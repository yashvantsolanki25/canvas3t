import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import CanvasEditor from "../components/CanvasEditor";
import MetadataPanel from "../components/MetadataPanel";
import { fetchPainting } from "../api/paintings";

const EditorView = () => {
  const { id } = useParams();
  const { data } = useQuery({
    queryKey: ["painting", id],
    queryFn: () => fetchPainting(id!),
    enabled: Boolean(id)
  });

  return (
    <div className="editor-layout">
      <CanvasEditor painting={data} />
      <MetadataPanel painting={data} />
    </div>
  );
};

export default EditorView;

