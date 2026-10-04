#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::{
    fs,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::Duration,
};
use tauri::Manager;

#[derive(Clone, Serialize)]
struct BackendInfo {
    url: String,
    token: String,
}

struct Backend {
    child: Mutex<Child>,
    info: BackendInfo,
    ready: PathBuf,
    #[cfg(windows)]
    _job: WindowsJob,
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
        let _ = fs::remove_file(&self.ready);
        // On Windows dropping the job handle also terminates plugin/MCP children.
    }
}

#[tauri::command]
fn backend_info(backend: tauri::State<'_, Backend>) -> BackendInfo {
    backend.info.clone()
}

fn launch(app: &tauri::App) -> Result<Backend, Box<dyn std::error::Error>> {
    let root = std::env::var_os("FUSIONLAB_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../..")
                .canonicalize()
                .expect("source repository root")
        });
    let python = std::env::var_os("FUSIONLAB_PYTHON")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
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
        .unwrap_or(app.path().app_data_dir()?);
    fs::create_dir_all(&data)?;
    let token = uuid::Uuid::new_v4().to_string();
    let ready = data.join(format!("backend-{}.json", uuid::Uuid::new_v4()));
    let mut command = Command::new(python);
    command
        .args(["-m", "igem_drylab.software.desktop_backend", "--data-dir"])
        .arg(&data)
        .arg("--ready-file")
        .arg(&ready)
        .env("FUSIONLAB_SESSION_TOKEN", &token)
        .current_dir(root)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::from(fs::File::create(data.join("backend.log"))?));
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
    let mut backend = Backend {
        child: Mutex::new(child),
        info: BackendInfo {
            url: String::new(),
            token,
        },
        ready,
        #[cfg(windows)]
        _job: job,
    };
    for _ in 0..200 {
        let ready = &backend.ready;
        if ready.is_file() {
            let content: serde_json::Value = serde_json::from_slice(&fs::read(&ready)?)?;
            let url = content["url"]
                .as_str()
                .ok_or("invalid backend ready message")?
                .to_owned();
            backend.info.url = url;
            return Ok(backend);
        }
        if backend
            .child
            .get_mut()
            .map_err(|_| "backend lock poisoned")?
            .try_wait()?
            .is_some()
        {
            return Err(format!(
                "Python backend exited; inspect {}",
                data.join("backend.log").display()
            )
            .into());
        }
        thread::sleep(Duration::from_millis(100));
    }
    Err("Python backend startup timed out; inspect backend.log".into())
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            app.manage(launch(app)?);
            if !std::env::args().any(|argument| argument == "--smoke-test") {
                app.get_webview_window("main")
                    .ok_or("main window missing")?
                    .show()?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![backend_info])
        .run(tauri::generate_context!())
        .expect("FusionLab desktop failed");
}
