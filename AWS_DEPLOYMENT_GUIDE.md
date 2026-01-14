# AWS Deployment Guide - QoE Tool

## 🚀 Complete Step-by-Step Guide

### Prerequisites
- AWS Account (you have: acecpas)
- AWS Credentials (provided)
- Your QoE Tool code ready

---

## Option 1: AWS App Runner (Easiest - Recommended) ⭐

### Step 1: Login to AWS Console

1. **Go to AWS Console:**
   - Visit: https://console.aws.amazon.com
   - Click "Sign in to the console"

2. **Enter Credentials:**
   - **Account ID or alias:** `acecpas`
   - **IAM user name:** `mubarak@acecpas.com` (or root account)
   - **Password:** `Acecpas786`
   - Click "Sign in"

3. **Select Region:**
   - Choose a region (e.g., `us-east-1` or `us-west-2`)
   - Top right corner → Select region

### Step 2: Prepare Your Code for GitHub

1. **Push code to GitHub:**
   ```bash
   # If not already on GitHub
   git init
   git add .
   git commit -m "Ready for AWS deployment"
   
   # Create repo on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/qoe_tool.git
   git push -u origin main
   ```

2. **Create Dockerfile:**
   Create `Dockerfile` in project root:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*

   # Copy requirements
   COPY requirements.txt .

   # Install Python dependencies
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Expose Streamlit port
   EXPOSE 8501

   # Health check
   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

   # Run Streamlit
   ENTRYPOINT ["streamlit", "run", "app/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

3. **Create .dockerignore:**
   ```
   __pycache__
   *.pyc
   .git
   .gitignore
   venv/
   env/
   .env
   *.xlsx
   *.xls
   sample_data/
   tests/
   .pytest_cache/
   *.md
   ```

### Step 3: Deploy on AWS App Runner

1. **Navigate to App Runner:**
   - In AWS Console, search for "App Runner"
   - Click "Create service"

2. **Source Configuration:**
   - **Source:** GitHub
   - **Connect to GitHub:** Authorize AWS to access your GitHub
   - **Repository:** Select your `qoe_tool` repository
   - **Branch:** `main`
   - **Deployment trigger:** Automatic (on push)

3. **Build Settings:**
   - **Configuration file:** Use default (auto-detect)
   - Or create `apprunner.yaml`:
     ```yaml
     version: 1.0
     build:
       commands:
         build:
           - echo "Building QoE Tool"
     run:
       runtime-version: 3.11
       command: streamlit run app/ui/app.py --server.port=8501 --server.address=0.0.0.0
       network:
         port: 8501
         env: PORT
     ```

4. **Service Settings:**
   - **Service name:** `qoe-tool`
   - **Virtual CPU:** 1 vCPU
   - **Memory:** 2 GB
   - **Auto scaling:** Enabled (min 1, max 5)

5. **Review and Create:**
   - Review settings
   - Click "Create & deploy"

6. **Wait for Deployment:**
   - Build takes 5-10 minutes
   - Watch progress in App Runner console

7. **Get Your URL:**
   - After deployment, you'll see:
   - **Service URL:** `https://xxxxx.us-east-1.awsapprunner.com`
   - This is your live app URL!

---

## Option 2: AWS EC2 (More Control)

### Step 1: Launch EC2 Instance

1. **Navigate to EC2:**
   - Search "EC2" in AWS Console
   - Click "Launch instance"

2. **Configure Instance:**
   - **Name:** `qoe-tool-server`
   - **AMI:** Amazon Linux 2023 or Ubuntu 22.04 LTS
   - **Instance type:** `t3.small` (2 vCPU, 2 GB RAM) - Free tier eligible: `t2.micro`
   - **Key pair:** Create new or use existing
   - **Network settings:** 
     - Allow HTTP (port 80)
     - Allow HTTPS (port 443)
     - Allow custom TCP (port 8501)

3. **Launch Instance:**
   - Click "Launch instance"
   - Wait for instance to be "Running"

### Step 2: Connect to EC2

1. **Get Public IP:**
   - In EC2 console, note the Public IPv4 address

2. **SSH Connect (Windows):**
   ```powershell
   # Using PowerShell
   ssh -i "your-key.pem" ec2-user@YOUR_PUBLIC_IP
   
   # Or use PuTTY/WinSCP
   ```

3. **SSH Connect (Mac/Linux):**
   ```bash
   chmod 400 your-key.pem
   ssh -i "your-key.pem" ec2-user@YOUR_PUBLIC_IP
   ```

### Step 3: Install Dependencies on EC2

```bash
# Update system
sudo yum update -y  # Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.11
sudo yum install python3.11 python3.11-pip -y  # Amazon Linux
# OR
sudo apt install python3.11 python3.11-pip -y  # Ubuntu

# Install Git
sudo yum install git -y  # Amazon Linux
# OR
sudo apt install git -y  # Ubuntu

# Install other dependencies
sudo yum install gcc -y  # Amazon Linux
```

### Step 4: Deploy Application

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/qoe_tool.git
cd qoe_tool

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Streamlit
pip install streamlit

# Run application
streamlit run app/ui/app.py --server.port=8501 --server.address=0.0.0.0
```

### Step 5: Run as Service (PM2 or systemd)

**Option A: Using PM2 (Recommended)**
```bash
# Install PM2
npm install -g pm2

# Start app with PM2
pm2 start streamlit --name qoe-tool -- run app/ui/app.py --server.port=8501 --server.address=0.0.0.0
pm2 save
pm2 startup
```

**Option B: Using systemd**
```bash
# Create service file
sudo nano /etc/systemd/system/qoe-tool.service
```

Add this content:
```ini
[Unit]
Description=QoE Tool Streamlit App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/qoe_tool
Environment="PATH=/home/ec2-user/qoe_tool/venv/bin"
ExecStart=/home/ec2-user/qoe_tool/venv/bin/streamlit run app/ui/app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable qoe-tool
sudo systemctl start qoe-tool
sudo systemctl status qoe-tool
```

### Step 6: Access Your App

- **URL:** `http://YOUR_PUBLIC_IP:8501`
- Or set up domain with Route 53

---

## Option 3: AWS Elastic Beanstalk (Easy)

### Step 1: Prepare Application

1. **Create `application.py` in root:**
   ```python
   # This is a wrapper for Elastic Beanstalk
   import subprocess
   import sys

   if __name__ == "__main__":
       subprocess.run([
           sys.executable, "-m", "streamlit", "run",
           "app/ui/app.py",
           "--server.port=8080",
           "--server.address=0.0.0.0"
       ])
   ```

2. **Create `Procfile`:**
   ```
   web: python application.py
   ```

### Step 2: Deploy to Elastic Beanstalk

1. **Navigate to Elastic Beanstalk:**
   - Search "Elastic Beanstalk" in AWS Console
   - Click "Create application"

2. **Configure:**
   - **Application name:** `qoe-tool`
   - **Platform:** Python 3.11
   - **Application code:** Upload your code as ZIP
   - **Environment:** Web server environment

3. **Configure more options:**
   - **Instance type:** t3.small
   - **Capacity:** 1-4 instances

4. **Deploy:**
   - Click "Create environment"
   - Wait for deployment (5-10 minutes)

5. **Get URL:**
   - After deployment: `http://qoe-tool.xxxxx.us-east-1.elasticbeanstalk.com`

---

## 🔒 Security Best Practices

### ⚠️ IMPORTANT: Secure Your Credentials

1. **Don't use root account:**
   - Create IAM user with limited permissions
   - Use IAM roles instead of access keys when possible

2. **Set up IAM User:**
   ```
   AWS Console → IAM → Users → Add user
   - User name: qoe-tool-deploy
   - Access type: Programmatic access
   - Permissions: Attach policies (EC2FullAccess or AppRunnerFullAccess)
   ```

3. **Use Environment Variables:**
   - Never hardcode credentials
   - Use AWS Secrets Manager or Parameter Store

---

## 📋 Quick Deployment Checklist

### Before Deployment:
- [ ] Code pushed to GitHub
- [ ] `requirements.txt` is complete
- [ ] `Dockerfile` created (for App Runner)
- [ ] Tested locally
- [ ] Security groups configured (for EC2)

### After Deployment:
- [ ] App is accessible via URL
- [ ] Can upload files
- [ ] Processing works
- [ ] Download works
- [ ] Set up custom domain (optional)

---

## 🌐 Setting Up Custom Domain (Optional)

### Using Route 53:

1. **Register/Buy Domain:**
   - AWS Route 53 → Registered domains
   - Or use existing domain

2. **Create Hosted Zone:**
   - Route 53 → Hosted zones → Create
   - Add your domain

3. **Update DNS:**
   - Point A record to your App Runner/EC2 IP
   - Or use CNAME for App Runner

4. **Configure SSL:**
   - AWS Certificate Manager (ACM)
   - Request certificate for your domain
   - Attach to App Runner/ALB

---

## 💰 Cost Estimation

### App Runner:
- **Free tier:** None
- **Cost:** ~$0.007/hour (~$5/month for 1 vCPU, 2GB RAM)

### EC2:
- **Free tier:** t2.micro (750 hours/month for 12 months)
- **Cost:** ~$0.012/hour (~$8.64/month for t3.small)

### Elastic Beanstalk:
- **Free tier:** None (but uses EC2)
- **Cost:** Same as EC2 + small overhead

---

## 🔗 Your Deployment URLs

After deployment, you'll get:

**App Runner:**
```
https://xxxxx.us-east-1.awsapprunner.com
```

**EC2:**
```
http://YOUR_PUBLIC_IP:8501
```

**Elastic Beanstalk:**
```
http://qoe-tool.xxxxx.us-east-1.elasticbeanstalk.com
```

---

## 🆘 Troubleshooting

### App Not Loading:
1. Check security groups (ports 80, 443, 8501)
2. Check instance status (running)
3. Check application logs
4. Verify dependencies installed

### File Upload Issues:
1. Check file size limits (200MB default)
2. Check disk space on EC2
3. Verify temp directory permissions

### Performance Issues:
1. Increase instance size
2. Enable auto-scaling
3. Use CloudFront CDN

---

## 📞 Support

If you encounter issues:
1. Check AWS CloudWatch logs
2. Check application logs
3. Verify all dependencies in requirements.txt
4. Test locally first

---

## ✅ Recommended: App Runner

**For your QoE Tool, I recommend AWS App Runner because:**
- ✅ Easiest setup (just connect GitHub)
- ✅ Automatic deployments on git push
- ✅ Built-in HTTPS/SSL
- ✅ Auto-scaling
- ✅ No server management
- ✅ Perfect for Streamlit apps

**Estimated time to deploy: 15-20 minutes**

Good luck with your deployment! 🚀

