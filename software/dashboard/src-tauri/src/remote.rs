//! Desktop-only transport. No Python or scientific job is launched here.
use std::{
    fs,
    io::{Read, Write},
    net::{SocketAddr, TcpListener, TcpStream},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    thread,
    time::{Duration, Instant},
};

fn hidden(command: &mut Command) -> &mut Command {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    command
}

// ssh -G resolves the user's alias/identities. Strip unrelated forwards and
// session commands rather than copying private keys or modifying ~/.ssh/config.
pub fn transport_config(resolved: &str) -> String {
    resolved
        .lines()
        .filter(|line| {
            let key = line.split_whitespace().next().unwrap_or("");
            !matches!(
                key,
                "host"
                    | "localforward"
                    | "remoteforward"
                    | "dynamicforward"
                    | "clearallforwardings"
                    | "remotecommand"
                    | "localcommand"
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
        + "\n"
}

fn probe(address: SocketAddr) -> Result<(), Box<dyn std::error::Error>> {
    let mut stream = TcpStream::connect_timeout(&address, Duration::from_secs(1))?;
    stream.set_read_timeout(Some(Duration::from_secs(2)))?;
    stream.set_write_timeout(Some(Duration::from_secs(2)))?;
    stream.write_all(
        b"GET /api/platform/info HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n",
    )?;
    let mut response = String::new();
    stream.take(64 * 1024).read_to_string(&mut response)?;
    let (header, body) = response
        .split_once("\r\n\r\n")
        .ok_or("invalid HTTP response")?;
    if header
        .lines()
        .next()
        .and_then(|line| line.split_whitespace().nth(1))
        != Some("200")
    {
        return Err("remote FusionLab API did not return HTTP 200".into());
    }
    let info: serde_json::Value = serde_json::from_str(body)?;
    if info["name"] != "FusionLab" || info["storage"] != "SQLite WAL" {
        return Err("forwarded service is not the FusionLab API".into());
    }
    Ok(())
}

pub fn launch(
    data: &Path,
    host: &str,
    remote_port: u16,
) -> Result<(Child, PathBuf, String), Box<dyn std::error::Error>> {
    let ssh = std::env::var_os("FUSIONLAB_SSH").unwrap_or_else(|| "ssh".into());
    let resolved = hidden(Command::new(&ssh).args([
        "-G",
        "-o",
        "ClearAllForwardings=yes",
        "-o",
        "PermitLocalCommand=no",
        host,
    ]))
    .stdin(Stdio::null())
    .output()?;
    if !resolved.status.success() {
        return Err(format!(
            "SSH alias {host} could not be resolved: {}",
            String::from_utf8_lossy(&resolved.stderr)
        )
        .into());
    }
    let config = data.join(format!("ssh-{}.conf", uuid::Uuid::new_v4()));
    fs::write(
        &config,
        transport_config(std::str::from_utf8(&resolved.stdout)?),
    )?;
    let address = TcpListener::bind("127.0.0.1:0")?.local_addr()?;
    let mut command = Command::new(&ssh);
    hidden(&mut command)
        .args(["-F"])
        .arg(&config)
        .args([
            "-N",
            "-T",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ServerAliveInterval=15",
            "-o",
            "ServerAliveCountMax=2",
            "-o",
            "ForkAfterAuthentication=no",
            "-o",
            "PermitLocalCommand=no",
            "-o",
            "ControlMaster=no",
            "-o",
            "ControlPath=none",
            "-o",
            "ControlPersist=no",
            "-L",
            &format!("{address}:127.0.0.1:{remote_port}"),
            host,
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::from(fs::File::create(data.join("ssh.log"))?));
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(error) => {
            let _ = fs::remove_file(&config);
            return Err(error.into());
        }
    };
    let start = Instant::now();
    let ready = loop {
        if child.try_wait()?.is_some() {
            break Err(format!(
                "SSH connection to {host} exited; inspect {}",
                data.join("ssh.log").display()
            ));
        }
        match probe(address) {
            Ok(()) => break Ok(()),
            Err(error) if start.elapsed() >= Duration::from_secs(20) => {
                break Err(format!(
                    "remote API not ready: {error}; inspect {}",
                    data.join("ssh.log").display()
                ));
            }
            Err(_) => thread::sleep(Duration::from_millis(200)),
        }
    };
    if let Err(error) = ready {
        let _ = child.kill();
        let _ = child.wait();
        let _ = fs::remove_file(&config);
        return Err(error.into());
    }
    Ok((child, config, format!("http://{address}")))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn resolved_alias_keeps_identity_but_removes_unrelated_forward_and_commands() {
        let config = transport_config("host research-example\nuser scientist\nhostname example.org\nidentityfile C:/keys/research\nremoteforward 9001 localhost:9002\nlocalforward 5173 localhost:5173\ndynamicforward 9000\nclearallforwardings yes\nremotecommand echo bad\nlocalcommand echo bad\n");
        assert_eq!(
            config,
            "user scientist\nhostname example.org\nidentityfile C:/keys/research\n"
        );
    }
    #[test]
    fn live_service_identity_is_checked_not_just_an_open_port() {
        for (status, body, accepted) in [
            (
                "200",
                r#"{"name":"FusionLab","storage":"SQLite WAL"}"#,
                true,
            ),
            (
                "200",
                r#"{"name":"unrelated","storage":"SQLite WAL"}"#,
                false,
            ),
            (
                "503",
                r#"{"name":"FusionLab","storage":"SQLite WAL"}"#,
                false,
            ),
        ] {
            let listener = TcpListener::bind("127.0.0.1:0").unwrap();
            let address = listener.local_addr().unwrap();
            let server = thread::spawn(move || {
                let (mut connection, _) = listener.accept().unwrap();
                let mut request = [0; 2048];
                connection.read(&mut request).unwrap();
                write!(
                    connection,
                    "HTTP/1.0 {status} OK\r\nContent-Length: {}\r\n\r\n{body}",
                    body.len()
                )
                .unwrap();
            });
            assert_eq!(probe(address).is_ok(), accepted);
            server.join().unwrap();
        }
    }
}
