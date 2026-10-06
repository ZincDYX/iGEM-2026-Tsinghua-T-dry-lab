import { useEffect, useState } from "react";
import * as api from "./api";

export function DesktopConnectionPanel() {
  const [settings, setSettings] = useState<api.DesktopSettings>();
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    if (api.isDesktop()) api.getDesktopSettings().then(value => { if (active) setSettings(value); })
      .catch(error => { if (active) setMessage(String(error)); });
    return () => { active = false; };
  }, []);
  if (!api.isDesktop()) return null;
  return <section aria-label="桌面计算位置"><h3>桌面计算位置（下次启动生效）</h3>
    {settings && <><label>计算模式<select aria-label="计算模式" value={settings.mode}
      onChange={event => setSettings({...settings, mode:event.target.value as "local" | "ssh"})}>
      <option value="local">本地计算（默认）</option><option value="ssh">可选远程服务器（SSH）</option></select></label>
      {settings.mode === "ssh" && <><label>用户 SSH 别名<input aria-label="用户 SSH 别名" value={settings.ssh_host}
        placeholder="用户自行配置的 SSH 别名" onChange={event => setSettings({...settings, ssh_host:event.target.value})} /></label>
        <label>远程后台端口<input aria-label="远程后台端口" type="number" min="1" max="65535" value={settings.remote_port}
          onChange={event => setSettings({...settings, remote_port:Number(event.target.value)})} /></label>
        <p>使用系统 OpenSSH 和已有 known_hosts/认证配置；不复制私钥，不自动信任新主机。远程后台须已运行。</p></>}
      <button onClick={async () => { try { await api.saveDesktopSettings(settings); setMessage("连接设置已保存。关闭并重新打开软件后生效；当前连接没有改变。"); }
        catch(error) { setMessage(String(error)); } }}>保存连接设置</button></>}
    <p role="status">{message}</p><p>设置仅存于本机用户数据目录，不进入项目仓库。默认模式不启动 SSH。</p>
  </section>;
}
