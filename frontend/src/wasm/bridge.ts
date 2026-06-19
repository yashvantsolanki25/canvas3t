type NormalizedFilterMap = Record<string, number>;

export type NormalizedWasm = {
  CanvasEngine: new (width: number, height: number) => {
    load_pixels(pixels: Uint8Array, width: number, height: number): void;
    export_pixels(): Uint8Array;
    width(): number;
    height(): number;
    clear(): void;
    undo(): boolean;
    redo(): boolean;
    apply_brush(
      startX: number,
      startY: number,
      endX: number,
      endY: number,
      options: unknown,
      erase: boolean
    ): void;
    flood_fill(x: number, y: number, options: unknown): void;
    apply_filter(filter: number, intensity: number): void;
  };
  BrushOptions: new (
    size: number,
    softness: number,
    opacity: number,
    color_r: number,
    color_g: number,
    color_b: number
  ) => object;
  FilterType: NormalizedFilterMap;
};

let cachedNative: Promise<NormalizedWasm> | null = null;

const normalizeFilterEnum = (input: Record<string, unknown>): NormalizedFilterMap => {
  const result: NormalizedFilterMap = {};
  Object.keys(input).forEach((key) => {
    if (Number.isNaN(Number(key))) {
      result[key] = input[key] as number;
    }
  });
  return result;
};

export const loadNativeWasm = (): Promise<NormalizedWasm> => {
  if (!cachedNative) {
    cachedNative = (async () => {
      try {
        // Import using the actual path - vite will handle the hashing
        const wasm = await import("./pkg/canvas3t_tools");
        
        // Handle both default export and named exports
        const wasmModule = wasm.default || wasm;
        
        if (typeof wasmModule === "function") {
          await wasmModule();
        }
        
        return {
          CanvasEngine: wasm.CanvasEngine,
          BrushOptions: wasm.BrushOptions,
          FilterType: normalizeFilterEnum(wasm.FilterType ?? {})
        };
      } catch (err) {
        console.error("WASM loading failed:", err);
        throw new Error(`Failed to load WASM: ${err instanceof Error ? err.message : String(err)}`);
      }
    })();
  }
  return cachedNative;
};

export const loadFallbackWasm = async (): Promise<NormalizedWasm> => {
  const fallback = await import("./fallback");
  return {
    CanvasEngine: fallback.CanvasEngine,
    BrushOptions: fallback.BrushOptions,
    FilterType: fallback.FilterType as NormalizedFilterMap
  };
};

