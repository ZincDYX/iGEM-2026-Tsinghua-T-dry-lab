import { useEffect, useRef, useState } from "react";
import type { ImportView, TablePage } from "../../contracts/generated";
import { parsePublic } from "../../contracts/validation";
import { requestJson } from "../../api";

export function TableViewer({
  projectId,
  fileId,
  revision,
  onRegistered,
}: {
  projectId: string;
  fileId: string;
  revision: number;
  onRegistered: (value: ImportView) => void;
}) {
  const [page, setPage] = useState<TablePage>();
  const [offset, setOffset] = useState(0),
    [error, setError] = useState("");
  const [time, setTime] = useState(""),
    [unit, setUnit] = useState(""),
    [source, setSource] = useState("");
  const [columns, setColumns] = useState<
    { key: string; species: string; compartment: string; unit: string }[]
  >([]);
  const [pending, setPending] = useState(false);
  const mappingRequest = useRef<AbortController | undefined>(undefined);
  const registered = useRef(onRegistered);
  registered.current = onRegistered;
  useEffect(() => () => mappingRequest.current?.abort(), []);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    void requestJson(
      `/files/${encodeURIComponent(fileId)}/table?project_id=${encodeURIComponent(projectId)}&offset=${offset}`,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        const value = parsePublic("TablePage", raw);
        if (
          value.identity.project_id !== projectId ||
          value.identity.file_id !== fileId
        )
          throw Error("Wrong table identity.");
        if (!controller.signal.aborted) setPage(value);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(String(e));
      });
    return () => controller.abort();
  }, [projectId, fileId, offset]);
  return (
    <section>
      {error && <p role="alert">{error}</p>}
      {page && (
        <>
          <p>
            Original strings, {Math.min(offset + 1, page.total)}–
            {Math.min(offset + 500, page.total)} / {page.total}{" "}
            {page.columns.length ? "rows" : "characters"}. No inferred
            scientific role.
          </p>
          {page.text !== null ? (
            <pre>{page.text}</pre>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Source row</th>
                    {page.columns.map((c) => (
                      <th key={c}>{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {page.rows.map((row, i) => (
                    <tr key={offset + i}>
                      <td>{offset + i + 1}</td>
                      {row.map((v, j) => (
                        <td key={j}>
                          {v === "" || v === null ? "Not recorded" : v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <button
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 500))}
          >
            Previous table page
          </button>
          <button
            disabled={!page.has_more}
            onClick={() => setOffset(offset + 500)}
          >
            Next table page
          </button>
          {!!page.columns.length && (
            <details>
              <summary>Declare time-course columns</summary>
              <p>
                Specify every meaning and unit yourself. Empty numeric cells
                remain gaps. Time must be recorded, finite and strictly
                increasing. This does not approve evidence.
              </p>
              <fieldset disabled={pending}>
                <label>
                  Time column
                  <select
                    aria-label="Time column"
                    value={time}
                    onChange={(e) => {
                      setTime(e.target.value);
                      setColumns((cs) =>
                        cs.filter((c) => c.key !== e.target.value),
                      );
                    }}
                  >
                    <option value="">Choose explicitly</option>
                    {page.columns.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Time unit
                  <input
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                  />
                </label>
                <label>
                  Source reference
                  <input
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                  />
                </label>
                {page.columns
                  .filter((c) => c !== time)
                  .map((key) => {
                    const column = columns.find((c) => c.key === key);
                    return (
                      <div key={key}>
                        <label>
                          <input
                            type="checkbox"
                            checked={!!column}
                            onChange={(e) =>
                              setColumns((cs) =>
                                e.target.checked
                                  ? [
                                      ...cs,
                                      {
                                        key,
                                        species: "",
                                        compartment: "",
                                        unit: "",
                                      },
                                    ]
                                  : cs.filter((c) => c.key !== key),
                              )
                            }
                          />
                          {key}
                        </label>
                        {column &&
                          (["species", "compartment", "unit"] as const).map(
                            (field) => (
                              <label key={field}>
                                {key} {field}
                                <input
                                  value={column[field]}
                                  onChange={(e) =>
                                    setColumns((cs) =>
                                      cs.map((c) =>
                                        c.key === key
                                          ? { ...c, [field]: e.target.value }
                                          : c,
                                      ),
                                    )
                                  }
                                />
                              </label>
                            ),
                          )}
                      </div>
                    );
                  })}
                <button
                  disabled={
                    !time ||
                    !unit.trim() ||
                    !source.trim() ||
                    !columns.length ||
                    columns.some(
                      (c) =>
                        !c.species.trim() ||
                        !c.compartment.trim() ||
                        !c.unit.trim(),
                    )
                  }
                  onClick={() => {
                    setPending(true);
                    setError("");
                    const controller = new AbortController();
                    mappingRequest.current = controller;
                    void requestJson(
                      "/imports/series-mapping",
                      {
                        project_id: projectId,
                        expected_revision: revision,
                        file_id: fileId,
                        source_reference: source,
                        time_key: time,
                        time_unit: unit,
                        columns,
                      },
                      controller.signal,
                    )
                      .then((raw) => {
                        if (!controller.signal.aborted)
                          registered.current(parsePublic("ImportView", raw));
                      })
                      .catch((e) => setError(String(e)))
                      .finally(() => setPending(false));
                  }}
                >
                  Register declared series
                </button>
              </fieldset>
            </details>
          )}
        </>
      )}
    </section>
  );
}
