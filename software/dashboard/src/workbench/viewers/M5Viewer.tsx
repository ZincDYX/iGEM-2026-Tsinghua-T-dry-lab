import { useEffect, useState } from "react";
import { requestJson } from "../../api";
import { parsePublic } from "../../contracts/validation";
import type { M5ComparisonSeries } from "../../contracts/generated";
import { M5View } from "../M5View";

export function M5Viewer({
  projectId,
  fileId,
}: {
  projectId: string;
  fileId: string;
}) {
  const [series, setSeries] = useState<M5ComparisonSeries>(),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setSeries(undefined);
    setError("");
    void requestJson(
      `/files/${encodeURIComponent(fileId)}/m5-comparison?project_id=${encodeURIComponent(projectId)}`,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        const result = parsePublic("M5ComparisonSeries", raw);
        if (!controller.signal.aborted) setSeries(result);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Recorded M5 alignment unavailable. No comparison regenerated.",
          );
      });
    return () => controller.abort();
  }, [projectId, fileId]);
  return (
    <section aria-label="Registered M5 alignment">
      <p>
        This artifact records an aligned observable, not a full M5 assessment.
        Observable identity, QC, fitting and biological validation are not
        inferred from its filename.
      </p>
      {error && <p role="alert">{error}</p>}
      {series && (
        <M5View
          record={{
            ...series,
            metabolite_comparisons: {
              "registered observable": { display_series: series },
            },
          }}
        />
      )}
    </section>
  );
}
