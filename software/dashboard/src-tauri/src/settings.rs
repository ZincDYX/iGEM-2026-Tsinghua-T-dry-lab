use serde::{Deserialize, Serialize};
use std::{fs, path::Path};

#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    #[default]
    Local,
    Https,
    // Read old settings without activating the retired transport.
    Ssh,
}

#[derive(Default, Deserialize, Serialize)]
#[serde(default)]
pub struct DesktopSettings {
    pub mode: Mode,
    pub api_url: String,
    pub ca_file: String,
    protected_token: Vec<u8>,
}

#[derive(Serialize)]
pub struct SettingsView {
    pub mode: Mode,
    pub api_url: String,
    pub ca_file: String,
    pub has_access_token: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SettingsInput {
    pub mode: Mode,
    pub api_url: String,
    pub ca_file: String,
    // None keeps the saved token; empty explicitly removes it.
    pub access_token: Option<String>,
}

impl DesktopSettings {
    pub fn view(&self) -> SettingsView {
        SettingsView {
            mode: if self.mode == Mode::Ssh {
                Mode::Local
            } else {
                self.mode.clone()
            },
            api_url: self.api_url.clone(),
            ca_file: self.ca_file.clone(),
            has_access_token: !self.protected_token.is_empty(),
        }
    }
    pub fn validate(&self) -> Result<(), String> {
        if self.mode == Mode::Ssh {
            return Err("Choose local or HTTPS API mode".into());
        }
        if self.mode == Mode::Https {
            let url =
                tauri::Url::parse(&self.api_url).map_err(|_| "Enter a valid HTTPS API base URL")?;
            if url.scheme() != "https"
                || url.host_str().is_none()
                || !url.username().is_empty()
                || url.password().is_some()
                || url.query().is_some()
                || url.fragment().is_some()
            {
                return Err("Use HTTPS without URL credentials, query or fragment".into());
            }
            if self.protected_token.is_empty() {
                return Err("Provide an API access token".into());
            }
            if !self.ca_file.is_empty() && !Path::new(&self.ca_file).is_file() {
                return Err("Select an existing PEM CA certificate file or leave it blank".into());
            }
        }
        Ok(())
    }
    pub fn update(&mut self, input: SettingsInput) -> Result<(), String> {
        // A saved token belongs to one endpoint, not arbitrary new hosts/bases.
        if self.api_url.trim_end_matches('/') != input.api_url.trim().trim_end_matches('/') {
            self.protected_token.clear();
        }
        self.mode = input.mode;
        self.api_url = input.api_url.trim().trim_end_matches('/').into();
        self.ca_file = input.ca_file.trim().into();
        if let Some(token) = input.access_token {
            if !token.is_ascii() || token.chars().any(char::is_whitespace) {
                return Err("Access token must not contain whitespace".into());
            }
            self.protected_token = if token.is_empty() {
                vec![]
            } else {
                protect(token.as_bytes(), true)?
            };
        }
        self.validate()
    }
    pub fn access_token(&self) -> Result<String, String> {
        String::from_utf8(protect(&self.protected_token, false)?)
            .map_err(|_| "Saved token unavailable".into())
    }
    pub fn load(path: &Path) -> Result<Self, String> {
        if !path.exists() {
            return Ok(Self::default());
        }
        serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())
    }
    pub fn save(&self, path: &Path) -> Result<(), String> {
        self.validate()?;
        fs::write(
            path,
            serde_json::to_vec_pretty(self).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())
    }
}

#[cfg(windows)]
fn protect(data: &[u8], encrypt: bool) -> Result<Vec<u8>, String> {
    use std::{ptr, slice};
    use windows_sys::Win32::{Foundation::LocalFree, Security::Cryptography::*};
    let input = CRYPT_INTEGER_BLOB {
        cbData: data.len() as u32,
        pbData: data.as_ptr() as *mut u8,
    };
    let mut output = CRYPT_INTEGER_BLOB {
        cbData: 0,
        pbData: ptr::null_mut(),
    };
    unsafe {
        let success = if encrypt {
            CryptProtectData(
                &input,
                ptr::null(),
                ptr::null(),
                ptr::null(),
                ptr::null(),
                CRYPTPROTECT_UI_FORBIDDEN,
                &mut output,
            )
        } else {
            CryptUnprotectData(
                &input,
                ptr::null_mut(),
                ptr::null(),
                ptr::null(),
                ptr::null(),
                CRYPTPROTECT_UI_FORBIDDEN,
                &mut output,
            )
        };
        if success == 0 {
            return Err("Windows user credential protection failed".into());
        }
        let result = slice::from_raw_parts(output.pbData, output.cbData as usize).to_vec();
        LocalFree(output.pbData as *mut _);
        Ok(result)
    }
}
#[cfg(not(windows))]
fn protect(_: &[u8], _: bool) -> Result<Vec<u8>, String> {
    Err("Private token storage is currently supported by the Windows desktop".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn input(url: &str, token: Option<&str>) -> SettingsInput {
        SettingsInput {
            mode: Mode::Https,
            api_url: url.into(),
            ca_file: String::new(),
            access_token: token.map(str::to_owned),
        }
    }
    #[test]
    fn local_default_and_legacy_recovery() {
        let settings = DesktopSettings::default();
        assert_eq!(settings.mode, Mode::Local);
        assert!(settings.api_url.is_empty() && !settings.view().has_access_token);
        let legacy: DesktopSettings = serde_json::from_str(
            r#"{"mode":"ssh","ssh_host":"private-old-alias","remote_port":8780}"#,
        )
        .unwrap();
        assert_eq!(legacy.view().mode, Mode::Local);
        assert!(legacy.validate().is_err());
    }
    #[test]
    #[cfg(windows)]
    fn encrypted_roundtrip_without_token_getter_or_host_reuse() {
        let mut settings = DesktopSettings::default();
        settings
            .update(input(
                "https://example.invalid/fusion",
                Some("TEST_ONLY_ACCESS"),
            ))
            .unwrap();
        assert_eq!(settings.access_token().unwrap(), "TEST_ONLY_ACCESS");
        assert!(!serde_json::to_string(&settings)
            .unwrap()
            .contains("TEST_ONLY_ACCESS"));
        assert!(!serde_json::to_string(&settings.view())
            .unwrap()
            .contains("protected_token"));
        settings
            .update(input("https://example.invalid/fusion/", None))
            .unwrap();
        assert!(settings
            .update(input("https://another.invalid", None))
            .is_err());
    }
    #[test]
    #[cfg(windows)]
    fn rejects_insecure_urls_and_removed_token() {
        for url in [
            "http://example.invalid",
            "https://user:pass@example.invalid",
            "https://example.invalid?key=x",
            "https://example.invalid#x",
        ] {
            assert!(DesktopSettings::default()
                .update(input(url, Some("TEST_ONLY_ACCESS")))
                .is_err());
        }
        let mut settings = DesktopSettings::default();
        settings
            .update(input("https://example.invalid", Some("TEST_ONLY_ACCESS")))
            .unwrap();
        assert!(settings
            .update(input("https://example.invalid", Some("")))
            .is_err());
    }
}
