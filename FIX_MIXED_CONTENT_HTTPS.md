# Fix Mixed Content Error - Add HTTPS to Backend

## Problem
- Frontend: HTTPS (Amplify)
- Backend: HTTP (EC2)
- Browsers block HTTP requests from HTTPS pages

## Solution: Add HTTPS to Backend (Free SSL with Let's Encrypt)

---

## Quick Fix: Install Nginx + SSL Certificate

### Step 1: SSH into EC2

```bash
ssh -i Qoe.pem ubuntu@13.62.98.63
```

### Step 2: Install Nginx

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Step 3: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/default
```

**Replace entire content with:**

```nginx
server {
    listen 80;
    server_name 13.62.98.63;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Save:** `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Test Nginx Configuration

```bash
sudo nginx -t
```

Should see: `nginx: configuration file /etc/nginx/nginx.conf test is successful`

### Step 5: Start Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

### Step 6: Test Backend Through Nginx

```bash
curl http://localhost/
```

Should return FastAPI response.

---

## Option A: Quick Demo Fix (Skip SSL - Use Nginx on Port 80)

**Simplest for demo - uses Nginx reverse proxy without SSL**

Update frontend to use HTTP on port 80:

1. **In Amplify Console:**
   - Go to: App Settings → Environment variables
   - Edit `VITE_API_URL`
   - Change to: `http://13.62.98.63` (remove `:8000`)
   - Save and Redeploy

**This uses Nginx proxy (port 80) but still HTTP. May still show warnings.**

---

## Option B: Full HTTPS Solution (Recommended)

### Step 7: Get Free SSL Certificate with Let's Encrypt

**You need a domain name first!** (Let's Encrypt requires a domain)

**Option B1: If you have a domain:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Option B2: If no domain (Use AWS Application Load Balancer):**
- More complex, requires ALB setup
- Not free tier eligible

---

## Option C: Temporary Workaround (For Demo Only)

### Use HTTPS Backend URL in Environment Variable

**This won't work without SSL, but here's an alternative:**

### Quick Fix: Use HTTP Backend but Configure CORS

**On EC2, update backend CORS:**

```bash
# SSH to EC2
ssh -i Qoe.pem ubuntu@13.62.98.63

# Edit backend service
sudo nano /etc/systemd/system/qoe-backend.service
```

**Update Environment line:**
```ini
Environment="CORS_ORIGINS=https://main.d2qu6wvx2wuafq.amplifyapp.com,http://localhost:3000,*"
```

**Restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart qoe-backend
```

**But this won't fix mixed content error - browsers will still block.**

---

## **Best Solution: Use Cloudflare (Free SSL Proxy)**

### Step 1: Sign up for Cloudflare (Free)

1. Go to: https://cloudflare.com
2. Sign up for free account
3. Add your EC2 IP as a "site"

### Step 2: Configure Cloudflare DNS

1. Add A record:
   - Type: A
   - Name: `api` (or any subdomain)
   - IPv4: `13.62.98.63`
   - Proxy: ✅ ON (orange cloud)

2. Get your Cloudflare domain (e.g., `api.yoursite.cloudflare.com`)

### Step 3: Update Amplify Environment Variable

1. Amplify Console → Environment variables
2. Edit `VITE_API_URL`
3. Change to: `https://api.yoursite.cloudflare.com` (or your Cloudflare URL)
4. Save and Redeploy

**Cloudflare provides free HTTPS automatically!**

---

## Recommended: Cloudflare Solution (Easiest)

1. Sign up: https://cloudflare.com (free)
2. Add EC2 IP to Cloudflare
3. Get HTTPS URL from Cloudflare
4. Update `VITE_API_URL` in Amplify
5. Redeploy frontend

**Total time: 5 minutes, completely free!**

---

## Quick Alternative: Change Amplify to HTTP (Not Recommended)

If you absolutely need a quick demo without SSL:

1. Stop using Amplify HTTPS
2. Deploy frontend to EC2 on port 3000
3. Use HTTP for both frontend and backend

**But Amplify HTTPS is better for client demo.**

---

## Which Solution Should You Use?

1. **Best:** Cloudflare free SSL proxy (5 minutes, free)
2. **Good:** Get domain + Let's Encrypt SSL (15 minutes, free)
3. **Demo:** Nginx on port 80 (may still show warnings)

**I recommend Cloudflare - it's the fastest and easiest!**

