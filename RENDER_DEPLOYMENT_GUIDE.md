# Render Deployment Setup Guide for CleanSpeak Backend

## Step 1: Prepare Your Repository

### Create necessary files:
- `render.yaml` ✅ (Created)
- `backend/start.sh` ✅ (Created)

### Ensure `.gitignore` includes:
```
backend/temp/
backend/__pycache__
*.pyc
.env
.env.local
```

## Step 2: Update CORS for Production

Your frontend will be hosted on Vercel. Update the CORS settings in `backend/main.py`:

Replace:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

With:
```python
import os

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", "https://yourdomain.vercel.app"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 3: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. **Create a Render account** at https://render.com
2. **Connect your GitHub repository**
   - Go to https://dashboard.render.com
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub account and select your repository
3. **Configure the service:**
   - **Name:** cleanspeak-backend
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** 3.11

### Option B: Manual Setup (If render.yaml doesn't work)

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Select your GitHub repository
4. Fill in these settings:
   - **Name:** cleanspeak-backend
   - **Environment:** Python
   - **Region:** Oregon (or your preferred region)
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or Starter)

## Step 4: Environment Variables

In Render Dashboard:
1. Go to your service → "Environment"
2. Add these environment variables:
   - **FRONTEND_URL:** `https://yourfrontend.vercel.app` (your Vercel frontend URL)
   - **PORT:** `8000` (Render sets this automatically, but you can override)

## Step 5: Storage Considerations ⚠️

**Important:** Render's free tier has **ephemeral storage** - files are deleted after service restart.

### Solutions:

#### Option 1: Use AWS S3 (Recommended for production)
1. Create AWS S3 bucket
2. Install: `pip install boto3`
3. Update `requirements.txt`
4. Modify `main.py` to upload/download from S3
5. Add AWS credentials as environment variables

#### Option 2: Use Cloudinary (Easy for audio)
1. Create Cloudinary account (free tier available)
2. Install: `pip install cloudinary`
3. Add to `requirements.txt`
4. Update `main.py` to use Cloudinary
5. Add CLOUDINARY_URL to Render environment variables

#### Option 3: Keep local storage (Works for small files)
- Files persist between deploys (but not after container restarts)
- Suitable for development/small usage

## Step 6: Connect Frontend to Backend

Update your frontend API calls to use the Render URL:

In `src/integrations/supabase/client.ts` or your API service:
```typescript
const API_URL = process.env.VITE_API_URL || "http://localhost:8000";
```

Add to `.env.local` (frontend):
```
VITE_API_URL=https://cleanspeak-backend.onrender.com
```

Add to `.env.production` (frontend):
```
VITE_API_URL=https://cleanspeak-backend.onrender.com
```

## Step 7: Deploy

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push
   ```

2. **Render will automatically deploy** when you push to your main branch

3. **Monitor deployment** in Render Dashboard → Logs

## Troubleshooting

### Deployment fails with "module not found"
- Check `requirements.txt` has all dependencies
- Make sure build command is correct

### 502 Bad Gateway
- Check logs in Render dashboard
- Ensure start command is using `$PORT` variable
- Check CORS settings

### Files not persisting
- This is expected behavior on Render free tier
- Implement S3 or Cloudinary storage (see Step 5)

### CORS errors
- Verify `FRONTEND_URL` environment variable is set correctly
- Check that frontend URL is in `ALLOWED_ORIGINS`

## Monitoring

View logs and metrics:
1. Go to your service in Render Dashboard
2. Click "Logs" to see real-time logs
3. Check "Metrics" for CPU, memory usage

## Next Steps

1. Update requirements.txt if needed for production dependencies
2. Test API connectivity from your Vercel frontend
3. Consider implementing S3/Cloudinary for file storage
4. Set up environment-specific CORS rules
