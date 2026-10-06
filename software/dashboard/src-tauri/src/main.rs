#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::{
    fs,
    io::{BufRead, BufReader},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{mpsc, Mutex},
    thread,
    time::Duration,
};
use tauri::Manager;
#[cfg(test)]
mod remote;
mod settings;
use settings::{DesktopSettings, Mode};

#[derive(Clone, Serialize)]
struct BackendInfo {
    url: String,
    token: String,
    mode: String,
}

struct Backend {
    child: Mutex<Child>,
    info: BackendInfo,
    cleanup_file: Option<PathBuf>,
    #[cfg(windows)]
    _job: WindowsJob,
}

struct Connection {
    backend: Result<Backend, String>,
    settings_path: PathBuf,
}

#[cfg(windows)]
struct WindowsJob(windows_sys::Win32::Foundation::HANDLE);
#[cfg(windows)]
unsafe impl Send for WindowsJob {}
#[cfg(windows)]
unsafe impl Sync for WindowsJob {}

#[cfg(windows)]
impl WindowsJob {
    fn attach(child: &Child) -> std::io::Result<Self> {
        use std::{mem, os::windows::io::AsRawHandle, ptr};
        use windows_sys::Win32::System::JobObjects::*;
        unsafe {
            let handle = CreateJobObjectW(ptr::null(), ptr::null());
            if handle.is_null() {
                return Err(std::io::Error::last_os_error());
            }
            let job = Self(handle);
            let mut limits: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = mem::zeroed();
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            if SetInformationJobObject(
                handle,
                JobObjectExtendedLimitInformation,
                &limits as *const _ as *const _,
                mem::size_of_val(&limits) as u32,
            ) == 0
                || AssignProcessToJobObject(handle, child.as_raw_handle()) == 0
            {
                return Err(std::io::Error::last_os_error());
            }
            Ok(job)
        }
    }
}
#[cfg(windows)]
impl Drop for WindowsJob {
    fn drop(&mut self) {
        unsafe {
            windows_sys::Win32::Foundation::CloseHandle(self.0);
        }
    }
}

impl Drop for Backend {
    fn drop(&mut self) {
        if let Ok(child) = self.child.get_mut() {
            let _ = child.kill();
            let _ = child.wait();
        }
        if let Some(path) = &self.cleanup_file {
            let _ = fs::remove_file(path);
        }
        // On Windows dropping the job handle also terminates plugin/MCP children.
    }
}

#[tauri::command]
fn backend_info(connection: tauri::State<'_, Connection>) -> Result<BackendInfo, String> {
    connection
        .backend
        .as_ref()
        .map(|backend| backend.info.clone())
        .map_err(Clone::clone)
}

#[tauri::command]
fn desktop_settings(connection: tauri::State<'_, Connection>) -> Result<DesktopSettings, String> {
    DesktopSettings::load(&connection.settings_path).map(|mut settings| {
        settings.ssh_host.clear();
        settings.remote_port = 8780;
        settings
    }).map_err(|_| "desktop_settings_unavailable".to_string())
}
#[tauri::command]
fn save_desktop_settings(
    connection: tauri::State<'_, Connection>,
    settings: DesktopSettings,
) -> Result<(), String> {
    if settings.mode == Mode::Ssh {
        return Err("remote_authenticated_session_unavailable".into());
    }
    let mut private = DesktopSettings::load(&connection.settings_path)
        .map_err(|_| "desktop_settings_unavailable")?;
    private.mode = Mode::Local;
    private.save(&connection.settings_path).map_err(|_| "desktop_settings_save_failed".into())
}

