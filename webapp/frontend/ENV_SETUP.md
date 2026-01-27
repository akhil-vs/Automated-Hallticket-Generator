# Environment Configuration Guide

## How the API URL Configuration Works

### Local Development
- **No configuration needed!** The Vite dev server proxy automatically forwards `/api` requests to `http://localhost:5001`
- Just make sure your backend is running on `http://localhost:5001`
- Run: `npm run dev`

### Production Build
- Create a `.env.production` file in the frontend directory with:
  ```
  VITE_API_URL=https://vsakhilvs.pythonanywhere.com
  ```
- Then build: `npm run build`
- The built app will use the PythonAnywhere URL directly

## How It Works

1. **Development Mode** (`npm run dev`):
   - Vite proxy intercepts requests to `/api/*`
   - Forwards them to `http://localhost:5001`
   - No CORS issues because proxy handles it

2. **Production Mode** (`npm run build`):
   - Proxy doesn't work (it's dev-only)
   - App uses `VITE_API_URL` environment variable
   - If not set, uses relative URLs (won't work for cross-origin)

## Quick Setup

### For Local Development:
```bash
# No .env file needed - proxy handles everything
npm run dev
```

### For Production Build:
```bash
# Create .env.production file
echo "VITE_API_URL=https://vsakhilvs.pythonanywhere.com" > .env.production

# Build
npm run build
```
