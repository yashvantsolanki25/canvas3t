export class CanvasEngine {
  private widthValue: number;
  private heightValue: number;
  private buffer: Uint8ClampedArray;

  constructor(width: number, height: number) {
    this.widthValue = width;
    this.heightValue = height;
    this.buffer = new Uint8ClampedArray(width * height * 4);
  }

  width() {
    return this.widthValue;
  }

  height() {
    return this.heightValue;
  }

  load_pixels(pixels: Uint8Array, width: number, height: number) {
    this.widthValue = width;
    this.heightValue = height;
    this.buffer = new Uint8ClampedArray(pixels);
  }

  export_pixels() {
    return new Uint8Array(this.buffer);
  }

  clear() {
    this.buffer.fill(0);
  }

  undo() {
    return false;
  }

  redo() {
    return false;
  }

  apply_brush() {}
  flood_fill() {}
  apply_filter() {}
}

export const FilterType = {
  Blur: 0,
  Sharpen: 1,
  Invert: 2,
  Grayscale: 3,
  Brightness: 4
} as const;

export class BrushOptions {
  constructor(
    public size: number,
    public softness: number,
    public opacity: number,
    public color_r: number,
    public color_g: number,
    public color_b: number
  ) {}
}

export default async function loadFallback() {
  return { CanvasEngine, BrushOptions, FilterType };
}

