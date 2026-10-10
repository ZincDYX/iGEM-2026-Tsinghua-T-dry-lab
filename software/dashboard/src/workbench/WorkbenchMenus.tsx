import { useEffect, useRef, useState } from 'react';
type Command = { label: string; action: () => void; disabled?: boolean };
export function WorkbenchMenus({
  file,
  view,
  tools,
  help,
}: {
  file: Command[];
  view: Command[];
  tools: Command[];
  help: Command[];
}) {
  const [openMenu,setOpenMenu]=useState<string|null>(null);
  const root=useRef<HTMLElement>(null);
  useEffect(()=>{
    function outside(event: PointerEvent) { if (!root.current?.contains(event.target as Node)) setOpenMenu(null); }
    window.addEventListener('pointerdown',outside);
    return ()=>window.removeEventListener('pointerdown',outside);
  },[]);
  return (
    <nav ref={root} aria-label="Workbench menus" onKeyDown={event=>{
      if (event.key==='Escape') {
        root.current?.querySelector<HTMLDetailsElement>('details[open]')?.querySelector('summary')?.focus();
        setOpenMenu(null);event.preventDefault();
      }
    }}>
      {Object.entries({ File: file, View: view, Tools: tools, Help: help }).map(
        ([name, commands]) => (
          <details className="workbench-menu" key={name} open={openMenu===name}>
            <summary aria-expanded={openMenu===name} onClick={event=>{
              event.preventDefault();setOpenMenu(current=>current===name?null:name);
            }} onKeyDown={event=>{
              if (event.key==='ArrowDown') {
                event.preventDefault();setOpenMenu(name);
                const details=event.currentTarget.closest('details');
                requestAnimationFrame(()=>details?.querySelector<HTMLButtonElement>('button:not(:disabled)')?.focus());
              }
            }}>{name}</summary>
            <div role="menu" aria-label={name}>
              {commands.map((command) => (
                <button
                  role="menuitem"
                  key={command.label}
                  disabled={command.disabled}
                  onClick={() => {
                    try { command.action(); } finally { setOpenMenu(null); }
                  }}
                >
                  {command.label}
                </button>
              ))}
            </div>
          </details>
        ),
      )}
    </nav>
  );
}
