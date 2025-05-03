#!/bin/bash

# Variables (edit these)
DOMAIN="code.dev.akumotechnology.com"  
EMAIL="asharif+dev@akumosolutions.io" 

# Update and install EPEL (for Amazon Linux) and Certbot
sudo yum update -y
sudo yum install -y epel-release
sudo yum install -y certbot nginx

# Start and enable nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Obtain SSL certificate (will prompt for DNS challenge if not using HTTP)
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

# Set up automatic renewal
echo "0 3 * * * root certbot renew --quiet" | sudo tee /etc/cron.d/certbot-renew

echo "SSL setup complete! Please configure your nginx to proxy to your FastAPI app if not already done."