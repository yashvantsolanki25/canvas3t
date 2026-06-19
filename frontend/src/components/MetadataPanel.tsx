import { useEffect, useState } from "react";
import type { Painting } from "../api/paintings";
import { createPainting, updatePainting } from "../api/paintings";
import { useAuthStore } from "../store/authStore";

type Props = {
  painting?: Painting;
};

const MetadataPanel = ({ painting }: Props) => {
  const [title, setTitle] = useState(painting?.title ?? "");
  const [folder, setFolder] = useState(painting?.folder ?? "");
  const [tags, setTags] = useState(painting?.tags ?? "");
  const [isPublic, setIsPublic] = useState(painting?.is_public ?? false);
  const [format, setFormat] = useState(painting?.format ?? "PNG");
  const [status, setStatus] = useState<string | null>(null);
  const [lastSaved, setLastSaved] = useState<string | null>(null);
  const { user } = useAuthStore();

  useEffect(() => {
    setTitle(painting?.title ?? "");
    setFolder(painting?.folder ?? "");
    setTags(painting?.tags ?? "");
    setIsPublic(painting?.is_public ?? false);
    setFormat(painting?.format ?? "PNG");
  }, [painting]);

  const save = async () => {
    const canvas = document.querySelector("canvas");
    if (!canvas) {
      setStatus("No canvas found");
      return;
    }
    
    if (!user) {
      setStatus("Must be logged in to save");
      return;
    }

    setStatus("Saving...");
    const mime =
      format === "JPEG" ? "image/jpeg" : format === "WEBP" ? "image/webp" : "image/png";
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((result) => resolve(result), mime)
    );

    if (!blob) {
      setStatus("Failed to capture canvas");
      return;
    }

    const data = new FormData();
    data.append("title", title || "Untitled");
    data.append("folder", folder);
    data.append("tags", tags);
    data.append("is_public", String(isPublic));
    data.append("format", format);
    const extension = format === "JPEG" ? "jpg" : format.toLowerCase();
    data.append("image", blob, `${title || "untitled"}.${extension}`);

    try {
      if (painting) {
        await updatePainting(String(painting.id), data);
        setStatus("Updated successfully");
      } else {
        const result = await createPainting(data);
        // Backend returns { message, painting }
        const saved = result?.painting ?? result;
        setStatus("Saved successfully");
        console.log("Painting saved:", saved);
        // Notify other parts of the app that a painting was saved
        try {
          window.dispatchEvent(new CustomEvent('paintingSaved', { detail: saved }));
        } catch {}
      }
      const timestamp = new Date().toLocaleTimeString();
      setLastSaved(timestamp);
      setStatus(`Saved at ${timestamp}`);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      setStatus(`Save failed: ${errorMsg}`);
      console.error("Save error:", error);
    }
  };

  return (
    <aside className="metadata-panel">
      <h2>Metadata</h2>
      <label>
        Title
        <input value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label>
        Folder
        <input
          value={folder}
          onChange={(event) => setFolder(event.target.value)}
        />
      </label>
      <label>
        Tags
        <input value={tags} onChange={(event) => setTags(event.target.value)} />
      </label>
      <label>
        Format
        <select value={format} onChange={(event) => setFormat(event.target.value)}>
          <option value="PNG">PNG</option>
          <option value="JPEG">JPEG</option>
          <option value="WEBP">WEBP</option>
        </select>
      </label>
      <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <input
          type="checkbox"
          checked={isPublic}
          onChange={(event) => setIsPublic(event.target.checked)}
        />
        Public (others can see)
      </label>
      {painting?.width && painting?.height && (
        <p className="metadata-panel__info">
          {painting.width} × {painting.height} — {painting.format}
        </p>
      )}
      <button onClick={save} disabled={!user}>
        {!user ? "Login to save" : "Save painting"}
      </button>
      {status && <p className="status">{status}</p>}
      {lastSaved && <p className="metadata-panel__info">Last saved {lastSaved}</p>}
    </aside>
  );
};

export default MetadataPanel;

