import { Route, Routes, Navigate } from "react-router-dom";
import GalleryView from "./pages/GalleryView";
import EditorView from "./pages/EditorView";
import DetailView from "./pages/DetailView";
import AppShell from "./components/AppShell";

const App = () => {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/gallery" replace />} />
        <Route path="/gallery" element={<GalleryView />} />
        <Route path="/editor/:id?" element={<EditorView />} />
        <Route path="/paintings/:id" element={<DetailView />} />
      </Routes>
    </AppShell>
  );
};

export default App;

