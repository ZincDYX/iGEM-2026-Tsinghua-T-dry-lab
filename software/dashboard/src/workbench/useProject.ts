import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import type { ProjectView, ProjectSummaryView } from "../contracts/generated";
import * as client from "./client";

type State = {
  draft?: ProjectView;
  saved?: ProjectView;
  dirty: boolean;
  loading: boolean;
};
type Action =
  | { type: "load"; value?: ProjectView }
  | { type: "edit"; value: ProjectView }
  | { type: "saved"; value: ProjectView; unchanged: boolean }
  | { type: "loading" };
function reducer(state: State, action: Action): State {
  if (action.type === "loading") return { dirty: false, loading: true };
  if (action.type === "load")
    return {
      draft: action.value,
      saved: action.value,
      dirty: false,
      loading: false,
    };
  if (action.type === "edit")
    return {
      ...state,
      saved: state.saved?.id === action.value.id ? state.saved : undefined,
      draft: action.value,
      dirty: true,
      loading: false,
    };
  return {
    ...state,
    saved: action.value,
    draft: action.unchanged
      ? action.value
      : state.draft
        ? { ...state.draft, revision: action.value.revision }
        : undefined,
    dirty: !action.unchanged,
  };
}
export function newProject(): ProjectView {
  return {
    id: crypto.randomUUID(),
    name: "New fusion protein project",
    revision: 1,
    description: "",
    sequences: [],
    assemblies: [],
    conditions: {},
    pathway: null,
    files: [],
    datasets: [],
    scientific_project: null,
    runtime_profile_ref: null,
    parent_run_id: null,
    parent_snapshot_sha256: null,
  };
}
export function useProject(fail: (reason: unknown) => void) {
  const [state, dispatch] = useReducer(reducer, {
    dirty: false,
    loading: false,
  });
  const [summaries, setSummaries] = useState<ProjectSummaryView[]>([]);
  const generation = useRef(0);
  const stateRef = useRef(state);
  stateRef.current = state;
  const fetchController = useRef<AbortController | undefined>(undefined);
  const refresh = useCallback(async () => {
    setSummaries(await client.projectSummaries());
  }, []);
  const choose = useCallback(
    async (id: string) => {
      const stamp = ++generation.current;
      fetchController.current?.abort();
      const controller = new AbortController();
      fetchController.current = controller;
      dispatch({ type: "loading" });
      try {
        const value = await client.project(id, controller.signal);
        if (generation.current === stamp) {
          dispatch({ type: "load", value });
          localStorage.setItem("fusionlab.project", id);
        }
      } catch (reason) {
        if (!controller.signal.aborted) fail(reason);
      }
    },
    [fail],
  );
  useEffect(() => {
    const controller = new AbortController();
    const stamp = generation.current;
    client
      .projectSummaries(controller.signal)
      .then((values) => {
        if (controller.signal.aborted) return;
        setSummaries(values);
        const selected =
          values.find(
            (row) => row.id === localStorage.getItem("fusionlab.project"),
          ) ?? values[0];
        if (selected && generation.current === stamp) void choose(selected.id);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) fail(reason);
      });
    return () => {
      controller.abort();
      fetchController.current?.abort();
    };
  }, [choose, fail]);
  function edit(value: ProjectView) {
    ++generation.current;
    dispatch({ type: "edit", value });
  }
  function adopt(value: ProjectView) {
    ++generation.current;
    dispatch({ type: "load", value });
    localStorage.setItem("fusionlab.project", value.id);
    void refresh().catch(fail);
  }
  async function save() {
    const current = stateRef.current;
    if (!current.draft) return;
    const stamp = generation.current;
    const id = current.draft.id;
    if (!current.dirty && current.saved) return current.saved;
    const value = await client.save(current.draft, current.saved?.revision);
    if (stateRef.current.draft?.id === id)
      dispatch({
        type: "saved",
        value,
        unchanged: stamp === generation.current,
      });
    await refresh();
    if (stamp !== generation.current) return;
    localStorage.setItem("fusionlab.project", value.id);
    return value;
  }
  return {
    ...state,
    summaries,
    generation,
    choose,
    edit,
    adopt,
    save,
    new: () => edit(newProject()),
    refresh,
  };
}
