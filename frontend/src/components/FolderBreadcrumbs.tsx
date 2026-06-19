import { useGalleryStore } from "../store/galleryStore";

const FolderBreadcrumbs = () => {
  const { folder, setFolder } = useGalleryStore();
  if (!folder) {
    return (
      <div className="breadcrumbs">
        <span>All folders</span>
      </div>
    );
  }

  const segments = folder.split("/");

  return (
    <div className="breadcrumbs">
      <button onClick={() => setFolder(null)}>All folders</button>
      {segments.map((segment, idx) => {
        const partial = segments.slice(0, idx + 1).join("/");
        return (
          <button key={partial} onClick={() => setFolder(partial)}>
            {segment}
          </button>
        );
      })}
    </div>
  );
};

export default FolderBreadcrumbs;

