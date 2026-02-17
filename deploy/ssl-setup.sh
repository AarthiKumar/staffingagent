#!/bin/bash
# SSL certificate setup using Let's Encrypt
# Run this after setup.sh and before deploy.sh

set -e

DOMAIN="aal.yookthi.ai"
EMAIL="your-email@example.com"  # Change this!

echo "================================"
echo "SSL Certificate Setup"
echo "================================"

# Check if domain is already configured
if [ "$EMAIL" = "your-email@example.com" ]; then
    echo "ERROR: Please edit this script and set your email address first!"
    exit 1
fi

# Create a temporary nginx config without SSL for initial cert generation
echo "Creating temporary nginx config..."
cat > /tmp/nginx-temp.conf << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name aal.yookthi.ai;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 "SSL setup in progress";
        add_header Content-Type text/plain;
    }
}
EOF

# Apply temporary config
sudo cp /tmp/nginx-temp.conf /etc/nginx/sites-available/aal.yookthi.ai
sudo nginx -t
sudo systemctl reload nginx

# Obtain SSL certificate
echo "Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly \
    --nginx \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

# Restore the full nginx config with SSL
echo "Restoring full nginx configuration..."
sudo cp nginx-site.conf /etc/nginx/sites-available/aal.yookthi.ai
sudo nginx -t
sudo systemctl reload nginx

# Set up automatic renewal
echo "Setting up automatic certificate renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

echo ""
echo "================================"
echo "SSL setup complete!"
echo "================================"
echo ""
echo "Certificate details:"
sudo certbot certificates
echo ""
echo "Next step: Run ./deploy/deploy.sh to deploy the application"
