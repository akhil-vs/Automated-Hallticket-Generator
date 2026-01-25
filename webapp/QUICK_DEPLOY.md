# Quick Deployment Guide: Backend to Railway + Frontend on Vercel

## Prerequisites
- GitHub repository with your code
- Vercel account (frontend already deployed)
- Railway account (free signup)

## Step 1: Deploy Backend to Railway (5 minutes)

### Option A: Via Railway Dashboard

1. **Sign up/Login**: Go to [railway.app](https://railway.app) and sign in with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `AutomatedHallticketGenerator` repository

3. **Configure Service**:
   - Railway will auto-detect Docker
   - If not, click "Add Service" → "Docker"
   - Set **Root Directory**: `webapp`
   - Set **Dockerfile Path**: `Dockerfile.backend`

4. **Set Environment Variables**:
   Click on your service → Variables tab, add:
   ```
   FLASK_ENV=production
   PYTHONPATH=/app
   CORS_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
   ```
   (Replace with your actual Vercel URLs)

5. **Deploy**:
   - Railway will automatically build and deploy
   - Wait for "Deploy Successful"

6. **Get Your Backend URL**:
   - Click on your service
   - Go to "Settings" → "Generate Domain"
   - Copy the URL (e.g., `https://hallticket-backend.railway.app`)

### Option B: Via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set FLASK_ENV=production
railway variables set PYTHONPATH=/app
railway variables set CORS_ORIGINS=https://your-vercel-app.vercel.app

# Deploy
railway up
```

## Step 2: Update Frontend on Vercel

1. **Go to Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)

2. **Select Your Project**

3. **Add Environment Variable**:
   - Go to Settings → Environment Variables
   - Add new variable:
     - **Name**: `VITE_API_URL`
     - **Value**: `https://your-railway-app.railway.app` (your Railway URL)
     - **Environment**: Production, Preview, Development (check all)

4. **Redeploy**:
   - Go to Deployments tab
   - Click "..." on latest deployment → "Redeploy"
   - Or push a new commit to trigger redeploy

## Step 3: Test Your Setup

1. **Test Backend**:
   ```bash
   curl https://your-railway-app.railway.app/api/health
   ```
   Should return: `{"status": "ok"}`

2. **Test Frontend**:
   - Visit your Vercel URL
   - Try uploading files and generating hall tickets
   - Check browser console for errors

## Step 4: Custom Domain (Optional)

### Railway (Backend)
1. Go to Railway service → Settings
2. Click "Generate Domain" or add custom domain
3. Update `CORS_ORIGINS` environment variable with new domain

### Vercel (Frontend)
1. Go to Vercel project → Settings → Domains
2. Add your custom domain
3. Update `VITE_API_URL` if backend also has custom domain

## Troubleshooting

### CORS Errors
- Make sure `CORS_ORIGINS` includes your Vercel URL
- Format: `https://app.vercel.app,https://custom.com` (comma-separated, no spaces in URLs)
- Redeploy backend after changing CORS_ORIGINS

### Frontend Can't Connect
- Verify `VITE_API_URL` is set in Vercel
- **Important**: Rebuild frontend after adding env var (Vite needs it at build time)
- Check browser Network tab for actual API calls

### Backend Build Fails
- Check Railway logs
- Verify Dockerfile.backend exists in `webapp/` directory
- Ensure all dependencies are in `requirements.txt`

## Cost Estimate

- **Railway**: Free tier ($5 credit/month), then ~$5-20/month
- **Vercel**: Free tier (generous), then $20/month for Pro
- **Total**: Free for small projects, ~$25/month for production

## Alternative Platforms

If Railway doesn't work for you:

1. **Render**: [render.com](https://render.com) - Similar to Railway
2. **Fly.io**: [fly.io](https://fly.io) - Great for global deployment
3. **DigitalOcean App Platform**: ~$5/month

See [BACKEND_HOSTING.md](./BACKEND_HOSTING.md) for detailed comparison.

## Next Steps

- Set up monitoring (Railway has built-in logs)
- Configure custom domains
- Set up CI/CD (Railway auto-deploys on git push)
- Add database if needed (Railway offers PostgreSQL)
