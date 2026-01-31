# Deploying Staffing Agent to Digital Ocean

This guide walks you through deploying the Staffing Agent application to Digital Ocean with Auth0 authentication.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Prerequisites](#prerequisites)
3. [Option A: App Platform (Recommended)](#option-a-app-platform-recommended)
4. [Option B: Droplet with Docker](#option-b-droplet-with-docker)
5. [Database Setup](#database-setup)
6. [Auth0 Production Configuration](#auth0-production-configuration)
7. [Domain and SSL Setup](#domain-and-ssl-setup)
8. [Testing](#testing)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Deployment Options

### Option A: App Platform (Recommended) ⭐
- **Pros**: Easy setup, automatic SSL, auto-scaling, managed infrastructure
- **Cons**: Higher cost (~$12-25/month per service)
- **Best for**: Production apps, teams without DevOps expertise

### Option B: Droplet with Docker
- **Pros**: Lower cost (~$6-12/month), full control
- **Cons**: Requires more setup and maintenance
- **Best for**: Cost-sensitive projects, developers comfortable with Linux

---

## Prerequisites

### Required Accounts
- [ ] Digital Ocean account (get $200 credit: https://m.do.co/c/yourreferralcode)
- [ ] Domain name (optional but recommended)
- [ ] Auth0 account with production tenant

### Required Tools
- [ ] Git
- [ ] Digital Ocean CLI (`doctl`) - optional but helpful

### Install Digital Ocean CLI (Optional)

```bash
# macOS
brew install doctl

# Windows (PowerShell as Admin)
choco install doctl

# Linux
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.98.0/doctl-1.98.0-linux-amd64.tar.gz
tar xf ~/doctl-1.98.0-linux-amd64.tar.gz
sudo mv ~/doctl /usr/local/bin
```

Authenticate:
```bash
doctl auth init
```

---

## Option A: App Platform (Recommended)

### Step 1: Prepare Your Repository

Your code is already on GitHub. Make sure you're on the main branch or your deployment branch.

```bash
# Verify your code is pushed
git status
git push origin main
```

### Step 2: Create PostgreSQL Database

1. **Go to** Digital Ocean Dashboard → Databases → Create Database Cluster
2. **Select**:
   - Database engine: PostgreSQL 15
   - Datacenter: Choose closest to your users (e.g., NYC, SFO, LON)
   - Plan: Basic ($15/month for 1GB RAM, 10GB disk)
3. **Configure**:
   - Name: `staffing-agent-db`
   - Enable VPC: Yes (for security)
4. **Create Database Cluster**
5. **Wait** 3-5 minutes for provisioning

**After creation:**
1. Go to the database cluster → **Settings** → **Trusted Sources**
2. Add your App Platform app (you'll do this after creating the app)
3. Note the connection string - you'll need it!

### Step 3: Create Backend App

1. **Go to** Digital Ocean Dashboard → Apps → Create App
2. **Source**: Connect to GitHub
   - Authorize Digital Ocean
   - Select your repository
   - Select branch: `main` (or your deployment branch)
3. **Resources**:
   - Click "Edit" on the automatically detected services
   - **Service Name**: `backend`
   - **Source Directory**: `/backend`
   - **Build Command**: (leave default or empty)
   - **Run Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
   - **HTTP Port**: 8080
   - **Instance Size**: Basic (512 MB RAM, $5/month)
   - **Instance Count**: 1

4. **Environment Variables**:
   Click "Edit" → Environment Variables → Add the following:

   ```bash
   # Database (get from your DB cluster connection details)
   DATABASE_URL=${db.DATABASE_URL}

   # Auth0 (from your Auth0 production tenant)
   AUTH0_ENABLED=true
   AUTH0_DOMAIN=your-prod-tenant.auth0.com
   AUTH0_CLIENT_ID=your_prod_client_id
   AUTH0_CLIENT_SECRET=${AUTH0_CLIENT_SECRET}  # Add as secret
   AUTH0_AUDIENCE=https://api.staffingagent.com
   AUTH0_CALLBACK_URL=https://staffingagent.com/callback

   # App Settings
   APP_NAME=Staffing Agent
   CORS_ORIGINS=https://staffingagent.com,https://www.staffingagent.com

   # Embeddings
   EMBEDDINGS_PROVIDER=sentence_transformers
   EMBEDDINGS_MODEL=all-MiniLM-L6-v2

   # MinIO (use Digital Ocean Spaces instead)
   MINIO_ENABLED=false
   ```

5. **Database Connection**:
   - In Environment Variables, click "Bind Database"
   - Select your `staffing-agent-db`
   - This automatically adds `${db.DATABASE_URL}`

6. **Review and Create**

### Step 4: Create Frontend App

1. **In the same App**, click "Add Component" → Web Service
2. **Configure**:
   - **Service Name**: `frontend`
   - **Source Directory**: `/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Instance Size**: Basic (512 MB RAM, $5/month)

3. **Environment Variables**:

   ```bash
   VITE_API_URL=https://backend-xxxxx.ondigitalocean.app/api/v1
   VITE_AUTH0_ENABLED=true
   VITE_AUTH0_DOMAIN=your-prod-tenant.auth0.com
   VITE_AUTH0_CLIENT_ID=your_prod_client_id
   VITE_AUTH0_AUDIENCE=https://api.staffingagent.com
   VITE_AUTH0_REDIRECT_URI=https://staffingagent.com/callback
   ```

   **Note**: Replace `backend-xxxxx.ondigitalocean.app` with your actual backend URL after it's created.

4. **Click** "Save"

### Step 5: Configure Domains

After deployment:

1. **Backend**:
   - Go to Settings → Domains
   - Add custom domain: `api.staffingagent.com`
   - Update DNS (see [Domain Setup](#domain-and-ssl-setup))

2. **Frontend**:
   - Go to Settings → Domains
   - Add custom domain: `staffingagent.com` and `www.staffingagent.com`
   - Update DNS

### Step 6: Run Database Migrations

**Option 1: From your local machine**
```bash
# Get database connection string from Digital Ocean
DATABASE_URL="postgresql://user:pass@host:25060/dbname?sslmode=require"

# Run migrations
cd backend
DATABASE_URL=$DATABASE_URL alembic upgrade head
```

**Option 2: Using Digital Ocean console**
1. Go to App → backend → Console
2. Run:
   ```bash
   cd /workspace
   alembic upgrade head
   ```

### Step 7: Update Auth0

See [Auth0 Production Configuration](#auth0-production-configuration) section below.

### Step 8: Deploy!

1. Click "Create Resources" or "Deploy"
2. Wait 5-10 minutes for build and deployment
3. Check deployment logs for any errors

**Your app is now live!** 🎉

---

## Option B: Droplet with Docker

### Step 1: Create Droplet

1. **Go to** Digital Ocean → Create → Droplets
2. **Choose**:
   - Image: Ubuntu 22.04 LTS
   - Plan: Basic ($6/month - 1GB RAM, 25GB SSD)
   - Datacenter: Closest to your users
   - Authentication: SSH key (recommended) or Password
   - Hostname: `staffing-agent`
3. **Create Droplet**

### Step 2: Initial Server Setup

SSH into your droplet:
```bash
ssh root@your_droplet_ip
```

**Update system and install dependencies:**
```bash
# Update packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Install Git
apt install git -y

# Create app user
adduser --disabled-password --gecos "" appuser
usermod -aG docker appuser
```

### Step 3: Clone Repository

```bash
# Switch to app user
su - appuser

# Clone repository
git clone https://github.com/yourusername/staffingagent.git
cd staffingagent
```

### Step 4: Create Production Docker Compose

Create `docker-compose.prod.yml`:

```bash
nano docker-compose.prod.yml
```

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: staffing-postgres-prod
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-staffing}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/app/db/init_pgvector.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: staffing-backend-prod
    environment:
      DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-staffing}
      AUTH0_ENABLED: ${AUTH0_ENABLED}
      AUTH0_DOMAIN: ${AUTH0_DOMAIN}
      AUTH0_CLIENT_ID: ${AUTH0_CLIENT_ID}
      AUTH0_CLIENT_SECRET: ${AUTH0_CLIENT_SECRET}
      AUTH0_AUDIENCE: ${AUTH0_AUDIENCE}
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: ${VITE_API_URL}
        VITE_AUTH0_ENABLED: ${VITE_AUTH0_ENABLED}
        VITE_AUTH0_DOMAIN: ${VITE_AUTH0_DOMAIN}
        VITE_AUTH0_CLIENT_ID: ${VITE_AUTH0_CLIENT_ID}
        VITE_AUTH0_AUDIENCE: ${VITE_AUTH0_AUDIENCE}
        VITE_AUTH0_REDIRECT_URI: ${VITE_AUTH0_REDIRECT_URI}
    container_name: staffing-frontend-prod
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### Step 5: Create Backend Dockerfile

Create `backend/Dockerfile`:

```bash
nano backend/Dockerfile
```

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations on startup (optional, can be done manually)
# RUN alembic upgrade head

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 6: Create Frontend Dockerfile

Create `frontend/Dockerfile`:

```bash
nano frontend/Dockerfile
```

```dockerfile
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build arguments for env variables
ARG VITE_API_URL
ARG VITE_AUTH0_ENABLED
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_AUTH0_AUDIENCE
ARG VITE_AUTH0_REDIRECT_URI

# Set env variables
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_AUTH0_ENABLED=$VITE_AUTH0_ENABLED
ENV VITE_AUTH0_DOMAIN=$VITE_AUTH0_DOMAIN
ENV VITE_AUTH0_CLIENT_ID=$VITE_AUTH0_CLIENT_ID
ENV VITE_AUTH0_AUDIENCE=$VITE_AUTH0_AUDIENCE
ENV VITE_AUTH0_REDIRECT_URI=$VITE_AUTH0_REDIRECT_URI

# Build app
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Step 7: Create Nginx Configuration

Create `frontend/nginx.conf`:

```bash
nano frontend/nginx.conf
```

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Step 8: Create Environment File

Create `.env.prod`:

```bash
nano .env.prod
```

```bash
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=staffing

# Auth0
AUTH0_ENABLED=true
AUTH0_DOMAIN=your-prod-tenant.auth0.com
AUTH0_CLIENT_ID=your_prod_client_id
AUTH0_CLIENT_SECRET=your_prod_client_secret
AUTH0_AUDIENCE=https://api.staffingagent.com

# Backend
CORS_ORIGINS=https://staffingagent.com,https://www.staffingagent.com

# Frontend
VITE_API_URL=https://api.staffingagent.com/api/v1
VITE_AUTH0_ENABLED=true
VITE_AUTH0_DOMAIN=your-prod-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your_prod_client_id
VITE_AUTH0_AUDIENCE=https://api.staffingagent.com
VITE_AUTH0_REDIRECT_URI=https://staffingagent.com/callback
```

### Step 9: Deploy with Docker Compose

```bash
# Build and start services
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 10: Setup SSL with Let's Encrypt

Install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
```

Get SSL certificate:
```bash
sudo certbot --nginx -d staffingagent.com -d www.staffingagent.com -d api.staffingagent.com
```

Auto-renewal:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Database Setup

### Option 1: Digital Ocean Managed Database (Recommended)

**Advantages:**
- Automatic backups
- High availability
- Automatic updates
- Point-in-time recovery

**Pricing:** Starts at $15/month

**Setup:**
1. Create database cluster (see App Platform Step 2)
2. Enable backups (automatic)
3. Configure firewall rules
4. Use connection pooling

### Option 2: Self-Hosted on Droplet

**Advantages:**
- Lower cost
- Full control

**Disadvantages:**
- You manage backups
- You manage updates
- No high availability

**Backup script** (`/home/appuser/backup-db.sh`):
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec staffing-postgres-prod pg_dump -U postgres staffing > /home/appuser/backups/db_$DATE.sql
# Keep only last 7 days
find /home/appuser/backups -name "db_*.sql" -mtime +7 -delete
```

Setup cron:
```bash
crontab -e
# Add:
0 2 * * * /home/appuser/backup-db.sh
```

---

## Auth0 Production Configuration

### Step 1: Create Production Tenant

1. **Go to** Auth0 Dashboard
2. **Create new tenant** for production (don't use development tenant!)
3. **Name**: `your-company-prod`

### Step 2: Configure Application

1. **Go to** Applications → Applications → Create Application
2. **Name**: `Staffing Agent Production`
3. **Type**: Single Page Application
4. **Settings**:
   - **Allowed Callback URLs**:
     ```
     https://staffingagent.com/callback
     https://www.staffingagent.com/callback
     ```
   - **Allowed Logout URLs**:
     ```
     https://staffingagent.com
     https://www.staffingagent.com
     ```
   - **Allowed Web Origins**:
     ```
     https://staffingagent.com
     https://www.staffingagent.com
     ```

### Step 3: Create API

1. **Go to** Applications → APIs → Create API
2. **Name**: `Staffing Agent API`
3. **Identifier**: `https://api.staffingagent.com`
4. **Signing Algorithm**: RS256

### Step 4: Create Roles

Same as development:
1. Go to User Management → Roles
2. Create: `superuser`, `project_manager`, `staff`

### Step 5: Create Auth0 Action

1. **Go to** Actions → Flows → Login
2. **Create** "Add Roles to Token" action (same code as dev)
3. **Deploy** and add to flow

### Step 6: Create Production Users

1. Go to User Management → Users
2. Create initial admin user with `superuser` role
3. Assign roles

### Step 7: Security Settings

**Enable MFA:**
1. Go to Security → Multi-factor Auth
2. Enable "One-time Password"
3. Set policy: "Always" for superusers

**Set Token Expiration:**
1. Go to Applications → APIs → Your API
2. Token Expiration: 24 hours (or as needed)

**Enable Breached Password Detection:**
1. Go to Security → Attack Protection
2. Enable "Breached Password Detection"

---

## Domain and SSL Setup

### Step 1: Add DNS Records

In your domain registrar (e.g., Namecheap, Google Domains):

**For App Platform:**
```
Type    Name    Value                                      TTL
A       @       your-app-platform-ip                       3600
A       www     your-app-platform-ip                       3600
CNAME   api     backend-xxxxx.ondigitalocean.app          3600
```

**For Droplet:**
```
Type    Name    Value                   TTL
A       @       your_droplet_ip         3600
A       www     your_droplet_ip         3600
A       api     your_droplet_ip         3600
```

### Step 2: SSL/TLS Certificates

**App Platform**: SSL is automatic! ✅

**Droplet**: Use Let's Encrypt (see Droplet Step 10)

### Step 3: Force HTTPS

**Nginx config** (already included in nginx.conf):
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name staffingagent.com www.staffingagent.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Testing

### Post-Deployment Checklist

#### Backend
- [ ] Open `https://api.staffingagent.com/docs`
- [ ] API documentation loads
- [ ] Try `/health` endpoint - returns 200 OK
- [ ] Database connection works

#### Frontend
- [ ] Open `https://staffingagent.com`
- [ ] Site loads without errors
- [ ] Click "Log In" - redirects to Auth0
- [ ] Log in with test user
- [ ] Redirected back to site
- [ ] User menu shows correctly

#### Auth0 Integration
- [ ] Log in as superuser - can access all features
- [ ] Log in as project manager - can search
- [ ] Log in as staff - search shows permission error
- [ ] Tokens are valid and contain roles
- [ ] Logout works correctly

#### Security
- [ ] HTTPS works (no mixed content warnings)
- [ ] HTTP redirects to HTTPS
- [ ] CORS is properly configured
- [ ] API endpoints require authentication

### Load Testing

Use Apache Bench:
```bash
# Test backend
ab -n 1000 -c 10 https://api.staffingagent.com/health

# With auth token
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" https://api.staffingagent.com/api/v1/candidates/
```

---

## Monitoring and Maintenance

### Digital Ocean Monitoring

1. **Go to** your App/Droplet → Insights
2. **Enable**:
   - CPU usage alerts
   - Memory usage alerts
   - Disk usage alerts

### Application Logging

**View logs:**

**App Platform:**
```bash
# Via dashboard: Apps → your-app → Logs
# Or via CLI:
doctl apps logs <app-id> --type BUILD
doctl apps logs <app-id> --type RUN
```

**Droplet:**
```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Backup Strategy

**Database backups:**
- Digital Ocean Managed DB: Automatic daily backups ✅
- Self-hosted: Automated script (see Database Setup)

**Code backups:**
- GitHub repository ✅

**Environment variables:**
- Store securely in password manager
- Document in team wiki

### Updates and Maintenance

**App Platform:**
- Automatic deploys on `git push` (if configured)
- Manual deploy: Click "Deploy" button

**Droplet:**
```bash
# Update code
cd ~/staffingagent
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Clean old images
docker system prune -a
```

### Cost Estimation

**App Platform:**
- Backend (512MB): $5/month
- Frontend (512MB): $5/month
- Database (Basic): $15/month
- **Total**: ~$25/month

**Droplet:**
- Droplet (1GB): $6/month
- Managed Database: $15/month
- OR Self-hosted DB: $0 (included in droplet)
- **Total**: ~$6-21/month

---

## Troubleshooting

### Issue: App won't start

**Check logs:**
```bash
# App Platform
doctl apps logs <app-id> --type RUN

# Droplet
docker compose -f docker-compose.prod.yml logs backend
```

**Common causes:**
- Missing environment variables
- Database connection failed
- Port already in use

### Issue: Database connection refused

**Check:**
1. Database is running and healthy
2. DATABASE_URL is correct
3. Firewall allows connections
4. VPC is configured (App Platform)

**Fix:**
```bash
# Test connection
psql $DATABASE_URL

# Restart database
docker compose -f docker-compose.prod.yml restart postgres
```

### Issue: Frontend shows "Auth0 not configured"

**Check:**
1. Environment variables are set correctly
2. VITE_ prefix is used
3. App was rebuilt after changing env vars

**Fix (App Platform):**
1. Update environment variables
2. Click "Deploy"

**Fix (Droplet):**
```bash
docker compose -f docker-compose.prod.yml up -d --build frontend
```

### Issue: CORS errors

**Check CORS_ORIGINS:**
```bash
# Should include your domain
CORS_ORIGINS=https://staffingagent.com,https://www.staffingagent.com
```

**Restart backend after changing.**

---

## Next Steps

1. **✅ Set up monitoring alerts**
2. **✅ Configure automated backups**
3. **📊 Set up analytics** (Google Analytics, Plausible)
4. **🔐 Review security** (run security audit)
5. **📈 Scale** as needed (increase resources)
6. **🚀 CI/CD** (automate deployments with GitHub Actions)

---

## Support Resources

- **Digital Ocean Docs**: https://docs.digitalocean.com/
- **Digital Ocean Community**: https://www.digitalocean.com/community
- **App Platform Guide**: https://docs.digitalocean.com/products/app-platform/
- **Droplet Tutorial**: https://www.digitalocean.com/community/tutorials

## Deployment Checklist

Before going live:

- [ ] Domain purchased and DNS configured
- [ ] SSL certificate installed
- [ ] Auth0 production tenant configured
- [ ] Production users created in Auth0
- [ ] Database backups configured
- [ ] Monitoring and alerts set up
- [ ] Environment variables documented
- [ ] Security review completed
- [ ] Load testing performed
- [ ] Team trained on deployment process

---

**Congratulations! Your Staffing Agent is now live on Digital Ocean! 🎉**
