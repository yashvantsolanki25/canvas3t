import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Painting } from "../api/paintings";
import { useWasmTools } from "../hooks/useWasmTools";
import { importRemoteImage } from "../api/paintings";
import { createPainting } from "../api/paintings";

type Props = {
  painting?: Painting;
};

const DEFAULT_WIDTH = 1024;
const DEFAULT_HEIGHT = 768;

const CanvasEditor = ({ painting }: Props) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);
  const engineRef = useRef<any | null>(null);

  const [isDrawing, setIsDrawing] = useState(false);
  const [color, setColor] = useState("#ff5c5c");
  const [brushSize, setBrushSize] = useState(24);
  const [opacity, setOpacity] = useState(0.85);
  const [softness, setSoftness] = useState(0.5);
  const [isEraser, setIsEraser] = useState(false);
  const [importUrl, setImportUrl] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [fillMode, setFillMode] = useState(false);

  const [tool, setTool] = useState<'brush' | 'rect' | 'ellipse' | 'line' | 'text'>('brush');
  const shapeStart = useRef<{ x: number; y: number } | null>(null);
  const [textValue, setTextValue] = useState('');

  const { bindings, error } = useWasmTools();

  const render = useCallback(() => {
    if (!bindings || !engineRef.current || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;
    const pixels = engineRef.current.export_pixels();
    const width = engineRef.current.width();
    const height = engineRef.current.height();
    const data = new ImageData(new Uint8ClampedArray(pixels), width, height);
    canvasRef.current.width = width;
    canvasRef.current.height = height;
    ctx.putImageData(data, 0, 0);
  }, [bindings]);

  const mergeOverlayToEngine = useCallback(
    (overlayCanvas: HTMLCanvasElement) => {
      if (!engineRef.current) return;
      const width = engineRef.current.width();
      const height = engineRef.current.height();
      const ctx = overlayCanvas.getContext('2d');
      if (!ctx) return;
      // Get existing engine pixels
      const pixels = engineRef.current.export_pixels();
      const existing = new ImageData(new Uint8ClampedArray(pixels), width, height);
      const temp = document.createElement('canvas');
      temp.width = width;
      temp.height = height;
      const tctx = temp.getContext('2d');
      if (!tctx) return;
      tctx.putImageData(existing, 0, 0);
      // Draw overlay onto temp
      tctx.drawImage(overlayCanvas, 0, 0, width, height);
      const merged = tctx.getImageData(0, 0, width, height);
      engineRef.current.load_pixels(new Uint8Array(merged.data.buffer), merged.width, merged.height);
      render();
    },
    [render]
  );

  useEffect(() => {
    if (!bindings) return;
    engineRef.current = new bindings.CanvasEngine(DEFAULT_WIDTH, DEFAULT_HEIGHT);
    render();
  }, [bindings, render]);

  const loadImage = useCallback(
    async (src: string) => {
      if (!bindings || !engineRef.current) return;
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.src = src;
      await img.decode();
      const temp = document.createElement("canvas");
      temp.width = img.width;
      temp.height = img.height;
      const ctx = temp.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);
      const data = ctx.getImageData(0, 0, img.width, img.height);
      engineRef.current.load_pixels(new Uint8Array(data.data), data.width, data.height);
      render();
    },
    [bindings, render]
  );

  useEffect(() => {
    if (painting?.image_url) {
      loadImage(painting.image_url);
    }
  }, [painting, loadImage]);

  const pointerPosition = (event: { clientX: number; clientY: number }) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect || !canvasRef.current) return { x: 0, y: 0 };
    // Scale to canvas logical size (not display size) to fix DPI/scaling
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    return {
      x: Math.floor((event.clientX - rect.left) * scaleX),
      y: Math.floor((event.clientY - rect.top) * scaleY)
    };
  };

  const handlePointerDown = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!bindings || !engineRef.current) return;
    const { x, y } = pointerPosition(event);
    if (fillMode) {
      floodFillAt(x, y);
      setIsDrawing(false);
      return;
    }
    if (tool === 'brush') {
      setIsDrawing(true);
      lastPoint.current = { x, y };
      drawStroke(x, y);
    } else if (tool === 'text') {
      // insert text at point
      const overlay = document.createElement('canvas');
      overlay.width = engineRef.current.width();
      overlay.height = engineRef.current.height();
      const ctx = overlay.getContext('2d');
      if (ctx) {
        ctx.fillStyle = color;
        ctx.font = `${brushSize * 2}px sans-serif`;
        ctx.fillText(textValue || 'Text', x, y);
        mergeOverlayToEngine(overlay);
      }
    } else {
      // start shape
      shapeStart.current = { x, y };
      setIsDrawing(true);
    }
  };

  const handlePointerUp = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    // finalize shape if any
    if (tool !== 'brush' && shapeStart.current && engineRef.current) {
      const start = shapeStart.current;
      const end = lastPoint.current ?? start;
      const overlay = document.createElement('canvas');
      overlay.width = engineRef.current.width();
      overlay.height = engineRef.current.height();
      const ctx = overlay.getContext('2d');
      if (ctx) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        const w = (end.x ?? start.x) - start.x;
        const h = (end.y ?? start.y) - start.y;
        if (tool === 'rect') ctx.fillRect(start.x, start.y, w, h);
        if (tool === 'line') {
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x ?? start.x, end.y ?? start.y);
          ctx.lineWidth = Math.max(1, brushSize / 4);
          ctx.stroke();
        }
        if (tool === 'ellipse') {
          ctx.beginPath();
          ctx.ellipse(start.x + w / 2, start.y + h / 2, Math.abs(w / 2), Math.abs(h / 2), 0, 0, Math.PI * 2);
          ctx.fill();
        }
        mergeOverlayToEngine(overlay);
      }
      shapeStart.current = null;
    }
    lastPoint.current = null;
  };

  const drawStroke = (x: number, y: number) => {
    if (!bindings || !engineRef.current) return;
    const start = lastPoint.current ?? { x, y };
    const rgb = hexToRgb(color);
    const brush = new bindings.BrushOptions(
      brushSize,
      softness,
      opacity,
      rgb.r,
      rgb.g,
      rgb.b
    );
    engineRef.current.apply_brush(start.x, start.y, x, y, brush, isEraser);
    lastPoint.current = { x, y };
    render();
  };

  const handlePointerMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const { x, y } = pointerPosition(event);
    if (tool === 'brush') {
      drawStroke(x, y);
    } else {
      // update last point for shape end position
      lastPoint.current = { x, y };
    }
  };

  const touchPoint = (event: React.TouchEvent<HTMLCanvasElement>) => {
    const touch = event.touches[0] || event.changedTouches[0];
    return touch ? pointerPosition(touch) : { x: 0, y: 0 };
  };

  const handleTouchStart = (event: React.TouchEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    if (!bindings || !engineRef.current) return;
    const { x, y } = touchPoint(event);
    if (fillMode) {
      floodFillAt(x, y);
      return;
    }
    setIsDrawing(true);
    lastPoint.current = { x, y };
    drawStroke(x, y);
  };

  const handleTouchMove = (event: React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    event.preventDefault();
    const { x, y } = touchPoint(event);
    drawStroke(x, y);
  };

  const handleTouchEnd = (event: React.TouchEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    setIsDrawing(false);
    lastPoint.current = null;
  };

  const applyFilter = (type: number, amount = 0.8) => {
    if (!bindings || !engineRef.current) return;
    engineRef.current.apply_filter(type, amount);
    render();
  };

  const undo = () => {
    if (engineRef.current?.undo()) {
      render();
    }
  };

  const redo = () => {
    if (engineRef.current?.redo()) {
      render();
    }
  };

  const floodFillAt = (x: number, y: number) => {
    if (!bindings || !engineRef.current) return;
    const rgb = hexToRgb(color);
    const brush = new bindings.BrushOptions(brushSize, softness, opacity, rgb.r, rgb.g, rgb.b);
    engineRef.current.flood_fill(Math.floor(x), Math.floor(y), brush);
    render();
  };

  const handleImportUrl = async () => {
    if (!importUrl.trim()) return;
    setStatus("Importing image...");
    setIsImporting(true);
    try {
      const data = await importRemoteImage({ image_url: importUrl });
      // Backend may return a saved painting (with image_url) or just metadata with data_url
      const src = data?.painting?.image_url ?? data?.data_url ?? importUrl;
      // If it's a relative URL (starts with /), load via the frontend base
      const fullSrc = src.startsWith('/') ? src : src;
      await loadImage(fullSrc);
      setStatus("Image imported");
      setIsImporting(false);
    } catch (err) {
      console.error(err);
      // Server-side import failed — fallback to browser fetch + upload
      setStatus("Server import failed, trying browser upload...");
      try {
        const resp = await fetch(importUrl, { mode: 'cors' });
        if (!resp.ok) throw new Error(`Fetch failed: ${resp.status}`);
        const blob = await resp.blob();
        // Create FormData and upload using createPainting
        const form = new FormData();
        const title = importUrl.split('/').pop() || 'imported';
        const extension = (blob.type && blob.type.split('/')[1]) || 'png';
        form.append('title', title || 'Imported');
        form.append('folder', 'imports');
        form.append('tags', 'imported');
        form.append('is_public', 'false');
        form.append('format', extension.toUpperCase());
        form.append('image', blob, `${title}.${extension}`);
        const result = await createPainting(form);
        const saved = result?.painting ?? result;
        const src = saved?.image_url ?? importUrl;
        await loadImage(src);
        setStatus('Imported and saved');
      } catch (err2) {
        console.error(err2);
        setStatus('Import failed');
      } finally {
        setIsImporting(false);
      }
    }
  };

  const handleLocalImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setStatus("Importing image...");
    const url = URL.createObjectURL(file);
    await loadImage(url);
    URL.revokeObjectURL(url);
    setStatus("Image imported");
  };

  return (
    <section className="canvas-pane">
      <div className="toolbar">
        <label>
          Tool
          <select value={tool} onChange={(e) => setTool(e.target.value as any)}>
            <option value="brush">Brush</option>
            <option value="rect">Rectangle</option>
            <option value="ellipse">Ellipse</option>
            <option value="line">Line</option>
            <option value="text">Text</option>
          </select>
        </label>
        {tool === 'text' && (
          <label>
            Text
            <input value={textValue} onChange={(e) => setTextValue(e.target.value)} />
          </label>
        )}
        <label>
          Color
          <input type="color" value={color} onChange={(event) => setColor(event.target.value)} />
        </label>
        <label>
          Size: {brushSize}px
          <input
            type="range"
            min={1}
            max={128}
            value={brushSize}
            onChange={(event) => setBrushSize(Number(event.target.value))}
          />
        </label>
        <label>
          Softness: {softness.toFixed(1)}
          <input
            type="range"
            min={0.1}
            max={1}
            step={0.1}
            value={softness}
            onChange={(event) => setSoftness(Number(event.target.value))}
          />
        </label>
        <label>
          Opacity: {Math.round(opacity * 100)}%
          <input
            type="range"
            min={0.1}
            max={1}
            step={0.05}
            value={opacity}
            onChange={(event) => setOpacity(Number(event.target.value))}
          />
        </label>
        <button type="button" onClick={() => setIsEraser((prev) => !prev)} className={isEraser ? "active" : ""}>
          {isEraser ? "✓ Eraser" : "Eraser"}
        </button>
        <button
          type="button"
          className={fillMode ? "active" : ""}
          onClick={() => setFillMode((prev) => !prev)}
        >
          {fillMode ? "Exit Fill" : "Fill Mode"}
        </button>
        <button type="button" onClick={undo}>
          Undo
        </button>
        <button type="button" onClick={redo}>
          Redo
        </button>
        <div className="filters">
          <button type="button" onClick={() => applyFilter(bindings?.FilterType.Blur ?? 0, 0.6)}>
            Blur
          </button>
          <button
            type="button"
            onClick={() => applyFilter(bindings?.FilterType.Sharpen ?? 1, 1)}
          >
            Sharpen
          </button>
          <button type="button" onClick={() => applyFilter(bindings?.FilterType.Invert ?? 2, 1)}>
            Invert
          </button>
          <button
            type="button"
            onClick={() => applyFilter(bindings?.FilterType.Grayscale ?? 3, 1)}
          >
            Grayscale
          </button>
        </div>
        {error && <span className="badge warning">{error}</span>}
        {bindings && !error && (
          <span className="badge success">{fillMode ? "Fill active" : "WASM ready"}</span>
        )}
      </div>

      <div className="import-tools">
        <label className="import-link">
          Import from URL
          <input
            type="url"
            placeholder="https://example.com/art.png"
            value={importUrl}
            onChange={(event) => setImportUrl(event.target.value)}
          />
        </label>
        <button type="button" onClick={handleImportUrl}>
          Import
        </button>
        <label className="import-file">
          Import file
          <input type="file" accept="image/*" onChange={handleLocalImport} />
        </label>
        {status && <span className="status">{status}</span>}
      </div>

      <canvas
        ref={canvasRef}
        width={DEFAULT_WIDTH}
        height={DEFAULT_HEIGHT}
        onMouseDown={handlePointerDown}
        onMouseUp={handlePointerUp}
        onMouseMove={handlePointerMove}
        onMouseLeave={handlePointerUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onTouchCancel={handleTouchEnd}
      />
    </section>
  );
};

const hexToRgb = (hex: string) => {
  const normalized = hex.replace("#", "");
  const bigint = parseInt(normalized, 16);
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255
  };
};

export default CanvasEditor;

