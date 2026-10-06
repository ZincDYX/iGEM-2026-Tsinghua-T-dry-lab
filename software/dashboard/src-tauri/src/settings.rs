use serde::{Deserialize, Serialize};
use std::{fs, path::Path};

#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    #[default]
    Local,
    Ssh,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct DesktopSettings {
    pub mode: Mode,
    pub ssh_host: String,
    pub remote_port: u16,
}
impl Default for DesktopSettings {
    fn default() -> Self {
        Self {
            mode: Mode::Local,
            ssh_host: String::new(),
            remote_port: 8780,
        }
    }
}
impl DesktopSettings {
    pub fn validate(&self) -> Result<(), String> {
        if self.mode == Mode::Ssh
            && (self.ssh_host.trim().is_empty()
                || self.ssh_host.starts_with('-')
                || self.ssh_host.chars().any(char::is_whitespace))
        {
            return Err("请选择有效的用户 SSH 别名；没有内置远程服务器".into());
        }
        if self.remote_port == 0 {
            return Err("远程 API 端口不能为 0".into());
        }
        Ok(())
    }
    pub fn load(path: &Path) -> Result<Self, String> {
        let settings = if path.exists() {
            serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?
        } else {
            Self::default()
        };
        settings.validate()?;
        Ok(settings)
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
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn default_is_local_with_no_server() {
        let settings = DesktopSettings::default();
        assert_eq!(settings.mode, Mode::Local);
        assert!(settings.ssh_host.is_empty());
    }
    #[test]
    fn remote_requires_explicit_alias_and_port() {
        let mut settings = DesktopSettings {
            mode: Mode::Ssh,
            ..Default::default()
        };
        assert!(settings.validate().is_err());
        settings.ssh_host = "my-research-host".into();
        assert!(settings.validate().is_ok());
        settings.remote_port = 0;
        assert!(settings.validate().is_err());
    }
}
