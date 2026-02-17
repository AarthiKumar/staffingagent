# Deployment Scripts

This directory contains scripts and configuration files for deploying the Staffing Agent to Digital Ocean.

## Files

- **setup.sh** - Initial server setup (run once on fresh droplet)
- **ssl-setup.sh** - SSL certificate configuration with Let's Encrypt
- **deploy.sh** - Main deployment script (build and deploy)
- **nginx-site.conf** - Nginx reverse proxy configuration for the host

## Deployment Workflow

1. **Initial Setup** (Run once)
   ```bash
   ./setup.sh
   ```

2. **Configure Environment**
   ```bash
   cp ../.env.production.example ../.env.production
   nano ../.env.production  # Edit with your values
   ```

3. **Set Up SSL**
   ```bash
   nano ssl-setup.sh  # Update email address
   ./ssl-setup.sh
   ```

4. **Deploy Application**
   ```bash
   ./deploy.sh
   ```

## Subsequent Deployments

For updates after initial deployment:

```bash
cd /opt/staffingagent
git pull
cd deploy
./deploy.sh
```

## Quick Commands

### View Logs
```bash
cd /opt/staffingagent
docker-compose -f docker-compose.prod.yml logs -f [service]
```

### Restart Service
```bash
docker-compose -f docker-compose.prod.yml restart [service]
```

### Check Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Run Migrations
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Backup Database
```bash
cd /opt/staffingagent
./scripts/backup.sh
```

## Troubleshooting

See [DEPLOYMENT.md](../DEPLOYMENT.md) for detailed troubleshooting guide.

### Quick Checks

1. **Check if all containers are running:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. **Check backend health:**
   ```bash
   curl http://localhost:8000/api/v1/healthz
   ```

3. **Check frontend health:**
   ```bash
   curl http://localhost:3001/health
   ```

4. **Check nginx configuration:**
   ```bash
   sudo nginx -t
   ```

5. **Check SSL certificate:**
   ```bash
   sudo certbot certificates
   ```

## Security Notes

- All deployment scripts require appropriate permissions
- Keep `.env.production` secure and never commit it
- Use strong passwords for all services
- Regularly update system packages and Docker images
- Monitor application logs for suspicious activity

## Support

For detailed documentation, see [DEPLOYMENT.md](../DEPLOYMENT.md) in the project root.
