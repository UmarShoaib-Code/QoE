# EC2 Setup Commands - Quick Reference

Your EC2 IP: **13.62.98.63**

## Continue from where you stopped:

Ubuntu 24.04 uses Python 3.12 by default (works with your code). Continue with:

```bash
# Install Git
sudo apt install -y git

# Check Python version (should be 3.12)
python3 --version

# Clone repository
git clone https://github.com/UmarShoaib-Code/QoE.git
cd QoE

# Create virtual environment with Python 3.12
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create output directory
mkdir -p output

# Test backend (press Ctrl+C to stop)
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

**If backend starts successfully, continue with Step 8 in DEPLOYMENT_GUIDE.md**

