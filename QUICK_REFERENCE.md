# 🎨 Canvas3T - Quick Reference Guide

## ✅ Current Status
**ALL SYSTEMS OPERATIONAL** - Ready for use!

## 🚀 Start Application
```bash
cd c:\Users\Yashv\Downloads\Projects\Backend\Python_Flask
docker compose up -d
```

## 🌐 Access Points
- **Frontend App**: http://localhost:5173
- **Backend API**: http://localhost:5000  
- **API Docs**: Try endpoints below

## 📋 Key API Endpoints

### Authentication
```bash
# Register
POST /api/auth/register
{ "username": "user", "email": "user@test.com", "password": "Pass123!" }

# Login  
POST /api/auth/login
{ "username": "user", "password": "Pass123!" }
```

### Paintings
```bash
# List public paintings
GET /api/paintings

# List user's paintings (requires auth)
GET /api/paintings?user_id=1
Header: Authorization: Bearer {token}

# Upload image (requires auth)
POST /api/paintings
Form: image, title, is_public, tags
Header: Authorization: Bearer {token}

# Import from URL (requires auth)
POST /api/paintings/import-url
{ "image_url": "https://...", "title": "...", "is_public": true }
Header: Authorization: Bearer {token}
```

### Media
```bash
# Download image
GET /media/images/{path}
```

## 🗂️ File Structure

**Images Storage**:
- Private: `/app/images/{username}/`
- Public: `/app/images/public/`
- Database: `/app/db/app.db`

**All data persists across container restarts** ✅

## 🧪 Quick Test

```bash
# 1. Register & get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"Pass123!"}' \
  | jq -r '.token')

# 2. Check your gallery
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/paintings?user_id=1 | jq .

# 3. View public gallery
curl -s http://localhost:5000/api/paintings | jq .
```

## 🎯 Features

### ✅ Working Features
- User registration & login with secure tokens
- Image upload (file or from URL)
- Public/private visibility toggle
- Gallery view with filtering
- Download links
- Username attribution
- Canvas drawing with tools
- Database persistence
- File storage persistence

### 🟡 In Development
- WASM editor advanced UI (zoom, brush presets)

## 🛠️ Troubleshooting

### API returns 404
- Check blueprints are registered in `backend/app/__init__.py`
- Verify endpoint decorator matches URL prefix

### Images not saving
- Check `/app/images` directory exists in container
- Check file permissions in container
- View logs: `docker logs canvas3t_api`

### Database errors
- Reset database: `docker volume rm python_flask_canvas3t_db`
- Rebuild: `docker compose up -d --build`

### Authentication issues
- Verify token in Authorization header: `Bearer {token}`
- Check SECRET_KEY in docker-compose.yml is consistent
- Tokens expire in 7 days

## 📊 Database Schema

**Users**: id, username, email, password_hash, created_at

**Paintings**: id, user_id, title, filename, is_public, tags, thumbnail, source_url, width, height, format, created_at, updated_at

## 🔐 Security Notes
- Passwords: PBKDF2-SHA256 hashed
- Tokens: Signed with SECRET_KEY, 7-day expiration  
- Private images: Only owner can access via API
- CORS: Enabled for development (change for production)

## 📞 Container Commands

```bash
# View logs
docker logs canvas3t_api
docker logs canvas3t_frontend

# Restart
docker restart canvas3t_api
docker restart canvas3t_frontend

# Shell access
docker exec -it canvas3t_api bash
docker exec -it canvas3t_frontend sh

# Check database
docker exec canvas3t_api sqlite3 /app/db/app.db ".tables"
```

## 📝 Notes

- All timestamps in ISO 8601 format
- Image URLs: `/media/images/{relative_path}`
- Thumbnail URLs: `{image_url}_thumb.jpg`
- Pagination: 24 items per page by default
- Response format: JSON with `{ data, status_code }`

---

**Ready to use!** Open http://localhost:5173 in your browser 🎨
