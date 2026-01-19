# AWS Amplify Quick Setup - Demo Configuration

## Your Backend URL
**Backend:** `http://13.62.98.63:8000` ✅ (HTTP is fine for demo)

---

## AWS Amplify Setup Steps

### Step 1: Go to AWS Amplify Console
1. Open AWS Console
2. Search "Amplify"
3. Click "AWS Amplify" service

### Step 2: Create New App
1. Click **"New app"** → **"Host web app"**
2. Select **"GitHub"**
3. Click **"Connect branch"**
4. Authorize AWS Amplify (if first time)
5. Select repository: **`UmarShoaib-Code/QoE`**
6. Select branch: **`main`**
7. Click **"Next"**

### Step 3: Configure Build Settings
Amplify should auto-detect `amplify.yml`. If not, use:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

### Step 4: Set Environment Variable (IMPORTANT!)
Click **"Add environment variable"**:

- **Key:** `VITE_API_URL`
- **Value:** `http://13.62.98.63:8000`
- Click **"Save"**

### Step 5: Deploy
1. Click **"Save and deploy"**
2. Wait 5-10 minutes for build
3. Get your live URL (e.g., `https://main.xxxxx.amplifyapp.com`)

---

## Important Notes for Demo

### ✅ HTTP Backend is Fine for Demo
- HTTP backend works for demo purposes
- No SSL certificate needed
- Your backend at `http://13.62.98.63:8000` is accessible

### ⚠️ Browser Warnings (Normal)
- Browsers may show "Not Secure" for HTTP backend calls
- This is normal for demos
- Clients can still test all functionality

### 🔒 For Production Later
- Add SSL certificate to backend (Let's Encrypt)
- Use HTTPS: `https://13.62.98.63:8000`
- No extra cost, free SSL certificates available

---

## Verify Backend is Working

Test these URLs in browser:

1. **API Docs:** `http://13.62.98.63:8000/docs` ✅
2. **Health Check:** `http://13.62.98.63:8000/health` (if exists)
3. **Backend Root:** `http://13.62.98.63:8000/` ✅

---

## Your URLs After Deployment

- **Frontend (Live):** `https://main.xxxxx.amplifyapp.com` (from Amplify)
- **Backend (Demo):** `http://13.62.98.63:8000` (EC2)
- **API Docs:** `http://13.62.98.63:8000/docs`

**Everything ready for client demo! 🚀**

