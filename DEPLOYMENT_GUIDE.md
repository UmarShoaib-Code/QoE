# Complete AWS Deployment Guide - From Clone to Live

**Cost: FREE for 12 months (EC2 Free Tier) + AWS Amplify Free Tier**

## Architecture
- **Frontend:** AWS Amplify (React) - FREE
- **Backend:** EC2 Free Tier (FastAPI) - FREE for 12 months
- **Database:** Skipped for now (using localStorage on frontend)

---

## Prerequisites

1. **AWS Account** (Free tier eligible)
   - Sign up at https://aws.amazon.com
   - Requires credit card (won't be charged if using free tier)

2. **GitHub Account**
   - Your code is already at: `https://github.com/UmarShoaib-Code/QoE.git`

3. **SSH Client** (Windows: PuTTY or WSL, Mac/Linux: Built-in)

---

## Part 1: Prepare Code for Deployment

### Step 1: Clone Repository (if needed)

```bash
git clone https://github.com/UmarShoaib-Code/QoE.git
cd QoE
```

### Step 2: Code is Already Fixed ✅
- Hardcoded URLs fixed
- CORS updated for production
- Dockerfile created for backend

---

## Part 2: Deploy Backend to EC2 (Free Tier)

### Step 3: Launch EC2 Instance

1. **Login to AWS Console**
   - Go to: https://console.aws.amazon.com
   - Search for "EC2" in top search bar

2. **Launch Instance**
   - Click "Launch Instance"
   - **Name:** `qoe-tool-backend`

3. **Choose AMI (Operating System)**
   - Select: **Ubuntu Server 22.04 LTS** (Free tier eligible)

4. **Instance Type**
   - Select: **t2.micro** (Free tier eligible)
   - Click "Next: Configure Instance Details"

5. **Configure Instance**
   - Keep defaults
   - Click "Next: Add Storage"

6. **Storage**
   - Keep 8 GB (Free tier eligible)
   - Click "Next: Add Tags"

7. **Tags (Optional)**
   - Skip or add: `Name: qoe-backend`
   - Click "Next: Configure Security Group"

8. **Security Group (IMPORTANT)**
   - Name: `qoe-backend-sg`
   - Description: `Security group for QoE Tool backend`
   - **Add Rules:**
     - **Type:** SSH, Port: 22, Source: My IP
     - **Type:** Custom TCP, Port: 8000, Source: 0.0.0.0/0 (Allow all - for Amplify)
   - Click "Review and Launch"

9. **Review**
   - Click "Launch"

10. **Key Pair**
    - Select "Create a new key pair"
    - **Name:** `qoe-backend-key`
    - Click "Download Key Pair" (save `qoe-backend-key.pem` securely!)
    - Click "Launch Instances"

11. **Wait for Instance**
    - Click "View Instances"
    - Wait until "Instance State" shows "Running" (takes ~30 seconds)

### Step 4: Get EC2 Connection Details

1. **Find Public IP**
   - Select your instance
   - Copy "Public IPv4 address" (e.g., `3.89.123.45`)
   - Save this IP - you'll need it!

2. **Example:** `3.89.123.45` (Your IP will be different)

### Step 5: Connect to EC2 Instance

**Windows (PowerShell or Command Prompt):**

```powershell
# Navigate to where you saved the .pem file
cd C:\Users\YourName\Downloads

# Set permissions (one-time)
icacls qoe-backend-key.pem /inheritance:r

# Connect
ssh -i qoe-backend-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Replace `YOUR_PUBLIC_IP` with your actual IP from Step 4**

**Mac/Linux:**

```bash
# Navigate to .pem file
cd ~/Downloads

# Set permissions
chmod 400 qoe-backend-key.pem

# Connect
ssh -i qoe-backend-key.pem ubuntu@YOUR_PUBLIC_IP
```

**First connection:** Type `yes` when prompted about authenticity

### Step 6: Install Dependencies on EC2

Once connected, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Git
sudo apt install -y git

# Install Docker (optional, for easier deployment)
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Install Nginx (optional, for serving static files)
sudo apt install -y nginx

# Logout and login again for docker group to take effect
exit
```

**Reconnect to EC2:**

```bash
ssh -i qoe-backend-key.pem ubuntu@YOUR_PUBLIC_IP
```

### Step 7: Clone and Setup Backend

```bash
# Clone your repository
git clone https://github.com/UmarShoaib-Code/QoE.git
cd QoE

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create output directory
mkdir -p output

# Set environment variables
export CORS_ORIGINS="*"
export PORT=8000

# Test if backend starts (press Ctrl+C to stop)
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

**If this works, you'll see:** `Uvicorn running on http://0.0.0.0:8000`

Press `Ctrl+C` to stop it.

### Step 8: Run Backend as a Service (Auto-start on reboot)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/qoe-backend.service
```

**Paste this content:**

```ini
[Unit]
Description=QoE Tool Backend API
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/QoE
Environment="PATH=/home/ubuntu/QoE/venv/bin"
Environment="CORS_ORIGINS=*"
ExecStart=/home/ubuntu/QoE/venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

**Enable and start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable qoe-backend
sudo systemctl start qoe-backend

# Check status
sudo systemctl status qoe-backend
```

**You should see:** `active (running)`

**Check logs:**

```bash
sudo journalctl -u qoe-backend -f
```

**Test backend:**

```bash
curl http://localhost:8000/docs
```

### Step 9: Test Backend from Browser

1. Open browser
2. Go to: `http://YOUR_PUBLIC_IP:8000/docs`
3. You should see FastAPI Swagger documentation!

**Save your backend URL:** `http://YOUR_PUBLIC_IP:8000`

---

## Part 3: Deploy Frontend to AWS Amplify (FREE)

### Step 10: Push Latest Code to GitHub

Make sure your latest code is pushed:

```bash
# On your local machine (not EC2)
git add .
git commit -m "Production ready: Fixed hardcoded URLs and CORS"
git push origin main
```

### Step 11: Create AWS Amplify App

1. **Go to AWS Amplify**
   - In AWS Console, search for "Amplify"
   - Click "AWS Amplify"

2. **New App**
   - Click "New app" → "Host web app"

3. **Connect Repository**
   - Select "GitHub"
   - Click "Connect branch"
   - Authorize AWS Amplify to access GitHub
   - Select repository: `UmarShoaib-Code/QoE`
   - Select branch: `main`
   - Click "Next"

4. **Configure Build Settings**
   - Amplify should detect `amplify.yml` automatically
   - If not, click "Edit" and paste this:

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

5. **Environment Variables**
   - Click "Add environment variable"
   - **Name:** `VITE_API_URL`
   - **Value:** `http://YOUR_EC2_PUBLIC_IP:8000` (from Step 4)
   - Example: `http://3.89.123.45:8000`
   - Click "Save"

6. **Review and Deploy**
   - Click "Save and deploy"

### Step 12: Wait for Deployment

- Amplify will automatically:
  1. Clone your repository
  2. Install dependencies
  3. Build React app
  4. Deploy to CDN

**This takes 5-10 minutes**

You'll see progress in the Amplify console.

### Step 13: Get Your Live Frontend URL

1. Once deployment completes (green checkmark)
2. Click on your app in Amplify
3. Copy the **App URL** (looks like: `https://main.xxxxx.amplifyapp.com`)
4. **This is your live frontend URL!**

---

## Part 4: Final Configuration

### Step 14: Update CORS on Backend

Update EC2 to allow your Amplify domain:

```bash
# SSH back into EC2
ssh -i qoe-backend-key.pem ubuntu@YOUR_PUBLIC_IP

# Edit service file
sudo nano /etc/systemd/system/qoe-backend.service
```

**Update the Environment line:**

```ini
Environment="CORS_ORIGINS=https://main.xxxxx.amplifyapp.com,http://localhost:3000,*"
```

**Replace `xxxxx` with your actual Amplify domain**

**Save and restart:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart qoe-backend
sudo systemctl status qoe-backend
```

### Step 15: Test Your Live Application

1. Open your Amplify URL: `https://main.xxxxx.amplifyapp.com`
2. Test login/registration
3. Test file upload
4. Test Excel download

---

## Your Live URLs

- **Frontend:** `https://main.xxxxx.amplifyapp.com` (from Amplify)
- **Backend API:** `http://YOUR_PUBLIC_IP:8000` (EC2)
- **API Docs:** `http://YOUR_PUBLIC_IP:8000/docs`

---

## Troubleshooting

### Backend not accessible?

1. Check Security Group:
   - EC2 Console → Security Groups
   - Ensure port 8000 is open (0.0.0.0/0)

2. Check backend status:
   ```bash
   ssh -i qoe-backend-key.pem ubuntu@YOUR_PUBLIC_IP
   sudo systemctl status qoe-backend
   ```

### Frontend not connecting to backend?

1. Check environment variable in Amplify:
   - Amplify Console → App Settings → Environment variables
   - Ensure `VITE_API_URL` is set correctly

2. Rebuild frontend:
   - Amplify Console → Click "Redeploy this version"

### Need to update code?

```bash
# On local machine
git add .
git commit -m "Your changes"
git push origin main
```

- **Backend:** SSH to EC2 and run `git pull`, then `sudo systemctl restart qoe-backend`
- **Frontend:** Amplify auto-deploys on git push!

---

## Cost Summary

- **EC2 t2.micro:** FREE for 12 months, then ~$8/month
- **AWS Amplify:** FREE (within free tier limits)
- **Total:** $0/month for first 12 months! 🎉

---

## Next Steps (Optional)

1. **Custom Domain:** Add your domain to Amplify
2. **SSL for Backend:** Use Nginx reverse proxy with Let's Encrypt
3. **Database:** Set up AWS RDS MySQL when needed
4. **Monitoring:** Set up CloudWatch for logs

**Your application is now LIVE! 🚀**

