import api from "./client";

export type Painting = {
  id: number;
  user_id: number;
  title: string;
  tags?: string;
  folder?: string;
  thumbnail_url?: string;
  image_url?: string;
  width?: number;
  height?: number;
  format?: string;
  is_public?: boolean;
  description?: string;
  username?: string;
  painting?: Painting;
  created_at: string;
  updated_at: string;
};

export type PaginatedPaintings = {
  paintings: Painting[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
};

export const fetchPaintings = async (params: Record<string, unknown>) => {
  const { data } = await api.get<PaginatedPaintings>("/api/paintings", {
    params
  });
  return data;
};

export const fetchPainting = async (id: string) => {
  const { data } = await api.get<Painting>(`/api/paintings/${id}`);
  return data;
};

export const createPainting = async (payload: FormData) => {
  // Do NOT set Content-Type header; let axios/browser handle it with multipart boundary
  const { data } = await api.post<Painting>("/api/paintings", payload);
  return data;
};

export const updatePainting = async (id: string, payload: FormData | object) => {
  // Do NOT set Content-Type header for FormData; axios will handle it
  const { data } = await api.put<Painting>(`/api/paintings/${id}`, payload);
  return data;
};

export const importRemoteImage = async (payload: { image_url: string; format?: string }) => {
  // The backend will attempt to import AND save the image as a painting when possible.
  const { data } = await api.post<any>("/api/paintings/import-url", payload);
  return data;
};

