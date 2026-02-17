# Deployment Guide - Digital Ocean

This guide covers deploying the Staffing Agent application to Digital Ocean and hosting it on `aal.yookthi.ai`.

## Prerequisites

1. **Digital Ocean Droplet**
   - Recommended: 4GB RAM, 2 vCPUs, 80GB SSD
   - OS: Ubuntu 22.04 LTS
   - Root or sudo access

2. **Domain Configuration**
   - Domain: `yookthi.ai`
   - Subdomain: `aal.yookthi.ai`
   - DNS A record pointing to your droplet's IP address

3. **Required Credentials**
   - Auth0 account and application credentials
   - OpenAI API key (for embeddings and LLM features)
   - Email address for SSL certificate registration

## Quick Start

### 1. Initial Server Setup

SSH into your Digital Ocean droplet:

```bash
ssh root@your-droplet-ip
```

Clone the repository:

```bash
cd /opt
git clone <your-repo-url> staffingagent
cd staffingagent
```

Run the initial setup script:

```bash
cd deploy
./setup.sh
```

This script will:
- Update system packages
- Install Docker and Docker Compose
- Install nginx and certbot
- Configure firewall (UFW)
- Set up application directory
- Configure nginx site

**Important:** After running setup.sh, log out and back in for Docker group changes to take effect.

### 2. Configure Environment Variables

Copy the production environment template:

```bash
cd /opt/staffingagent
cp .env.production.example .env.production
```

Edit `.env.production` with your configuration:

```bash
nano .env.production
```

**Required configurations:**

```bash
# Database
POSTGRES_PASSWORD=<strong-random-password>

# MinIO
MINIO_ROOT_USER=<minio-username>
MINIO_ROOT_PASSWORD=<strong-random-password>

# OpenAI
LLM_API_KEY=sk-<your-openai-api-key>

# Auth0
AUTH0_DOMAIN=<your-tenant>.auth0.com
AUTH0_CLIENT_ID=<your-auth0-client-id>
AUTH0_AUDIENCE=https://aal.yookthi.ai

# Frontend Auth0
VITE_AUTH0_DOMAIN=<your-tenant>.auth0.com
VITE_AUTH0_CLIENT_ID=<your-auth0-client-id>
VITE_AUTH0_AUDIENCE=https://aal.yookthi.ai
VITE_API_BASE_URL=https://aal.yookthi.ai/api/v1

# Grafana
GRAFANA_ADMIN_PASSWORD=<strong-random-password>
```

### 3. Set Up SSL Certificates

Before running this script, edit `deploy/ssl-setup.sh` and update the email address:

```bash
nano deploy/ssl-setup.sh
# Change: EMAIL="your-email@example.com"
```

Run the SSL setup script:

```bash
cd deploy
./ssl-setup.sh
```

This will:
- Obtain SSL certificates from Let's Encrypt
- Configure nginx with SSL
- Set up automatic certificate renewal

### 4. Deploy the Application

Run the deployment script:

```bash
cd deploy
./deploy.sh
```

This will:
- Build Docker images
- Start all containers
- Run database migrations
- Verify service health
- Reload nginx

## Auth0 Configuration

### Backend API Configuration

1. Go to Auth0 Dashboard → Applications → APIs
2. Create a new API or use existing one:
   - **Name:** Staffing Agent API
   - **Identifier:** `https://aal.yookthi.ai`
   - **Signing Algorithm:** RS256

3. Note the identifier and use it for `AUTH0_AUDIENCE`

### Frontend Application Configuration

1. Go to Auth0 Dashboard → Applications
2. Create a new Single Page Application:
   - **Name:** Staffing Agent Frontend
   - **Type:** Single Page Application

3. Configure Application Settings:
   - **Allowed Callback URLs:** `https://aal.yookthi.ai/callback`
   - **Allowed Logout URLs:** `https://aal.yookthi.ai`
   - **Allowed Web Origins:** `https://aal.yookthi.ai`
   - **Allowed Origins (CORS):** `https://aal.yookthi.ai`

4. Note the Domain and Client ID:
   - Use Domain for `AUTH0_DOMAIN` and `VITE_AUTH0_DOMAIN`
   - Use Client ID for `AUTH0_CLIENT_ID` and `VITE_AUTH0_CLIENT_ID`

## Service Management

### View Logs

```bash
cd /opt/staffingagent

# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml stop
```

### Start Services

```bash
docker-compose -f docker-compose.prod.yml start
```

### Check Service Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

## Database Management

