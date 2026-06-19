import { useGalleryStore } from "../store/galleryStore";

const formats = ["ALL", "PNG", "JPEG", "WEBP"];

const GalleryFilters = () => {
  const { tag, format, setTag, setFormat } = useGalleryStore();

  return (
    <div className="gallery-filters">
      <label>
        Format
        <select value={format} onChange={(event) => setFormat(event.target.value)}>
          {formats.map((option) => (
            <option key={option} value={option}>
              {option === "ALL" ? "Any" : option}
            </option>
          ))}
        </select>
      </label>
      <label>
        Tag
        <input
          placeholder="e.g. landscape"
          value={tag}
          onChange={(event) => setTag(event.target.value)}
        />
      </label>
    </div>
  );
};

export default GalleryFilters;

