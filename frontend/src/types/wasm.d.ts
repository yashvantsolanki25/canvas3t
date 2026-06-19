declare module "../wasm/pkg/canvas3t_tools.js" {
  export class BrushOptions {
    constructor(
      size: number,
      softness: number,
      opacity: number,
      color_r: number,
      color_g: number,
      color_b: number
    );
  free(): void;
  [Symbol.dispose](): void;
  }

  export enum FilterType {
    Blur,
    Sharpen,
    Invert,
    Grayscale,
    Brightness
  }

  export class CanvasEngine {
    constructor(width: number, height: number);
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
      options: BrushOptions,
      erase: boolean
    ): void;
    flood_fill(x: number, y: number, options: BrushOptions): void;
    apply_filter(filter: FilterType, intensity: number): void;
  free(): void;
  [Symbol.dispose](): void;
  }

  export default function init(): Promise<void>;
}

