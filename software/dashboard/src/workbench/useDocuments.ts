import { useCallback, useEffect, useState } from "react";

export type DocumentId = "plan" | "inputs" | "results" | "compare" | "settings" | "plugins" | "tools" | "artifacts";
const valid: DocumentId[] = ["plan", "inputs", "results", "compare", "settings", "plugins", "tools", "artifacts"];
type State = { active: DocumentId; open: DocumentId[] };
const initial: State = { active: "inputs", open: ["inputs"] };

function restore(key: string): State {
  try {
    const raw = JSON.parse(localStorage.getItem(key) ?? "null");
    if (raw && Array.isArray(raw.open) && raw.open.length &&
        raw.open.every((id: DocumentId) => valid.includes(id)) && raw.open.includes(raw.active))
      return { active: raw.active, open: [...new Set<DocumentId>(raw.open)] };
  } catch { /* Invalid UI preferences are not scientific data. */ }
  return initial;
}

export function useDocuments(workspace: string, dirty: boolean, onBlockedClose: () => void) {
  const key = `fusionlab.documents.${workspace}`;
  const [state, setState] = useState<State & { key: string }>(() => ({ ...restore(key), key }));
  useEffect(() => { setState(current => current.key === key ? current : { ...restore(key), key }); }, [key]);
  useEffect(() => { if (state.key === key) localStorage.setItem(key, JSON.stringify(state)); }, [key, state]);
  const activate = useCallback((active: DocumentId) => setState(current => ({
    ...current, active, open: current.open.includes(active) ? current.open : [...current.open, active],
  })), []);
  function close(id: DocumentId) {
    if (id === "inputs" && dirty) { onBlockedClose(); return; }
    setState(current => {
      const open = current.open.filter(value => value !== id);
      if (!open.length) open.push("inputs");
      return { ...current, open, active: current.active === id ? open[0] : current.active };
    });
  }
  return { tab: state.active, setTab: activate, openDocuments: state.open, closeDocument: close };
}
