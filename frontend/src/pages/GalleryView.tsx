import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { fetchPaintings } from "../api/paintings";
import { useGalleryStore } from "../store/galleryStore";
import GalleryGrid from "../components/GalleryGrid";
import FolderBreadcrumbs from "../components/FolderBreadcrumbs";
import GalleryFilters from "../components/GalleryFilters";
import { useAuthStore } from "../store/authStore";
import { useState } from "react";

const GalleryView = () => {
  const { search, folder, tag, format } = useGalleryStore();
  const { user } = useAuthStore();
  const [viewMode, setViewMode] = useState<'public' | 'mine'>(user ? 'mine' : 'public');

  // Determine user_id only when viewing "mine" and user is present
  const userId = viewMode === 'mine' && user ? user.id : undefined;

  const { data, isLoading } = useQuery({
    queryKey: ["paintings", search, folder, tag, format, viewMode, userId],
    queryFn: () =>
      fetchPaintings({
        q: search,
        folder,
        tag: tag || undefined,
        format: format === "ALL" ? undefined : format,
        ...(userId ? { user_id: userId } : {})
      })
  });

  const queryClient = useQueryClient();

  // Refresh gallery when a new painting is saved elsewhere in the app
  useEffect(() => {
    const handler = () => {
      queryClient.invalidateQueries({ queryKey: ["paintings"] });
    };
    window.addEventListener("paintingSaved", handler as EventListener);
    return () => window.removeEventListener("paintingSaved", handler as EventListener);
  }, [queryClient]);

  return (
    <section>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button onClick={() => setViewMode('public')} disabled={viewMode === 'public'}>
          Public Gallery
        </button>
        {user && (
          <button onClick={() => setViewMode('mine')} disabled={viewMode === 'mine'}>
            My Gallery
          </button>
        )}
      </div>
      <FolderBreadcrumbs />
      <GalleryFilters />
      {isLoading && <p>Loading paintings...</p>}
      {data && <GalleryGrid paintings={data.paintings} />}
    </section>
  );
};

export default GalleryView;

