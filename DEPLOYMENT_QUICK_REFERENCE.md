# Deployment Quick Reference

Quick commands and cheat sheet for deploying the Staffing Agent application.

## 📋 Prerequisites Checklist

```bash
# Check you have everything:
[ ] Digital Ocean account
[ ] Domain name (optional)
[ ] Auth0 production tenant
[ ] GitHub repository
```

## 🚀 Option 1: Digital Ocean App Platform (Easiest)

### Setup (One Time)

1. **Create Database**
   - Digital Ocean → Databases → Create → PostgreSQL 15
   - Name: `staffing-agent-db`
   - Plan: Basic ($15/month)

2. **Create App**
   - Digital Ocean → Apps → Create App
   - Connect GitHub repository
   - Select branch: `main`

3. **Configure Backend Service**
   ```yaml
   Name: backend
   Source Directory: /backend
   Run Command: uvicorn app.main:app --host 0.0.0.0 --port 8080
   Port: 8080
   Size: Basic (512MB)
   ```

4. **Configure Frontend Service**
   ```yaml
   Name: frontend
   Source Directory: /frontend
   Build Command: npm run build
   Output Directory: dist
   Size: Basic (512MB)
   ```

5. **Set Environment Variables** (see below)

6. **Deploy!**

### Environment Variables

**Backend:**
```bash
DATABASE_URL=${db.DATABASE_URL}
AUTH0_ENABLED=true
AUTH0_DOMAIN=your-prod.auth0.com
AUTH0_CLIENT_ID=abc123
AUTH0_CLIENT_SECRET=${SECRET}
AUTH0_AUDIENCE=https://api.staffingagent.com
CORS_ORIGINS=https://staffingagent.com
```

**Frontend:**
```bash
VITE_API_URL=https://backend-xxx.ondigitalocean.app/api/v1
VITE_AUTH0_ENABLED=true
VITE_AUTH0_DOMAIN=your-prod.auth0.com
VITE_AUTH0_CLIENT_ID=abc123
VITE_AUTH0_AUDIENCE=https://api.staffingagent.com
VITE_AUTH0_REDIRECT_URI=https://staffingagent.com/callback
```

### Deploy Updates

```bash
git push origin main
# App Platform auto-deploys ✅
```

## 🐳 Option 2: Digital Ocean Droplet with Docker

### Setup (One Time)

```bash
# 1. Create droplet
# Digital Ocean → Create → Droplets → Ubuntu 22.04

# 2. SSH into droplet
ssh root@your_droplet_ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Clone repository
git clone https://github.com/yourusername/staffingagent.git
cd staffingagent

# 5. Create .env.prod file
cp .env.prod.example .env.prod
nano .env.prod
# Fill in your values

# 6. Deploy
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 7. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 8. Setup SSL (if using custom domain)
apt install certbot python3-certbot-nginx -y
certbot --nginx -d staffingagent.com -d www.staffingagent.com
```

### Deploy Updates

```bash
# SSH into droplet
ssh root@your_droplet_ip

# Update code
cd ~/staffingagent
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

## 🔐 Auth0 Production Setup

```bash
# 1. Create production tenant
Auth0 Dashboard → Create Tenant → "your-company-prod"

# 2. Create Application
Applications → Create → Single Page Application
Allowed Callback URLs: https://staffingagent.com/callback
Allowed Logout URLs: https://staffingagent.com
Allowed Web Origins: https://staffingagent.com

# 3. Create API
APIs → Create API
Identifier: https://api.staffingagent.com
Algorithm: RS256

# 4. Create roles
User Management → Roles → Create:
  - superuser
  - project_manager
  - staff

# 5. Create Action
Actions → Flows → Login → Create Action
# Add "Add Roles to Token" code

# 6. Deploy Action and add to flow
```

## 🌐 DNS Configuration

**For App Platform:**
```
Type    Name    Value
A       @       app-platform-ip
CNAME   www     @
CNAME   api     backend-xxx.ondigitalocean.app
```

**For Droplet:**
```
Type    Name    Value
A       @       droplet_ip
A       www     droplet_ip
A       api     droplet_ip
```

## 🧪 Testing Checklist

```bash
# Backend health
curl https://api.staffingagent.com/health

# API docs
open https://api.staffingagent.com/docs

# Frontend
open https://staffingagent.com

# Test login
# Click "Log In" → Auth0 → Should redirect back

# Test auth
# Try search as staff → Should get 403 error ✅
```

## 📊 Monitoring

### View Logs

**App Platform:**
```bash
doctl apps logs <app-id> --type RUN --follow
```

**Droplet:**
```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Check Resource Usage

**App Platform:**
```
Digital Ocean → Apps → Your App → Insights
```

**Droplet:**
```bash
docker stats
df -h
free -h
```

## 🔄 Common Commands

### Restart Services

**App Platform:**
```bash
doctl apps create-deployment <app-id>
```

**Droplet:**
```bash
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
```

### View Database

**App Platform (managed DB):**
```bash
# Get connection string from Digital Ocean
psql "postgresql://user:pass@host:25060/db?sslmode=require"
```

**Droplet:**
```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres staffing
```

### Backup Database

**Droplet:**
```bash
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres staffing > backup_$(date +%Y%m%d).sql
```

### Clean Up Docker

```bash
# Remove unused containers/images
docker system prune -a

# See disk usage
docker system df
```

## 🆘 Troubleshooting

### App won't start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Common fixes:
# - Check environment variables
# - Verify database connection
# - Ensure ports aren't in use
```

### Database connection error
```bash
# Test connection
docker compose -f docker-compose.prod.yml exec backend \
  python -c "from app.db.session import engine; print(engine)"

# Restart database
docker compose -f docker-compose.prod.yml restart postgres
```

### Frontend shows "Auth0 not configured"
```bash
# Rebuild with correct env vars
docker compose -f docker-compose.prod.yml up -d --build frontend

# Verify env vars were passed
docker compose -f docker-compose.prod.yml exec frontend env | grep VITE
```

### CORS errors
```bash
# Update CORS_ORIGINS in backend env vars
CORS_ORIGINS=https://staffingagent.com,https://www.staffingagent.com

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

## 💰 Cost Estimates

**App Platform (Managed):**
- Backend (512MB): $5/month
- Frontend (512MB): $5/month
- Database (Basic): $15/month
- **Total: ~$25/month**

**Droplet (Self-managed):**
- Droplet (1GB): $6/month
- Managed DB: $15/month OR
- Self-hosted DB: $0
- **Total: ~$6-21/month**

## 📚 Full Documentation

- `DIGITALOCEAN_DEPLOYMENT.md` - Complete deployment guide
- `GETTING_STARTED_WITH_AUTH0.md` - Auth0 setup walkthrough
- `AUTH0_SETUP.md` - Detailed Auth0 configuration

## 🎯 Quick Deploy Script

Save as `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Staffing Agent..."

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Clean up
docker system prune -f

echo "✅ Deployment complete!"
echo "📊 Checking services..."
docker compose -f docker-compose.prod.yml ps
```

Make executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

**Pro Tip:** Bookmark this page for quick reference during deployments! 📌
