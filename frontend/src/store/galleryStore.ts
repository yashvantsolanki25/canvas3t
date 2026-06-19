import { create } from "zustand";

type GalleryState = {
  search: string;
  folder: string | null;
  tag: string;
  format: string;
  setSearch: (value: string) => void;
  setFolder: (value: string | null) => void;
  setTag: (value: string) => void;
  setFormat: (value: string) => void;
};

export const useGalleryStore = create<GalleryState>((set) => ({
  search: "",
  folder: null,
  tag: "",
  format: "ALL",
  setSearch: (value) => set({ search: value }),
  setFolder: (value) => set({ folder: value }),
  setTag: (value) => set({ tag: value }),
  setFormat: (value) => set({ format: value })
}));

