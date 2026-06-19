# Canvas3T Architecture

Canvas3T is a three-tier system composed of a SPA frontend, a Flask REST API, and persistent storage (SQLite + image files on disk). Docker Compose orchestrates the tiers with named volumes for durability.

## Presentation Tier (React SPA)

- Built with Vite + React + TypeScript for fast iteration.
- Routes:
  - `GalleryView`: folder-style grid with filters, bulk actions, and search bar.
  - `EditorView`: HTML5 canvas editor paired with WASM-powered tools for heavy operations.
  - `DetailView`: enlarged artwork with metadata controls and download/export actions.
- Global state managed with Zustand; React Query handles API data caching.
- Header ships with an inline auth panel (register/login/logout) backed by the Flask endpoints, and gallery filters (format + tag) that drive query params.
- Canvas tooling:
  - WASM bridge module normalizes the wasm-bindgen output into a type-safe interface consumed by React hooks.
  - `CanvasEngine` handles brush/eraser, fill, filters (blur, sharpen, invert, grayscale, brightness), undo/redo, and layer-sized pixel export.
  - Optimistic UI on save/edit with status indicators, remote import feedback, and autosave intervals.
- Accessibility: keyboard shortcuts, ARIA labels, high-contrast toggle, responsive layout breakpoints.

## Application Tier (Flask API)

- Flask application structured with blueprints:
  - `api.users`: registration + user listing with hashed password storage.
  - `api.auth`: login endpoint returning signed tokens via `itsdangerous`.
  - `api.paintings`: painting CRUD + pagination/filtering, remote image import, multi-format encoding, and proxy import endpoint used by the SPA.
  - `api.search`: advanced search alias for cross-folder queries.
- Core modules:
  - `db.py`: SQLAlchemy engine/session factory, scoped per request, SQLite WAL enabled.
  - `models.py`: `User` and `Painting` ORM models, now tracking the persisted file `format`.
  - `storage.py`: handles secure filenames, UUID prefixes, downloads remote images, and normalizes to PNG/JPEG/WEBP.
  - `thumbnails.py`: Pillow-based thumbnail generator (configurable max size).
  - `schemas.py`: Marshmallow schemas for validation/serialization.
- Middleware:
  - CORS enabled for SPA.
  - Basic rate limiting stub via simple in-memory token bucket (extendable to Redis).
- Token helper built on `itsdangerous` for lightweight auth (swap for JWT/OPA later).
- Pagination/search implemented with SQLAlchemy query composition (`q`, `folder`, `tag`, `page`, `per_page`).
- File uploads use `werkzeug.datastructures.FileStorage` streamed directly onto the Docker-mounted volume.

## Data Tier

- SQLite database stored inside the named volume `canvas3t_db` (automatically mounted at `/app/db` inside the API container).
- Image assets + thumbnails live in `canvas3t_images` (`/app/images`), ensuring exported artwork persists across container restarts.
- Naming convention: `f"{uuid4().hex}_{secure_filename(original_name)}"`.
- Metadata fields tracked: dimensions (queried via Pillow), tools, tags, folder, created/updated timestamps.
- WAL mode and `PRAGMA foreign_keys = ON` configured during connection initialization.

## WebAssembly Module

- Rust-based crate compiled with `wasm-pack`.
- Exposes:
  - `apply_brush(buffer, width, height, brush_options)`
  - `apply_filter(buffer, width, height, filter_type, params)`
  - `diff_layers(base, top)` for fast undo/redo diffs.
- Built artifacts placed into `frontend/src/wasm/` via `npm run build:wasm`.
- Fallback JS implementations keep editor functional when WASM fails to load.

## Docker & Deployment

- `Dockerfile` (backend): `python:3.11-slim`, installs build deps (gcc, libjpeg), copies backend, installs requirements, runs `gunicorn`.
- `frontend/Dockerfile`: multi-stage (Rust + Node). Builds the Rust WASM module via `wasm-pack`, copies artifacts into the React build, and serves the static bundle with `serve`.
- `docker-compose.yml`:
  - Service `web`: builds backend, exposes port 5000 → host 5000, mounts `canvas3t_images` and `canvas3t_db`.
  - Service `frontend`: builds the SPA (including the WASM step) and serves it on 5173; consumes REST API via `WEB_API_URL`.
  - Named volumes: `canvas3t_images`, `canvas3t_db`.

## Development Workflow

1. `python -m venv .venv && pip install -r backend/requirements.txt`.
2. `npm install` inside `frontend/`.
3. `flask db upgrade` (or `python backend/manage.py init-db`) to create schema.
4. Run backend (`flask run` or `gunicorn wsgi:app`) and frontend (`npm run dev`).
5. Optional: `npm run build:wasm` to compile WASM helpers before running the editor.

## Testing & Quality

- Backend: pytest + Flask test client, covering CRUD and storage helpers.
- Frontend: Vitest + React Testing Library for key components, Playwright stubs for editor interactions.
- WASM: Rust unit tests ensuring deterministic brush/filter outputs.
- CI/CD pipeline (future): run lint/test for Python, Node, and Rust; build Docker images; push to registry.

This document should serve as a living reference for contributors implementing or extending Canvas3T.

