#!/bin/bash
# Deployment script for Staffing Agent on Digital Ocean
# This script builds and deploys the application using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env.production"

echo "================================"
echo "Staffing Agent - Deployment"
echo "================================"

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: .env.production file not found!${NC}"
    echo "Please copy .env.production.example to .env.production and configure it."
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Verify critical environment variables
REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "MINIO_ROOT_USER"
    "MINIO_ROOT_PASSWORD"
    "AUTH0_DOMAIN"
    "AUTH0_CLIENT_ID"
    "GRAFANA_ADMIN_PASSWORD"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}ERROR: Required environment variable $var is not set!${NC}"
        exit 1
    fi
done

echo -e "${GREEN}Environment configuration validated${NC}"

# Navigate to project directory
cd "$PROJECT_DIR"

# Pull latest code (if in git repo)
if [ -d .git ]; then
    echo "Pulling latest code..."
    git pull || echo -e "${YELLOW}Warning: Could not pull latest code${NC}"
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Build and start containers
echo "Building and starting containers..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check if backend is healthy
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/api/v1/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is healthy!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend health check failed!${NC}"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    echo "Waiting for backend... (attempt $i/30)"
    sleep 2
done

# Run database migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || {
    echo -e "${YELLOW}Warning: Migrations might have failed. Check logs.${NC}"
}

# Check frontend health
echo "Checking frontend health..."
for i in {1..30}; do
    if curl -f http://localhost:3001/health > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend is healthy!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Frontend health check failed!${NC}"
        docker-compose -f docker-compose.prod.yml logs frontend
        exit 1
    fi
    echo "Waiting for frontend... (attempt $i/30)"
    sleep 2
done

# Reload nginx
echo "Reloading nginx..."
sudo systemctl reload nginx

# Show container status
echo ""
echo "Container status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "================================"
echo -e "${GREEN}Deployment complete!${NC}"
echo "================================"
echo ""
echo "Services:"
echo "  - Frontend: https://aal.yookthi.ai"
echo "  - Backend API: https://aal.yookthi.ai/api/v1"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo "  - MinIO Console: http://localhost:9001"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f [service_name]"
echo ""
echo "To restart a service:"
echo "  docker-compose -f docker-compose.prod.yml restart [service_name]"
