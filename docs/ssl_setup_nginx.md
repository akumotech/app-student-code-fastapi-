# SSL Setup for FastAPI with Nginx and Certbot

This guide explains how to secure your FastAPI app with SSL using Certbot (Let's Encrypt) and Nginx as a reverse proxy.

---

## 1. Prerequisites

- A domain name (e.g., `your.domain.com`) pointing to your EC2 instance (e.g., via Route53 A record)
- FastAPI app running (e.g., on `localhost:8000`)
- Root or sudo access to your server

---

## 2. Install Certbot and Nginx

On Amazon Linux:

```bash
sudo yum update -y
sudo yum install -y epel-release
sudo yum install -y certbot nginx
```

---

## 3. Start and Enable Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## 4. Allow HTTP/HTTPS in Firewall (if using firewalld)

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 5. Obtain SSL Certificate with Certbot

Replace `your.domain.com` and `your@email.com` with your actual domain and email:

```bash
sudo certbot --nginx -d your.domain.com --non-interactive --agree-tos -m your@email.com
```

Certbot will automatically configure Nginx for SSL.

---

## 6. Configure Nginx as a Reverse Proxy for FastAPI

Edit (or create) `/etc/nginx/conf.d/fastapi.conf`:

```nginx
server {
    listen 80;
    server_name your.domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your.domain.com;

    ssl_certificate /etc/letsencrypt/live/your.domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your.domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Reload Nginx:

```bash
sudo systemctl reload nginx
```

---

## 7. Automatic SSL Renewal

Certbot sets up automatic renewal, but you can test it with:

```bash
sudo certbot renew --dry-run
```

---

## 8. Troubleshooting

- Check Nginx status: `sudo systemctl status nginx`
- Check Certbot logs: `/var/log/letsencrypt/letsencrypt.log`
- Check Nginx config: `sudo nginx -t`
- View SSL certificate info: `sudo openssl x509 -in /etc/letsencrypt/live/your.domain.com/fullchain.pem -text -noout`

---

**Your FastAPI app is now secured with SSL and served via Nginx!**
