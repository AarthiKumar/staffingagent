#!/bin/bash
# Initial setup script for Digital Ocean deployment
# This script should be run once on a fresh Digital Ocean droplet

set -e

echo "================================"
echo "Staffing Agent - Initial Setup"
echo "================================"

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    ufw

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Configure firewall
echo "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Create application directory
echo "Creating application directory..."
APP_DIR="/opt/staffingagent"
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
fi

# Configure nginx
echo "Configuring nginx..."
sudo cp nginx-site.conf /etc/nginx/sites-available/aal.yookthi.ai
sudo ln -sf /etc/nginx/sites-available/aal.yookthi.ai /etc/nginx/sites-enabled/

# Remove default nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Create directory for Let's Encrypt challenges
sudo mkdir -p /var/www/certbot

# Test nginx configuration (will fail until SSL certs are generated, but that's ok)
echo "Testing nginx configuration..."
sudo nginx -t || true

echo ""
echo "================================"
echo "Initial setup complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Clone your repository to $APP_DIR"
echo "2. Copy .env.production.example to .env.production and configure it"
echo "3. Run ./deploy/ssl-setup.sh to set up SSL certificates"
echo "4. Run ./deploy/deploy.sh to deploy the application"
echo ""
echo "Note: You may need to log out and back in for Docker group changes to take effect"
