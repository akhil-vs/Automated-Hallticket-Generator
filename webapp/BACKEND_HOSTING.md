# Backend Hosting Options for Flask API

Since your frontend is deployed on Vercel, here are the best options for deploying your Flask backend separately.

## Recommended Options

### 1. **Railway** ⭐ (Recommended - Easiest)
**Best for**: Quick deployment, automatic HTTPS, generous free tier

**Pros:**
- Very easy deployment (connects to GitHub)
- Automatic HTTPS/SSL
- Free tier: $5 credit/month
- Built-in PostgreSQL (if needed later)
- Simple environment variable management

**Deployment:**
```bash
# Option 1: Connect GitHub repo
1. Go to railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects Dockerfile.backend
5. Set environment variables:
   - FLASK_ENV=production
   - PYTHONPATH=/app
6. Deploy!

# Option 2: Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

**Cost**: Free tier available, then ~$5-20/month

---

### 2. **Render** ⭐ (Great Alternative)
**Best for**: Simple deployment, good free tier

**Pros:**
- Free tier available (spins down after inactivity)
- Automatic HTTPS
- Easy GitHub integration
- Good documentation

**Deployment:**
1. Go to render.com
2. New → Web Service
3. Connect GitHub repo
4. Settings:
   - Build Command: `cd webapp && docker build -f Dockerfile.backend -t backend ..`
   - Start Command: `gunicorn -c webapp/backend/gunicorn_config.py webapp.backend.app:app`
   - Environment: `FLASK_ENV=production`, `PYTHONPATH=/app`

**Cost**: Free tier (with limitations), then $7/month

---

### 3. **Fly.io** ⭐ (Great for Global)
**Best for**: Global edge deployment, Docker-native

**Pros:**
- Deploy Docker containers easily
- Global edge network
- Good free tier
- Great for APIs

**Deployment:**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# From project root
cd webapp
fly launch --dockerfile Dockerfile.backend

# Set environment variables
fly secrets set FLASK_ENV=production PYTHONPATH=/app

# Deploy
fly deploy
```

**Cost**: Free tier available, then pay-as-you-go

---

### 4. **DigitalOcean App Platform**
**Best for**: Simple, reliable hosting

**Pros:**
- Simple deployment
- Automatic HTTPS
- Good pricing
- Reliable infrastructure

**Deployment:**
1. Go to cloud.digitalocean.com
2. Create App → GitHub
3. Select repository
4. Configure:
   - Build: Dockerfile.backend
   - Run: `gunicorn -c backend/gunicorn_config.py backend.app:app`

**Cost**: ~$5-12/month

---

### 5. **Google Cloud Run** (Serverless)
**Best for**: Pay-per-use, auto-scaling

**Pros:**
- Pay only for requests
- Auto-scaling
- Global deployment
- Good for variable traffic

**Deployment:**
```bash
# Install gcloud CLI
# Build and push
cd webapp
gcloud builds submit --tag gcr.io/YOUR_PROJECT/hallticket-backend

# Deploy
gcloud run deploy hallticket-backend \
  --image gcr.io/YOUR_PROJECT/hallticket-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Cost**: Pay-per-use, very cheap for low traffic

---

### 6. **AWS (Elastic Beanstalk or ECS)**
**Best for**: Enterprise, AWS ecosystem

**Pros:**
- Highly scalable
- Integrates with AWS services
- Production-ready

**Cons:**
- More complex setup
- Can be expensive

---

## Quick Comparison

| Platform | Free Tier | Ease | Cost (Paid) | Best For |
|----------|-----------|------|-------------|----------|
| **Railway** | ✅ $5/mo credit | ⭐⭐⭐⭐⭐ | $5-20/mo | Quick start |
| **Render** | ✅ (limited) | ⭐⭐⭐⭐ | $7/mo | Simple setup |
| **Fly.io** | ✅ | ⭐⭐⭐⭐ | Pay-as-you-go | Global edge |
| **DigitalOcean** | ❌ | ⭐⭐⭐⭐ | $5-12/mo | Reliability |
| **Cloud Run** | ✅ | ⭐⭐⭐ | Pay-per-use | Variable traffic |

## Recommended Setup: Railway

Here's a step-by-step for Railway (easiest option):

### Step 1: Prepare Your Repo
Make sure your `Dockerfile.backend` is in `webapp/` directory.

### Step 2: Deploy on Railway

1. **Sign up**: Go to [railway.app](https://railway.app)
2. **New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repo**: Choose your `AutomatedHallticketGenerator` repository
4. **Configure**:
   - Railway will auto-detect the Dockerfile
   - If not, set root directory to `webapp/`
   - Dockerfile path: `Dockerfile.backend`
5. **Environment Variables**:
   ```
   FLASK_ENV=production
   PYTHONPATH=/app
   ```
6. **Deploy**: Click "Deploy"

### Step 3: Get Your Backend URL

Railway will provide a URL like: `https://your-app.railway.app`

### Step 4: Update Frontend on Vercel

1. Go to your Vercel project settings
2. Add environment variable:
   ```
   VITE_API_URL=https://your-app.railway.app
   ```
3. Redeploy your frontend

### Step 5: Update CORS in Backend

In `webapp/backend/app.py`, update CORS:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-vercel-app.vercel.app",
            "https://your-custom-domain.com"
        ],
        "methods": ["GET", "POST", "DELETE", "OPTIONS", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
}, supports_credentials=True)
```

## Alternative: Render Deployment

### Step 1: Create Web Service
1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect GitHub repository

### Step 2: Configure
- **Name**: `hallticket-backend`
- **Environment**: `Docker`
- **Dockerfile Path**: `webapp/Dockerfile.backend`
- **Docker Context**: `webapp/`

### Step 3: Environment Variables
```
FLASK_ENV=production
PYTHONPATH=/app
```

### Step 4: Deploy
Click "Create Web Service"

## Important Notes

### 1. Update Frontend API URL
After deploying backend, update your Vercel environment variable:
```
VITE_API_URL=https://your-backend-url.com
```
Then rebuild/redeploy frontend.

### 2. CORS Configuration
Make sure your backend allows requests from your Vercel domain:
- `https://your-app.vercel.app`
- Your custom domain (if any)

### 3. Health Check
Test your backend:
```bash
curl https://your-backend-url.com/api/health
```

### 4. File Upload Limits
Some platforms have file size limits. Check:
- Railway: 100MB
- Render: 100MB
- Fly.io: Configurable

## Troubleshooting

### Backend not accessible
- Check CORS settings
- Verify environment variables
- Check platform logs

### Frontend can't connect
- Verify `VITE_API_URL` is set correctly
- Rebuild frontend after changing env var
- Check browser console for CORS errors

### Build fails
- Check Dockerfile path
- Verify all dependencies in requirements.txt
- Check platform build logs

## My Recommendation

**Start with Railway** - it's the easiest and has a good free tier. If you need more control or global distribution later, consider Fly.io or Cloud Run.
