use std::cmp::{max, min};
use std::collections::VecDeque;

use wasm_bindgen::prelude::*;

const CHANNELS: usize = 4;

#[wasm_bindgen]
pub struct BrushOptions {
    size: f32,
    softness: f32,
    opacity: f32,
    color_r: u8,
    color_g: u8,
    color_b: u8,
}

#[wasm_bindgen]
impl BrushOptions {
    #[wasm_bindgen(constructor)]
    pub fn new(
        size: f32,
        softness: f32,
        opacity: f32,
        color_r: u8,
        color_g: u8,
        color_b: u8,
    ) -> BrushOptions {
        BrushOptions {
            size,
            softness,
            opacity,
            color_r,
            color_g,
            color_b,
        }
    }
}

#[wasm_bindgen]
pub enum FilterType {
    Blur,
    Sharpen,
    Invert,
    Grayscale,
    Brightness,
}

#[wasm_bindgen]
pub struct CanvasEngine {
    width: u32,
    height: u32,
    buffer: Vec<u8>,
    undo_stack: Vec<Vec<u8>>,
    redo_stack: Vec<Vec<u8>>,
}

#[wasm_bindgen]
impl CanvasEngine {
    #[wasm_bindgen(constructor)]
    pub fn new(width: u32, height: u32) -> CanvasEngine {
        CanvasEngine {
            width,
            height,
            buffer: vec![0; (width * height * CHANNELS as u32) as usize],
            undo_stack: Vec::new(),
            redo_stack: Vec::new(),
        }
    }

    pub fn load_pixels(&mut self, pixels: &[u8], width: u32, height: u32) {
        self.width = width;
        self.height = height;
        self.buffer = pixels.to_vec();
        self.undo_stack.clear();
        self.redo_stack.clear();
    }

    pub fn export_pixels(&self) -> Vec<u8> {
        self.buffer.clone()
    }

    pub fn width(&self) -> u32 {
        self.width
    }

    pub fn height(&self) -> u32 {
        self.height
    }

    pub fn clear(&mut self) {
        self.snapshot();
        self.buffer.fill(0);
    }

    pub fn undo(&mut self) -> bool {
        if let Some(state) = self.undo_stack.pop() {
            self.redo_stack.push(self.buffer.clone());
            self.buffer = state;
            true
        } else {
            false
        }
    }

    pub fn redo(&mut self) -> bool {
        if let Some(state) = self.redo_stack.pop() {
            self.undo_stack.push(self.buffer.clone());
            self.buffer = state;
            true
        } else {
            false
        }
    }

    pub fn apply_brush(
        &mut self,
        start_x: f32,
        start_y: f32,
        end_x: f32,
        end_y: f32,
        options: &BrushOptions,
        erase: bool,
    ) {
        self.snapshot();
        let steps = max(
            (start_x - end_x).abs() as i32,
            (start_y - end_y).abs() as i32,
        )
        .max(1);
        for step in 0..=steps {
            let t = step as f32 / steps as f32;
            let x = start_x + (end_x - start_x) * t;
            let y = start_y + (end_y - start_y) * t;
            self.stamp(x, y, options, erase);
        }
    }

    pub fn flood_fill(&mut self, start_x: u32, start_y: u32, options: &BrushOptions) {
        if start_x >= self.width || start_y >= self.height {
            return;
        }
        self.snapshot();
        let idx = self.index(start_x, start_y);
        let target = self.buffer[idx..idx + 4].to_vec();
        let replacement = [
            options.color_r,
            options.color_g,
            options.color_b,
            (options.opacity * 255.0) as u8,
        ];
        if target == replacement {
            return;
        }
        let mut queue = VecDeque::new();
        queue.push_back((start_x, start_y));
        while let Some((x, y)) = queue.pop_front() {
            let idx = self.index(x, y);
            if self.buffer[idx..idx + 4] != target {
                continue;
            }
            self.set_pixel(idx, &replacement);
            if x > 0 {
                queue.push_back((x - 1, y));
            }
            if x + 1 < self.width {
                queue.push_back((x + 1, y));
            }
            if y > 0 {
                queue.push_back((x, y - 1));
            }
            if y + 1 < self.height {
                queue.push_back((x, y + 1));
            }
        }
    }

    pub fn apply_filter(&mut self, filter: FilterType, intensity: f32) {
        self.snapshot();
        match filter {
            FilterType::Blur => self.blur(max(1, (intensity * 5.0) as i32)),
            FilterType::Sharpen => self.sharpen(),
            FilterType::Invert => self.invert(),
            FilterType::Grayscale => self.grayscale(),
            FilterType::Brightness => self.brightness(intensity),
        }
    }

    fn set_pixel(&mut self, idx: usize, rgba: &[u8; 4]) {
        self.buffer[idx] = rgba[0];
        self.buffer[idx + 1] = rgba[1];
        self.buffer[idx + 2] = rgba[2];
        self.buffer[idx + 3] = rgba[3];
    }

