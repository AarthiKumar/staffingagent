# Digital Ocean App Platform - Manual Setup Guide

Since Digital Ocean can't auto-detect the components, follow these steps to manually configure your app.

## Step-by-Step Setup

### 1. Connect to GitHub

1. Go to https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Choose **"GitHub"** as source
4. Authorize Digital Ocean to access your GitHub
5. Select repository: **`AarthiKumar/staffingagent`**
6. Select branch: **`main`** (or your deployment branch)
7. Click **"Next"**

### 2. Configure Backend Service

When you see "No components detected", click **"Edit Plan"** → **"Add Resource"** → **"Web Service"**

**Service Settings:**
- **Name**: `backend`
- **Source Directory**: `/backend`
- **Environment**: Python
- **Build Command**: (leave empty - uses requirements.txt)
- **Run Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- **HTTP Port**: `8080`
- **HTTP Routes**: (leave default `/`)

**Instance Settings:**
- **Instance Size**: Basic ($5/month)
- **Instance Count**: 1

Click **"Save"**

### 3. Configure Frontend Service

Click **"Add Resource"** → **"Static Site"**

**Service Settings:**
- **Name**: `frontend`
- **Source Directory**: `/frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

**Instance Settings:**
- **Instance Size**: Basic ($5/month)

Click **"Save"**

### 4. Add Database

Click **"Add Resource"** → **"Database"**

**Database Settings:**
- **Name**: `db`
- **Engine**: PostgreSQL
- **Version**: 15
- **Cluster Size**: Basic ($15/month)

Click **"Save"**

### 5. Configure Environment Variables

#### Backend Environment Variables

Click on **"backend"** → **"Environment Variables"** → **"Edit"**

Add these variables:

```
# Database (auto-populated when you bind database)
DATABASE_URL = ${db.DATABASE_URL}

# Auth0
AUTH0_ENABLED = true
AUTH0_DOMAIN = your-prod-tenant.auth0.com
AUTH0_CLIENT_ID = your_client_id_here
AUTH0_CLIENT_SECRET = your_client_secret_here (mark as SECRET)
AUTH0_AUDIENCE = https://api.staffingagent.com

# App Config
CORS_ORIGINS = ${frontend.PUBLIC_URL}

# Embeddings
EMBEDDINGS_PROVIDER = sentence_transformers
EMBEDDINGS_MODEL = all-MiniLM-L6-v2
```

**Important**: For `AUTH0_CLIENT_SECRET`, check the **"Encrypt"** checkbox to mark it as a secret!

#### Frontend Environment Variables

Click on **"frontend"** → **"Environment Variables"** → **"Edit"**

Add these variables (these are **BUILD TIME** variables):

```
VITE_API_URL = ${backend.PUBLIC_URL}/api/v1
VITE_AUTH0_ENABLED = true
VITE_AUTH0_DOMAIN = your-prod-tenant.auth0.com
VITE_AUTH0_CLIENT_ID = your_client_id_here
VITE_AUTH0_AUDIENCE = https://api.staffingagent.com
VITE_AUTH0_REDIRECT_URI = ${frontend.PUBLIC_URL}/callback
```

### 6. Bind Database to Backend

1. Go to **backend** service settings
2. Scroll to **"Database"** section
3. Click **"Attach Database"**
4. Select your `db` database
5. This will automatically add `${db.DATABASE_URL}` variable

### 7. Review Configuration

Your app should now have:
- ✅ Backend service (Python)
- ✅ Frontend static site (Node.js)
- ✅ PostgreSQL database
- ✅ All environment variables set
- ✅ Database attached to backend

### 8. Deploy!

Click **"Create Resources"** at the bottom

**Wait 5-10 minutes** for the first deployment. You can watch the logs:
- Click on your app
- Click on **"backend"** or **"frontend"**
- View the **"Build Logs"** and **"Runtime Logs"**

### 9. Run Database Migrations

After the first successful deployment:

**Option A: From your local machine**
```bash
# Get the database connection string from Digital Ocean
# Apps → Your App → db → Connection Details

# Run migrations
cd backend
DATABASE_URL="postgresql://..." alembic upgrade head
```

**Option B: Using Digital Ocean Console**
1. Go to your app → **backend** service
2. Click **"Console"** tab
3. Click **"Open Console"**
4. Run:
   ```bash
   cd /workspace
   alembic upgrade head
   exit
   ```

### 10. Update Auth0

Go to your Auth0 production tenant and update:

**Allowed Callback URLs:**
```
https://your-app-name.ondigitalocean.app/callback
```

**Allowed Logout URLs:**
```
https://your-app-name.ondigitalocean.app
```

**Allowed Web Origins:**
```
https://your-app-name.ondigitalocean.app
```

Replace `your-app-name` with your actual app URL from Digital Ocean.

### 11. Test Your App

1. Open your frontend URL (shown in Digital Ocean)
2. Click "Log In"
3. Should redirect to Auth0
4. Log in with your test user
5. Should redirect back to your app
6. User menu should show your name and role ✅

---

## Alternative: Use App Spec File

If you want to use the spec file approach:

### 1. Commit the spec file

```bash
cd staffingagent
git add .do/app.yaml
git commit -m "Add Digital Ocean App Platform spec"
git push origin main
```

### 2. Create app from spec

1. Go to https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Choose **"GitHub"**
4. Select your repository
5. Select branch
6. **IMPORTANT**: Click **"Edit your app spec"** (blue link at top)
7. Paste the contents of `.do/app.yaml`
8. Update the environment variables with your actual values
9. Click **"Save"**
10. Click **"Create Resources"**

---

## Troubleshooting

### Error: "No package.json found"

**Solution:** Make sure **Source Directory** is set to `/frontend` for frontend and `/backend` for backend.

### Error: "Build failed - requirements.txt not found"

**Solution:** For backend, make sure **Source Directory** is `/backend` (with leading slash).

### Error: "Module not found: app.main"

**Solution:**
- Check **Run Command** is: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- Check **Source Directory** is `/backend`

### Frontend shows blank page

**Solution:**
- Check **Output Directory** is set to `dist`
- Check build logs for errors
- Verify environment variables are set

### Backend returns 500 error

**Solution:**
- Check runtime logs for errors
- Verify `DATABASE_URL` is set correctly
- Make sure migrations were run
- Check Auth0 environment variables are correct

### Database connection failed

**Solution:**
- Verify database is attached to backend service
- Check `${db.DATABASE_URL}` is in backend environment variables
- Make sure database is fully provisioned (green status)

---

## Cost Breakdown

After setup, your monthly costs will be:

```
Backend (Basic):     $5/month
Frontend (Basic):    $5/month
Database (Basic):   $15/month
─────────────────────────────
Total:             ~$25/month
```

You can upgrade or downgrade at any time!

---

## Next Steps

1. ✅ Set up custom domain (optional)
2. ✅ Enable alerts and monitoring
3. ✅ Set up automated backups (enabled by default for database)
4. ✅ Configure production Auth0 tenant
5. ✅ Test with all user roles

See `DIGITALOCEAN_DEPLOYMENT.md` for more details!
