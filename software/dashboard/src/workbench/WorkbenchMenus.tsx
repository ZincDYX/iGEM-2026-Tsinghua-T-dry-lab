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
  return (
    <nav aria-label="Workbench menus">
      {Object.entries({ File: file, View: view, Tools: tools, Help: help }).map(
        ([name, commands]) => (
          <details className="workbench-menu" key={name}>
            <summary>{name}</summary>
            <div role="menu" aria-label={name}>
              {commands.map((command) => (
                <button
                  role="menuitem"
                  key={command.label}
                  disabled={command.disabled}
                  onClick={(e) => {
                    command.action();
                    e.currentTarget.closest("details")?.removeAttribute("open");
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
