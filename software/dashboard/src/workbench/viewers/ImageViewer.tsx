import { useEffect, useState } from "react";
import { requestBinary } from "../../api";

export function ImageViewer({
  fileId,
  projectId,
}: {
  fileId: string;
  projectId: string;
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const controller = new AbortController();
    let owned: string | undefined;
    setUrl("");
    setError("");
    setScale(1);
    void requestBinary(
      `/files/${encodeURIComponent(fileId)}/image-preview?project_id=${encodeURIComponent(projectId)}`,
      undefined,
      controller.signal,
    )
      .then((r) => r.blob())
      .then((blob) => {
        if (controller.signal.aborted) return;
        owned = URL.createObjectURL(blob);
        setUrl(owned);
      })
      .catch((reason) => {
        if (!controller.signal.aborted)
          setError(
            reason instanceof Error
              ? reason.message
              : "Image preview could not be decoded.",
          );
      });
    return () => {
      controller.abort();
      if (owned) URL.revokeObjectURL(owned);
    };
  }, [fileId, projectId]);
  return (
    <section>
      <p>
        Pixel-only preview. Original metadata and source bytes are sealed, not
        overwritten.
      </p>
      {error && <p role="alert">{error}</p>}
      <label>
        Zoom
        <input
          type="range"
          min="0.25"
          max="3"
          step="0.25"
          value={scale}
          onChange={(e) => setScale(Number(e.target.value))}
        />
      </label>
      <div style={{ overflow: "auto", maxHeight: 500 }}>
        {url && (
          <img
            alt="Authorized registered image preview"
            src={url}
            style={{
              maxWidth: "100%",
              transform: `scale(${scale})`,
              transformOrigin: "top left",
            }}
          />
        )}
      </div>
    </section>
  );
}
