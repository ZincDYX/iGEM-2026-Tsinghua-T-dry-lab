fn main() {
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(
        tauri_build::AppManifest::new().commands(&[
            "backend_info",
            "desktop_settings",
            "save_desktop_settings",
        ]),
    ))
    .expect("desktop permission manifest");
}