    fn stamp(&mut self, cx: f32, cy: f32, options: &BrushOptions, erase: bool) {
        let radius = (options.size / 2.0).max(1.0);
        let min_x = max((cx - radius).floor() as i32, 0);
        let max_x = min((cx + radius).ceil() as i32, self.width as i32 - 1);
        let min_y = max((cy - radius).floor() as i32, 0);
        let max_y = min((cy + radius).ceil() as i32, self.height as i32 - 1);
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                let dx = x as f32 - cx;
                let dy = y as f32 - cy;
                let distance = (dx * dx + dy * dy).sqrt();
                if distance > radius {
                    continue;
                }
                let softness = options.softness.clamp(0.01, 1.0);
                let falloff = 1.0 - (distance / radius).powf(softness * 2.0);
                let idx = self.index(x as u32, y as u32);
                if erase {
                    self.buffer[idx + 3] = (self.buffer[idx + 3] as f32
                        * (1.0 - falloff * options.opacity))
                        .round() as u8;
                } else {
                    self.buffer[idx] = lerp(self.buffer[idx], options.color_r, falloff, options.opacity);
                    self.buffer[idx + 1] =
                        lerp(self.buffer[idx + 1], options.color_g, falloff, options.opacity);
                    self.buffer[idx + 2] =
                        lerp(self.buffer[idx + 2], options.color_b, falloff, options.opacity);
                    let alpha = (options.opacity * 255.0 * falloff).min(255.0) as u8;
                    self.buffer[idx + 3] = alpha.max(self.buffer[idx + 3]);
                }
            }
        }
    }

    fn blur(&mut self, radius: i32) {
        let kernel = (2 * radius + 1) as u32;
        let mut output = self.buffer.clone();
        for y in 0..self.height as i32 {
            for x in 0..self.width as i32 {
                let mut acc = [0f32; 4];
                let mut samples = 0f32;
                for ky in -radius..=radius {
                    for kx in -radius..=radius {
                        let nx = x + kx;
                        let ny = y + ky;
                        if nx < 0 || ny < 0 || nx >= self.width as i32 || ny >= self.height as i32 {
                            continue;
                        }
                        let idx = self.index(nx as u32, ny as u32);
                        acc[0] += self.buffer[idx] as f32;
                        acc[1] += self.buffer[idx + 1] as f32;
                        acc[2] += self.buffer[idx + 2] as f32;
                        acc[3] += self.buffer[idx + 3] as f32;
                        samples += 1.0;
                    }
                }
                let idx = self.index(x as u32, y as u32);
                output[idx] = (acc[0] / samples) as u8;
                output[idx + 1] = (acc[1] / samples) as u8;
                output[idx + 2] = (acc[2] / samples) as u8;
                output[idx + 3] = (acc[3] / samples) as u8;
            }
        }
        self.buffer = output;
    }

    fn sharpen(&mut self) {
        let kernel: [[i32; 3]; 3] = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]];
        self.convolution(kernel, 1);
    }

    fn grayscale(&mut self) {
        for i in (0..self.buffer.len()).step_by(4) {
            let gray =
                (0.299 * self.buffer[i] as f32 + 0.587 * self.buffer[i + 1] as f32 + 0.114 * self.buffer[i + 2] as f32)
                    as u8;
            self.buffer[i] = gray;
            self.buffer[i + 1] = gray;
            self.buffer[i + 2] = gray;
        }
    }

    fn invert(&mut self) {
        for i in (0..self.buffer.len()).step_by(4) {
            self.buffer[i] = 255 - self.buffer[i];
            self.buffer[i + 1] = 255 - self.buffer[i + 1];
            self.buffer[i + 2] = 255 - self.buffer[i + 2];
        }
    }

    fn brightness(&mut self, intensity: f32) {
        let factor = (intensity * 255.0).round() as i32;
        for i in (0..self.buffer.len()).step_by(4) {
            self.buffer[i] = clamp_channel(self.buffer[i] as i32 + factor);
            self.buffer[i + 1] = clamp_channel(self.buffer[i + 1] as i32 + factor);
            self.buffer[i + 2] = clamp_channel(self.buffer[i + 2] as i32 + factor);
        }
    }

    fn convolution(&mut self, kernel: [[i32; 3]; 3], divisor: i32) {
        let mut output = self.buffer.clone();
        for y in 1..self.height - 1 {
            for x in 1..self.width - 1 {
                let mut acc = [0i32; 3];
                for ky in 0..3 {
                    for kx in 0..3 {
                        let weight = kernel[ky as usize][kx as usize];
                        let idx = self.index(x + kx as u32 - 1, y + ky as u32 - 1);
                        acc[0] += self.buffer[idx] as i32 * weight;
                        acc[1] += self.buffer[idx + 1] as i32 * weight;
                        acc[2] += self.buffer[idx + 2] as i32 * weight;
                    }
                }
                let idx = self.index(x, y);
                output[idx] = clamp_channel(acc[0] / divisor);
                output[idx + 1] = clamp_channel(acc[1] / divisor);
                output[idx + 2] = clamp_channel(acc[2] / divisor);
            }
        }
        self.buffer = output;
    }

    fn snapshot(&mut self) {
        self.undo_stack.push(self.buffer.clone());
        if self.undo_stack.len() > 32 {
            self.undo_stack.remove(0);
        }
        self.redo_stack.clear();
    }

    fn index(&self, x: u32, y: u32) -> usize {
        ((y * self.width + x) * CHANNELS as u32) as usize
    }
}

fn clamp_channel(value: i32) -> u8 {
    value.clamp(0, 255) as u8
}

fn lerp(current: u8, target: u8, falloff: f32, opacity: f32) -> u8 {
    let c = current as f32;
    let t = target as f32;
    let delta = (t - c) * falloff * opacity;
    clamp_channel((c + delta) as i32)
}
