import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchPainting } from "../api/paintings";

const DetailView = () => {
  const { id } = useParams();
  const { data, isLoading } = useQuery({
    queryKey: ["painting", id],
    queryFn: () => fetchPainting(id!),
    enabled: Boolean(id)
  });

  if (isLoading) {
    return <p>Loading painting...</p>;
  }

  if (!data) {
    return <p>Painting not found</p>;
  }

  return (
    <article className="detail-view">
      <header>
        <h1>{data.title || `Untitled #${data.id}`}</h1>
        <Link to={`/editor/${data.id}`}>Edit</Link>
      </header>
      <img src={data.image_url} alt={data.title} />
      <section className="detail-meta">
        <p>ID: {data.id}</p>
        <p>Folder: {data.folder || "Unfiled"}</p>
        <p>Tags: {data.tags || "—"}</p>
        <p>
          Dimensions: {data.width ?? "?"}×{data.height ?? "?"} ({data.format || "—"})
        </p>
        <p>Updated: {new Date(data.updated_at).toLocaleString()}</p>
      </section>
    </article>
  );
};

export default DetailView;

