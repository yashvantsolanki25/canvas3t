import { Link } from "react-router-dom";
import type { Painting } from "../api/paintings";

type Props = {
  paintings: Painting[];
};

const GalleryGrid = ({ paintings }: Props) => {
  if (!paintings || paintings.length === 0) {
    return <p>No paintings yet. Create one in the editor!</p>;
  }

  return (
    <div className="gallery-grid">
      {paintings.map((painting) => (
        <article key={painting.id} className="thumbnail-card">
          <Link to={`/paintings/${painting.id}`}>
            <img
              src={
                painting.thumbnail_url ||
                painting.image_url ||
                "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200'%3E%3Crect width='100%25' height='100%25' fill='%23e2e8f0'/%3E%3C/svg%3E"
              }
              alt={painting.title}
              loading="lazy"
            />
            <div className="thumbnail-card__meta">
              <h3>{painting.title || `Untitled #${painting.id}`}</h3>
              <p className="artist">by {painting.username || 'Anonymous'}</p>
              <p>{new Date(painting.created_at).toLocaleString()}</p>
              <div className="badges">
                {painting.format && <span className="badge subtle">{painting.format}</span>}
                <span className={`badge ${painting.is_public ? 'public' : 'private'}`}>
                  {painting.is_public ? '🌐 Public' : '🔒 Private'}
                </span>
              </div>
              {painting.tags && (
                <p className="thumbnail-card__tags">
                  {String(painting.tags)
                    .split(",")
                    .map((tag) => tag.trim())
                    .filter(Boolean)
                    .map((tag) => `#${tag}`)
                    .join(" ")}
                </p>
              )}
            </div>
          </Link>
          <footer>
            <Link to={`/editor/${painting.id}`}>Edit</Link>
            {painting.image_url && (
              <a href={painting.image_url} download target="_blank" rel="noopener noreferrer">
                Download
              </a>
            )}
          </footer>
        </article>
      ))}
    </div>
  );
};

export default GalleryGrid;

