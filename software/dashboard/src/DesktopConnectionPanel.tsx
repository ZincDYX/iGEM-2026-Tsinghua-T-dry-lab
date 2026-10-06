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
      <option value="local">本地计算（默认）</option><option value="ssh" disabled>远程（缺少受控认证会话，暂不支持）</option></select></label>
      <p>远程配置由维护者私下管理；应用认证尚未接入，当前不会启动 SSH 或发送匿名 API 请求。</p>
      <button onClick={async () => { try { await api.saveDesktopSettings(settings); setMessage("连接设置已保存。关闭并重新打开软件后生效；当前连接没有改变。"); }
        catch(error) { setMessage(String(error)); } }}>保存连接设置</button></>}
    <p role="status">{message}</p><p>设置仅存于本机用户数据目录，不进入项目仓库。默认模式不启动 SSH。</p>
  </section>;
}
