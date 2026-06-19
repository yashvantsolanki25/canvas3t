# Canvas3T - Complete System Architecture & Setup Guide

## Overview
Canvas3T is a full-stack web application for creating, editing, uploading, and managing digital paintings with persistent storage and user authentication.

**Current Status**: ✅ Fully Functional
- User registration and authentication working
- Image upload and storage persisting to database and Docker volumes
- Gallery displays user's saved paintings with thumbnails
- Container restart preserves all data via named volumes

---

## 1. DATABASE SCHEMA

### Location in Container
```
/app/db/app.db
```

### Tables

#### **users**
Stores user account information with password hashing.

```sql
CREATE TABLE users (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  username          VARCHAR(80) UNIQUE NOT NULL,
  email             VARCHAR(120) UNIQUE NOT NULL,
  password_hash     VARCHAR(255) NOT NULL,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Key Points**:
- `password_hash`: Uses werkzeug.security `generate_password_hash(method='pbkdf2:sha256')`
- `username`: Unique index, used for file organization
- Auto-timestamps track creation and updates

#### **paintings**
Stores painting metadata and file paths for gallery display.

```sql
CREATE TABLE paintings (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id           INTEGER FOREIGN KEY → users.id,
  title             VARCHAR(255) NOT NULL DEFAULT 'Untitled',
  description       TEXT DEFAULT '',
  filename          VARCHAR(512) NOT NULL,
  prefix            VARCHAR(36),
  folder            VARCHAR(255) DEFAULT '',
  width             INTEGER DEFAULT 0,
  height            INTEGER DEFAULT 0,
  format            VARCHAR(10) DEFAULT 'png',
  is_public         BOOLEAN NOT NULL DEFAULT 0 INDEX,
  tags              TEXT DEFAULT '',
  thumbnail         VARCHAR(512),
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP INDEX,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields Explanation**:
- `filename`: **RELATIVE PATH** stored in database (e.g., `username/folder/prefix_imagename.png`)
- `prefix`: 8-character UUID generated for uniqueness (e.g., `a1b2c3d4`)
- `folder`: User-defined folder name (e.g., "landscapes", "portraits")
- `is_public`: Boolean flag for visibility (default: false = private)
- `thumbnail`: Relative path to compressed thumbnail (e.g., `username/folder/prefix_imagename_thumb.jpg`)

---

## 2. IMAGE STORAGE STRUCTURE

### Storage Location in Container
```
Container Path:      /app/images
Host Mounted Via:    Docker named volume "canvas3t_images"
```

### Directory Tree
```
/app/images/
├── anonymous/              # Default folder for unauthenticated uploads
│   ├── folder_name_1/
│   │   ├── a1b2c3d4_image1.png          ← Full image
│   │   ├── a1b2c3d4_image1_thumb.jpg    ← Thumbnail
│   │   ├── e5f6g7h8_image2.jpg
│   │   └── e5f6g7h8_image2_thumb.jpg
│   └── folder_name_2/
│       └── ...
│
├── demo/                   # User 'demo' (default user)
│   ├── sketches/
│   │   ├── b2c3d4e5_myart.png
│   │   └── b2c3d4e5_myart_thumb.jpg
│   └── uploads/
│       └── ...
│
└── user_jane/              # User 'jane'
    ├── nature/
    │   ├── c3d4e5f6_sunset.jpg
    │   └── c3d4e5f6_sunset_thumb.jpg
    └── abstract/
        └── ...
```

### File Naming Convention
```
{8-char-uuid}_{sanitized-original-name}.{extension}
```

**Example**: 
- Original upload: `My Beautiful Landscape.jpg`
- Saved as: `a1b2c3d4_my-beautiful-landscape.jpg`

### Thumbnail Convention
```
{8-char-uuid}_{sanitized-original-name}_thumb.jpg
```

**Example**: `a1b2c3d4_my-beautiful-landscape_thumb.jpg`

---

## 3. API ENDPOINTS

### Base URLs
```
Frontend (Development):  http://localhost:5173
Frontend (Production):   http://localhost:4173 (with nginx)
Backend:                 http://localhost:5000
Backend (from container): http://web:5000
```

### Authentication Endpoints

#### **POST /api/users** - Register New User
```bash
curl -X POST http://localhost:5173/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

**Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "created_at": "2025-11-29T10:30:00"
  }
}
```

#### **POST /api/auth/login** - Login User
```bash
curl -X POST http://localhost:5173/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePass123"
  }'
```

**Response** (200 OK):
```json
{
  "message": "Login successful",
  "token": "eyJjbGFzcyI6IklUUyJ9.ZW....",
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "created_at": "2025-11-29T10:30:00"
  }
}
```

**Token Storage** (Frontend):
- Stored in `localStorage` as key: `canvas3t.auth`
- Value: JSON object `{ token: "...", user: {...} }`
- Auto-injected in all subsequent requests via axios interceptor

#### **POST /api/auth/verify** - Verify Token
```bash
curl -X POST http://localhost:5173/api/auth/verify \
  -H "Authorization: Bearer eyJjbGFzcyI6IklUUyJ9.ZW...."
```

**Response** (200 OK):
```json
{
  "valid": true,
  "user": { "id": 1, "username": "john", ... }
}
```

---

### Paintings (Image Upload/Management)

#### **POST /api/paintings** - Upload/Save Painting
```bash
curl -X POST http://localhost:5173/api/paintings \
  -H "Authorization: Bearer {token}" \
  -F "image=@/path/to/image.png" \
  -F "title=My Artwork" \
  -F "folder=landscapes" \
  -F "tags=nature,sunset" \
  -F "is_public=true" \
  -F "format=PNG"
```

**Response** (201 Created):
```json
{
  "message": "Painting created successfully",
  "painting": {
    "id": 5,
    "user_id": 1,
    "username": "john",
    "title": "My Artwork",
    "filename": "john/landscapes/a1b2c3d4_image.png",
    "prefix": "a1b2c3d4",
    "folder": "landscapes",
    "width": 1920,
    "height": 1080,
    "format": "png",
    "is_public": true,
    "tags": "nature,sunset",
    "thumbnail": "john/landscapes/a1b2c3d4_image_thumb.jpg",
    "image_url": "/media/images/john/landscapes/a1b2c3d4_image.png",
    "thumbnail_url": "/media/images/john/landscapes/a1b2c3d4_image_thumb.jpg",
    "created_at": "2025-11-29T10:31:00",
    "updated_at": "2025-11-29T10:31:00"
  }
}
```

#### **GET /api/paintings** - List Paintings
```bash
# List user's own paintings
curl -X GET "http://localhost:5173/api/paintings?user_id=1&page=1" \
  -H "Authorization: Bearer {token}"

# List public paintings (no auth needed)
curl -X GET "http://localhost:5173/api/paintings?page=1"
```

**Response** (200 OK):
```json
{
  "total": 12,
  "page": 1,
  "per_page": 24,
  "pages": 1,
  "items": [
    {
      "id": 5,
      "user_id": 1,
      "username": "john",
      "title": "My Artwork",
      "filename": "john/landscapes/a1b2c3d4_image.png",
      "image_url": "/media/images/john/landscapes/a1b2c3d4_image.png",
      "thumbnail_url": "/media/images/john/landscapes/a1b2c3d4_image_thumb.jpg",
      ...
    }
  ]
}
```

#### **GET /media/images/{path}** - Serve Image
```bash
# Request
curl -X GET "http://localhost:5173/media/images/john/landscapes/a1b2c3d4_image.png"

# Response: Image file (image/png, image/jpeg, etc.)
```

---

## 4. AUTHENTICATION FLOW

### Registration to Viewing Gallery

```
┌─────────────────────────────────────────────────────────────────┐
│ USER: Click "Register"                                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Show registration form                                 │
│ - username, email, password fields                               │
│ - Submit POST /api/users with credentials                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: POST /api/users                                         │
│ 1. Validate input (length, format, duplicates)                   │
│ 2. Hash password using werkzeug.security                         │
│ 3. Create User record in database                                │
│ 4. Return 201 + user data                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Auto-login user after registration                     │
│ 1. POST /api/auth/login with same credentials                    │
│ 2. Backend returns token                                         │
│ 3. Store in localStorage: canvas3t.auth = {token, user}          │
│ 4. Set axios Authorization header via interceptor                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Fetch gallery (GET /api/paintings?user_id={id})        │
│ 1. axios interceptor auto-adds: Authorization: Bearer {token}    │
│ 2. Backend verifies token using itsdangerous serializer           │
│ 3. Return user's paintings list (200)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Render gallery grid                                    │
│ - Display thumbnails from thumbnail_url field                    │
│ - Show title, tags, format badge                                 │
│ - Link to edit or view painting                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. IMAGE UPLOAD & SAVE FLOW

### Canvas Editor to Gallery

```
┌─────────────────────────────────────────────────────────────────┐
│ USER: Draw on canvas or import image                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ USER: Fill metadata panel                                        │
│ - Title: "Sunset Over Mountains"                                 │
│ - Folder: "landscapes"                                           │
│ - Tags: "nature,sunset"                                          │
│ - Format: PNG/JPEG/WEBP                                          │
│ - Is Public: true/false                                          │
│ - Click "Save painting" button                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: MetadataPanel.tsx                                      │
│ 1. Get canvas element                                            │
│ 2. Convert canvas to Blob (toBlob with specified format mime)    │
│ 3. Create FormData with:                                         │
│    - image: Blob                                                 │
│    - title: string                                               │
│    - folder: string                                              │
│    - tags: string                                                │
│    - format: PNG|JPEG|WEBP                                       │
│    - is_public: "true"|"false"                                   │
│ 4. POST /api/paintings (axios auto-injects Bearer token)         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: POST /api/paintings (paintings.py)                      │
│                                                                  │
│ 1. Extract FormData fields                                       │
│ 2. Parse Bearer token from Authorization header                  │
│    - Token contains: {user_id, username}                         │
│ 3. Get user from database (verify exists)                        │
│ 4. Check image file present and valid                            │
│ 5. Call save_image() function:                                   │
│    a. Create directories:                                        │
│       /app/images/                                               │
│       /app/images/{username}/                                    │
│       /app/images/{username}/{folder}/                           │
│    b. Generate UUID prefix (8 chars): a1b2c3d4                   │
│    c. Sanitize filename: secure_filename()                       │
│    d. Save image: a1b2c3d4_sunset-mountains.png                  │
│    e. Get image dimensions using Pillow                          │
│    f. Create thumbnail (resize to 200x200):                      │
│       a1b2c3d4_sunset-mountains_thumb.jpg                        │
│    g. Build relative paths:                                      │
│       filename: john/landscapes/a1b2c3d4_sunset.png              │
│       thumbnail: john/landscapes/a1b2c3d4_sunset_thumb.jpg       │
│ 6. Create Painting record in database:                           │
│    - user_id: 1                                                  │
│    - title: "Sunset Over Mountains"                              │
│    - filename: "john/landscapes/a1b2c3d4_sunset.png"             │
│    - thumbnail: "john/landscapes/a1b2c3d4_sunset_thumb.jpg"      │
│    - prefix: "a1b2c3d4"                                          │
│    - folder: "landscapes"                                        │
│    - is_public: true                                             │
│    - width, height, format                                       │
│ 7. db.session.commit() → SAVED TO DATABASE                       │
│ 8. Return 201 + painting data with URLs                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Show success message                                   │
│ - "Saved successfully" at timestamp                              │
│ - Optionally navigate to gallery or show painting card           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Fetch updated gallery (GET /api/paintings?user_id=1)   │
│ - Backend queries paintings table with user_id=1 filter          │
│ - Returns list with new painting + URLs                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Render gallery card                                    │
│ - Fetch thumbnail_url: /media/images/john/.../a1b2c3d4_...jpg   │
│ - Display title, tags, format badge                              │
│ - Show created timestamp                                         │
│ - Link to edit or view painting                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. PERSISTENCE & DATA RECOVERY

### Docker Named Volumes

Canvas3T uses **Docker named volumes** for persistent storage:

```yaml
volumes:
  canvas3t_images:
    driver: local    # Persists /app/images
  canvas3t_db:
      driver: local    # Persists /app/db/app.db
```

### What Persists Across Container Restarts

✅ **Database** (`canvas3t_db` volume):
- User accounts with password hashes
- Painting metadata (title, tags, is_public, etc.)
- Image file paths stored in database

✅ **Image Files** (`canvas3t_images` volume):
- All uploaded PNG, JPEG, GIF, WEBP, BMP files
- Thumbnails in same location
- Directory structure by username and folder

### Verify Persistence

**Before restart:**
```bash
# Check files exist
docker exec canvas3t_api ls -la /app/images/john/landscapes/

# Check database records
docker exec canvas3t_api python3 -c "
from app import create_app
from app.models import Painting
app = create_app()
with app.app_context():
    for p in Painting.query.all():
        print(f'{p.title} → {p.filename}')
"
```

**Perform restart:**
```bash
docker compose down    # Stop and remove containers
docker compose up -d   # Start containers again
```

**After restart:**
```bash
# Files still exist
docker exec canvas3t_api ls -la /app/images/john/landscapes/

# Database records still exist
docker exec canvas3t_api python3 -c "
from app import create_app
from app.models import Painting
app = create_app()
with app.app_context():
    count = len(Painting.query.all())
    print(f'Total paintings: {count}')
"

# Frontend gallery still shows paintings
# Navigate to http://localhost:5173 and login
```

### Remove All Data (Clean Reset)

```bash
# Stop containers and remove volumes
docker compose down -v

# Next docker compose up will create fresh database and volumes
docker compose up -d
```

---

## 7. BACKEND FILE STRUCTURE

```
backend/
├── app/
│   ├── __init__.py          ← App factory, DB init, blueprint registration
│   ├── config.py            ← Configuration (DATABASE_URI, IMAGE_DIR, etc.)
│   ├── extensions.py        ← SQLAlchemy, CORS, rate limiter setup
│   ├── models.py            ← User, Painting ORM models
│   ├── schemas.py           ← Input validation schemas
│   └── api/
│       ├── __init__.py
│       ├── auth.py          ← /api/auth/login, /api/auth/verify
│       ├── users.py         ← /api/users (register, list, get)
│       ├── paintings.py     ← /api/paintings (list, create, import-url)
│       ├── media.py         ← /media/images/ (serve files)
│       └── search.py        ← /api/search (not fully implemented)
│
├── manage.py                ← Flask CLI commands
├── wsgi.py                  ← WSGI entry point for production
└── requirements.txt         ← Python dependencies
```

---

## 8. FRONTEND FILE STRUCTURE

```
frontend/
├── src/
│   ├── main.tsx             ← React entry point
│   ├── App.tsx              ← Root component, routing
│   ├── api/
│   │   ├── client.ts        ← Axios instance with auth interceptor
│   │   ├── auth.ts          ← register(), loginUser()
│   │   └── paintings.ts     ← fetchPaintings(), createPainting()
│   │
│   ├── store/
│   │   ├── authStore.ts     ← Zustand store for auth state
│   │   └── galleryStore.ts  ← Zustand store for gallery state
│   │
│   ├── components/
│   │   ├── AuthPanel.tsx    ← Login/register form
│   │   ├── MetadataPanel.tsx ← Canvas metadata form (SAVE button)
│   │   ├── CanvasEditor.tsx ← Drawing canvas
│   │   ├── GalleryGrid.tsx  ← Display paintings grid
│   │   ├── ErrorBoundary.tsx ← Error boundary
│   │   └── ...
│   │
│   ├── pages/
│   │   ├── EditorView.tsx   ← /editor route
│   │   ├── GalleryView.tsx  ← /gallery route
│   │   └── DetailView.tsx   ← /paintings/:id route
│   │
│   └── styles.css           ← Global styles
│
├── vite.config.ts           ← Vite build config
├── tsconfig.json            ← TypeScript config
└── Dockerfile               ← Multi-stage build + nginx
```

---

## 9. DOCKER DEPLOYMENT

### Build Images
```bash
docker compose build
```

### Start Services
```bash
docker compose up -d
```

### Services Running

| Service | Container | Port | URL | Purpose |
|---------|-----------|------|-----|---------|
| **Backend API** | canvas3t_api | 5000 | http://localhost:5000 | Flask API + image serving |
| **Frontend** | canvas3t_frontend | 5173 | http://localhost:5173 | Vite dev server + nginx |
| **nginx** | (in frontend) | 4173→5173 | - | Reverse proxy for /api, /media |
| **Database** | (volume) | - | /app/db/app.db | SQLite |
| **Images** | (volume) | - | /app/images | Stored paintings |

### Health Checks
```bash
# Backend health
curl http://localhost:5000/api/health

# Frontend accessibility
curl -I http://localhost:5173

# Check volumes
docker volume ls | grep canvas3t
docker volume inspect canvas3t_images
docker volume inspect canvas3t_db
```

---

## 10. COMPLETE END-TO-END WORKFLOW

### Step 1: Start Application
```bash
docker compose up -d
# Wait ~10 seconds for services to initialize
```

### Step 2: Access Frontend
```
Open browser: http://localhost:5173
```

### Step 3: Register New User
```
1. Click "Register" or "Sign Up"
2. Fill form:
   - Username: jane_artist
   - Email: jane@example.com
   - Password: SecurePass123
3. Click "Register"
```

### Step 4: Verify Registration
✅ Auto-redirects to gallery
✅ Token stored in localStorage
✅ User record in database

### Step 5: Navigate to Editor
```
1. Click "New" or "Create Painting" button
2. Canvas appears
```

### Step 6: Create Artwork
```
1. Draw on canvas OR import image
2. Fill metadata:
   - Title: "My First Artwork"
   - Folder: "sketches"
   - Tags: "abstract,first"
   - Format: PNG
   - Public: toggle on/off
3. Click "Save painting"
```

### Step 7: Verify Save Success
✅ Status shows: "Saved at HH:MM:SS"
✅ Gallery updates with new painting
✅ Image appears with thumbnail
✅ Can see in console: full file path

### Step 8: Verify Data Location
```bash
# Check files exist in container
docker exec canvas3t_api ls -la /app/images/jane_artist/sketches/

# Check database
docker exec canvas3t_api python3 -c "
from app import create_app
from app.models import Painting
app = create_app()
with app.app_context():
    for p in Painting.query.filter_by(title='My First Artwork'):
        print(f'ID: {p.id}')
        print(f'File: {p.filename}')
        print(f'Thumbnail: {p.thumbnail}')
        print(f'Public: {p.is_public}')
"
```

### Step 9: Test Persistence
```bash
# Restart containers
docker compose down
docker compose up -d

# Verify painting still exists
# Login with same credentials
# Gallery shows painting
# Files exist in volume
```

---

## 11. TROUBLESHOOTING

### Issue: "Save failed" on image upload

**Possible Causes & Solutions**:

1. **Not logged in**
   - Solution: Check localStorage for `canvas3t.auth` key
   - Verify token is valid: `POST /api/auth/verify`

2. **Token invalid or expired**
   - Solution: Log out and log back in
   - Token lifetime: 7 days (can be changed in `auth.py`)

3. **Image file too large**
   - Solution: Backend accepts up to system limit (usually 100MB+)
   - Check server logs: `docker logs canvas3t_api`

4. **Disk space full**
   - Solution: Check container disk: `docker exec canvas3t_api df -h`
   - Clean up old volumes: `docker volume prune`

### Issue: Gallery shows no images

**Possible Causes & Solutions**:

1. **Wrong user_id in request**
   - Solution: Verify logged-in user ID: check browser console
   - Verify paintings exist: `GET /api/paintings?user_id=1`

2. **Images not public but user not authenticated**
   - Solution: Ensure Bearer token in request headers
   - Check: `Authorization: Bearer {valid_token}`

3. **Image URLs broken (404 on /media/images/...)**
   - Solution: Verify filename in database
   - Check: `docker exec canvas3t_api ls -la /app/images/{username}/`
   - Verify nginx proxy working: check nginx logs

### Issue: Container restart loses data

**Possible Causes & Solutions**:

1. **Volumes removed during `docker compose down -v`**
   - Solution: Don't use `-v` flag unless you want to delete
   - Use: `docker compose down` (keeps volumes)

2. **Volumes not mounted correctly**
   - Solution: Verify docker-compose.yml volumes section
   - Check: `docker volume ls | grep canvas3t`
   - Inspect: `docker volume inspect canvas3t_images`

3. **Images saved to non-persistent location**
   - Solution: Verify IMAGE_DIR=/app/images (in docker-compose.yml)
   - Check backend logs: `docker logs canvas3t_api`

---

## 12. KEY TECHNICAL DETAILS

### Password Security
- **Hashing**: werkzeug.security.generate_password_hash(method='pbkdf2:sha256')
- **Verification**: werkzeug.security.check_password_hash()
- **Never stored**: Plain passwords never stored in database

### Token Security
- **Serializer**: itsdangerous.URLSafeTimedSerializer
- **Payload**: `{'user_id': int, 'username': str}`
- **Lifetime**: 7 days (604800 seconds)
- **Secret**: `app.config['SECRET_KEY']` (must be kept secret in production)

### Image Processing
- **Library**: Pillow (PIL)
- **Supported Formats**: PNG, JPEG, GIF, WEBP, BMP
- **Thumbnail Size**: 200×200 pixels
- **Thumbnail Format**: JPEG (quality=85)
- **Unique ID**: UUID 8-char prefix prevents filename collisions

### CORS Configuration
- **Allowed Origins**: All (*) in development
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization
- **Credentials**: false (token in header, not cookie)

### Rate Limiting
- **Library**: Flask-Limiter
- **Applied to**: API endpoints (configurable per endpoint)
- **Purpose**: Prevent abuse, brute force attacks

---

## 13. DATABASE PERSISTENCE VERIFICATION

### Query Examples

**Count all paintings:**
```python
from app.models import Painting
count = Painting.query.count()
print(f"Total paintings: {count}")
```

**Get paintings by user:**
```python
from app.models import User, Painting
user = User.query.filter_by(username='jane').first()
paintings = user.paintings if user else []
for p in paintings:
    print(f"{p.title} → {p.filename}")
```

**Check file paths:**
```python
from app.models import Painting
for p in Painting.query.all():
    print(f"ID: {p.id}")
    print(f"  Image: /app/images/{p.filename}")
    print(f"  Thumb: /app/images/{p.thumbnail}")
    print(f"  Public: {p.is_public}")
```

**List all users:**
```python
from app.models import User
users = User.query.all()
for u in users:
    print(f"{u.id}: {u.username} ({u.email}) - {len(u.paintings)} paintings")
```

---

## 14. SUMMARY

**What's Working:**
✅ User registration with secure password hashing
✅ User login with token generation
✅ Token-based authentication for all API requests
✅ Image upload with automatic thumbnail generation
✅ Images stored in organized directory structure (user/folder/prefix_name)
✅ Image metadata persisted in database
✅ Gallery displays user's paintings with thumbnails
✅ Public/private visibility toggle
✅ Docker named volumes ensure persistence across container restarts
✅ nginx reverse proxy routes requests correctly
✅ All endpoints tested and working

**File Locations (In Container):**
- Database: `/app/db/app.db`
- Images: `/app/images/{username}/{folder}/{prefix}_{name}.{ext}`
- Thumbnails: `/app/images/{username}/{folder}/{prefix}_{name}_thumb.jpg`
- Backend: `/app/`
- Frontend: `/app/frontend/`

**Key URLs:**
- Register/Login: `http://localhost:5173` → AuthPanel
- Editor: `http://localhost:5173/editor`
- Gallery: `http://localhost:5173/gallery`
- Serve Image: `http://localhost:5173/media/images/{path}`
- List Paintings: `http://localhost:5173/api/paintings?user_id={id}`
- Upload: `http://localhost:5173/api/paintings` (POST with Bearer token)