### Run Migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Create Migration

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic revision --autogenerate -m "description"
```

### Backup Database

```bash
cd /opt/staffingagent
./scripts/backup.sh
```

Backups are stored in `./backups/` directory.

### Restore Database

```bash
./scripts/restore.sh ./backups/staffing_db_YYYYMMDD_HHMMSS.sql.gz
```

## Monitoring

### Prometheus Metrics

- URL: `http://your-droplet-ip:9090`
- Accessible from server only (configure firewall if external access needed)

### Grafana Dashboards

- URL: `http://your-droplet-ip:3000`
- Default credentials: `admin` / `<your-grafana-password>`
- Accessible from server only (configure firewall if external access needed)

### Application Health Check

```bash
curl https://aal.yookthi.ai/api/v1/healthz
```

### MinIO Console

- URL: `http://your-droplet-ip:9001`
- Credentials: `<MINIO_ROOT_USER>` / `<MINIO_ROOT_PASSWORD>`
- Accessible from server only (configure firewall if external access needed)

## Updating the Application

### Pull Latest Changes

```bash
cd /opt/staffingagent
git pull
```

### Rebuild and Deploy

```bash
cd deploy
./deploy.sh
```

The deploy script will:
1. Stop current containers
2. Rebuild images with latest code
3. Start containers
4. Run migrations
5. Verify health

## Troubleshooting

### Check Container Logs

```bash
docker-compose -f docker-compose.prod.yml logs -f [service-name]
```

### Container Won't Start

1. Check logs for the specific container
2. Verify environment variables in `.env.production`
3. Check disk space: `df -h`
4. Check memory: `free -h`

### SSL Certificate Issues

Verify certificate status:

```bash
sudo certbot certificates
```

Renew certificate manually:

```bash
sudo certbot renew
```

### Database Connection Issues

Check if PostgreSQL container is running:

```bash
docker-compose -f docker-compose.prod.yml ps postgres
```

Check PostgreSQL logs:

```bash
docker-compose -f docker-compose.prod.yml logs postgres
```

### 502 Bad Gateway

1. Check if backend container is running and healthy
2. Check backend logs for errors
3. Verify nginx configuration: `sudo nginx -t`
4. Check nginx error logs: `sudo tail -f /var/log/nginx/aal.yookthi.ai.error.log`

### Frontend Not Loading

1. Check if frontend container is running
2. Check frontend logs
3. Verify build arguments were passed correctly
4. Check browser console for errors

## Security Considerations

1. **Firewall Rules**
   - Only ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) are exposed
   - Internal services (Postgres, MinIO, Prometheus, Grafana) are not exposed externally

2. **Secrets Management**
   - Keep `.env.production` secure with appropriate file permissions
   - Rotate passwords regularly
   - Use strong, unique passwords for all services

3. **Updates**
   - Keep system packages updated: `sudo apt-get update && sudo apt-get upgrade`
   - Update Docker images regularly
   - Monitor for security advisories

4. **Backups**
   - Schedule regular database backups
   - Store backups in a separate location (e.g., S3, Spaces)
   - Test restore procedures

## Performance Tuning

### For Higher Traffic

1. **Increase Droplet Resources**
   - Upgrade to a larger droplet if needed
   - Consider adding more memory for database operations

2. **Database Optimization**
   - Add appropriate indexes (see backend docs)
   - Tune PostgreSQL settings in docker-compose.prod.yml

3. **Caching**
   - Consider adding Redis for caching
   - Configure nginx caching for static assets

4. **Horizontal Scaling**
   - Run multiple backend containers behind a load balancer
   - Use external managed database (e.g., Digital Ocean Managed Databases)

## Cost Optimization

- Monitor OpenAI API usage through the application metrics
- Set appropriate budgets in agent config: `config/agents/staffing.yaml`
- Disable LLM features if not needed: `ENABLE_LLM_RERANK=false`, `ENABLE_NL_ASSIST=false`
- Use local embeddings model if OpenAI costs are too high (requires more memory)

## Support

For issues or questions:
- Check application logs
- Review this deployment guide
- Check the main README.md for application-specific documentation
- Review issue tracker at your repository

## Quick Reference

| Service | URL | Access |
|---------|-----|--------|
| Frontend | https://aal.yookthi.ai | Public |
| Backend API | https://aal.yookthi.ai/api/v1 | Public |
| Prometheus | http://localhost:9090 | Server only |
| Grafana | http://localhost:3000 | Server only |
| MinIO Console | http://localhost:9001 | Server only |

## File Locations

- Application: `/opt/staffingagent`
- Docker volumes: `/var/lib/docker/volumes/`
- Nginx config: `/etc/nginx/sites-available/aal.yookthi.ai`
- SSL certificates: `/etc/letsencrypt/live/aal.yookthi.ai/`
- Nginx logs: `/var/log/nginx/aal.yookthi.ai.*.log`
