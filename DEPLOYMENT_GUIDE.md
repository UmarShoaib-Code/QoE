# Free Deployment Guide for QoE Tool

## 🚀 Best Free Deployment Options

### Option 1: Streamlit Cloud (Recommended - Easiest) ⭐

**Why:** Perfect for Streamlit apps, completely free, easy setup

**Steps:**

1. **Prepare your repository:**
   ```bash
   # Make sure you have a requirements.txt
   pip freeze > requirements.txt
   ```

2. **Create requirements.txt** (if not exists):
   ```
   streamlit>=1.28.0
   pandas>=2.0.0
   numpy>=1.24.0
   openpyxl>=3.1.0
   xlsxwriter>=3.1.0
   pydantic>=2.0.0
   pyyaml>=6.0.0
   ```

3. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/qoe_tool.git
   git push -u origin main
   ```

4. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Main file path: `app/ui/app.py`
   - Click "Deploy"

**Limitations:**
- ✅ Free forever
- ✅ Unlimited apps
- ✅ Automatic HTTPS
- ⚠️ Apps sleep after inactivity (wake up in ~30 seconds)
- ⚠️ 1GB RAM limit
- ⚠️ File size limit: 200MB per upload

**Perfect for:** Your use case! ✅

---

### Option 2: Railway (Full Stack)

**Why:** Good for apps that need persistent processes, free tier available

**Steps:**

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create railway.json:**
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "streamlit run app/ui/app.py --server.port $PORT --server.address 0.0.0.0",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

3. **Create Procfile:**
   ```
   web: streamlit run app/ui/app.py --server.port $PORT --server.address 0.0.0.0
   ```

4. **Deploy:**
   ```bash
   railway init
   railway up
   ```

**Limitations:**
- ✅ $5 free credit monthly
- ✅ 500 hours free compute
- ⚠️ Need credit card (won't charge if under limit)

---

### Option 3: Render (Simple & Free)

**Why:** Easy deployment, free tier, good documentation

**Steps:**

1. **Create render.yaml:**
   ```yaml
   services:
     - type: web
       name: qoe-tool
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run app/ui/app.py --server.port $PORT --server.address 0.0.0.0
       envVars:
         - key: PYTHON_VERSION
           value: 3.11.0
   ```

2. **Deploy:**
   - Go to https://render.com
   - Connect GitHub
   - New Web Service
   - Select repository
   - Use render.yaml config
   - Deploy

**Limitations:**
- ✅ Free tier available
- ⚠️ Apps sleep after 15 min inactivity
- ⚠️ 512MB RAM limit
- ⚠️ Need credit card for free tier

---

### Option 4: Fly.io (Global Edge)

**Why:** Fast, global, free tier

**Steps:**

1. **Install Fly CLI:**
   ```bash
   # Windows: Use PowerShell
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Create fly.toml:**
   ```toml
   app = "qoe-tool"
   primary_region = "iad"

   [build]

   [http_service]
     internal_port = 8501
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]

   [[services]]
     protocol = "tcp"
     internal_port = 8501
     processes = ["app"]

     [[services.ports]]
       port = 80
       handlers = ["http"]
       force_https = true

     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
   ```

3. **Deploy:**
   ```bash
   fly launch
   fly deploy
   ```

**Limitations:**
- ✅ 3 shared VMs free
- ✅ 160GB outbound data/month
- ⚠️ Need credit card

---

## 📋 Quick Setup Checklist

### Before Deployment:

1. **Create requirements.txt:**
   ```bash
   pip freeze > requirements.txt
   ```

2. **Create .streamlit/config.toml** (for Streamlit Cloud):
   ```toml
   [server]
   headless = true
   port = 8501
   enableCORS = false
   enableXsrfProtection = false
   ```

3. **Update app.py** (if needed for deployment):
   ```python
   # Already has sys.path setup - should work!
   ```

4. **Test locally:**
   ```bash
   streamlit run app/ui/app.py
   ```

---

## 🎯 Recommended: Streamlit Cloud

**For your QoE Tool, I recommend Streamlit Cloud because:**

✅ **Easiest setup** - Just connect GitHub and deploy  
✅ **Completely free** - No credit card needed  
✅ **Perfect for Streamlit** - Built specifically for Streamlit apps  
✅ **Automatic HTTPS** - Secure by default  
✅ **Easy updates** - Push to GitHub, auto-deploys  
✅ **No server management** - Fully managed  

**Steps:**

1. **Create requirements.txt:**
   ```bash
   pip freeze > requirements.txt
   ```

2. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

3. **Deploy:**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Repository: `yourusername/qoe_tool`
   - Branch: `main`
   - Main file: `app/ui/app.py`
   - Click "Deploy"

4. **Your app will be live at:**
   ```
   https://your-app-name.streamlit.app
   ```

---

## 🔧 Troubleshooting

### Common Issues:

1. **Import errors:**
   - Make sure `requirements.txt` includes all dependencies
   - Check that `sys.path` setup in `app.py` is correct

2. **File upload issues:**
   - Streamlit Cloud has 200MB file limit
   - Large files may timeout - consider chunking

3. **Memory issues:**
   - Streamlit Cloud: 1GB RAM limit
   - For large files, consider processing in chunks

4. **Slow performance:**
   - First request may be slow (cold start)
   - Subsequent requests are faster

---

## 📝 Example requirements.txt

Create this file in your project root:

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
pydantic>=2.0.0
pyyaml>=6.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
```

---

## 🚀 Quick Start (Streamlit Cloud)

```bash
# 1. Create requirements.txt
pip freeze > requirements.txt

# 2. Commit to Git
git add requirements.txt
git commit -m "Add requirements for deployment"
git push

# 3. Go to https://share.streamlit.io
# 4. Deploy!
```

**That's it! Your app will be live in minutes!** 🎉