fn launch_local(app: &tauri::App) -> Result<Backend, Box<dyn std::error::Error>> {
    let root = std::env::var_os("FUSIONLAB_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            let portable = std::env::current_exe()
                .expect("executable path")
                .parent()
                .expect("executable directory")
                .join("resources");
            if portable.join("src/igem_drylab").is_dir() {
                return portable;
            }
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../..")
                .canonicalize()
                .expect("source repository root")
        });
    let python = std::env::var_os("FUSIONLAB_PYTHON")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            let portable = std::env::current_exe()
                .expect("executable path")
                .parent()
                .expect("executable directory")
                .join("python/python.exe");
            if cfg!(windows) && portable.is_file() {
                return portable;
            }
            root.join(if cfg!(windows) {
                ".venv/Scripts/python.exe"
            } else {
                ".venv/bin/python"
            })
        });
    if !python.is_file() {
        return Err(
            "Set FUSIONLAB_PYTHON to an environment with pip install -e '.[software]'".into(),
        );
    }
    let data = std::env::var_os("FUSIONLAB_DATA_DIR")
        .map(PathBuf::from)
        .unwrap_or(app.path().app_local_data_dir()?);
    fs::create_dir_all(&data)?;
    let token = uuid::Uuid::new_v4().to_string();
    let mut command = Command::new(python);
    command
        .args(["-B", "-m", "igem_drylab.software.desktop_backend", "--data-dir"])
        .arg(&data)
        .env("FUSIONLAB_SESSION_TOKEN", &token)
        .current_dir(root)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::from(fs::File::create(data.join("backend.log"))?));
    // Avoid BLAS oversubscription across the backend and MCP/plugin processes.
    // This is a runtime resource default, not a different scientific equation.
    for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"] {
        if std::env::var_os(key).is_none() {
            command.env(key, "1");
        }
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    }
    let mut child = command.spawn()?;
    #[cfg(windows)]
    let job = match WindowsJob::attach(&child) {
        Ok(job) => job,
        Err(error) => {
            let _ = child.kill();
            let _ = child.wait();
            return Err(error.into());
        }
    };
    let stdout = child.stdout.take().ok_or("Python startup pipe missing")?;
    let mut backend = Backend {
        child: Mutex::new(child),
        info: BackendInfo {
            url: String::new(),
            token,
            mode: "local".into(),
        },
        cleanup_file: None,
        #[cfg(windows)]
        _job: job,
    };
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        let mut line = String::new();
        let result = BufReader::new(stdout).read_line(&mut line).map(|_| line);
        let _ = sender.send(result);
    });
    let line = receiver.recv_timeout(Duration::from_secs(20)).map_err(|error| {
        format!("Python backend startup failed ({error}); inspect {}", data.join("backend.log").display())
    })??;
    let content: serde_json::Value = serde_json::from_str(&line).map_err(|error| {
        format!("Invalid Python startup message ({error}); inspect {}", data.join("backend.log").display())
    })?;
    backend.info.url = content["url"].as_str().ok_or("invalid backend ready message")?.to_owned();
    Ok(backend)
}

fn launch(
    app: &tauri::App,
    settings: &DesktopSettings,
) -> Result<Backend, Box<dyn std::error::Error>> {
    if settings.mode == Mode::Local {
        return launch_local(app);
    }
    // SSH transport alone is not API identity. Fail before creating any tunnel
    // until a maintained, restricted remote-session provider is configured.
    Err("remote_authenticated_session_unavailable".into())
}

fn main() {
    tauri::Builder::default()
        .on_window_event(|window, event| {
            // The hidden/test and visible workbench have the same lifecycle.
            // Do not leave a headless backend after its only UI is destroyed.
            if window.label() == "main" && matches!(event, tauri::WindowEvent::Destroyed) {
                window.app_handle().exit(0);
            }
        })
        .setup(|app| {
            // A failed connection still opens the app and exposes a useful error.
            let directory = std::env::var_os("FUSIONLAB_DATA_DIR")
                .map(PathBuf::from)
                .unwrap_or(app.path().app_local_data_dir()?);
            fs::create_dir_all(&directory)?;
            let settings_path = directory.join("desktop-settings.json");
            let backend = DesktopSettings::load(&settings_path)
                .and_then(|settings| launch(app, &settings).map_err(|error| error.to_string()))
                .map_err(|error| {
                    let id = uuid::Uuid::new_v4();
                    let _ = fs::write(directory.join(format!("private-diagnostic-{id}.log")), error);
                    format!("desktop_backend_startup_failed:{id}")
                });
            app.manage(Connection {
                backend,
                settings_path,
            });
            if !std::env::args().any(|argument| argument == "--smoke-test") {
                app.get_webview_window("main")
                    .ok_or("main window missing")?
                    .show()?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            backend_info,
            desktop_settings,
            save_desktop_settings
        ])
        .run(tauri::generate_context!())
        .expect("FusionLab desktop failed");
}
