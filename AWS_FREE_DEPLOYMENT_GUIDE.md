# AWS FREE Deployment Guide - QoE Tool

## Free Option: AWS Amplify (Frontend) + EC2 Free Tier (Backend)

**Cost: $0/month (Free for 12 months, then minimal cost)**

### Free Tier Components:

1. **AWS Amplify** - React Frontend
   - ✅ 1000 build minutes/month (FREE)
   - ✅ 5GB storage (FREE)
   - ✅ 15GB data transfer/month (FREE)
   - ✅ SSL/HTTPS included (FREE)
   - ✅ Global CDN (FREE)
   - **Truly free for small apps**

2. **EC2 Free Tier** - FastAPI Backend
   - ✅ t2.micro instance for 12 months (FREE)
   - ✅ 750 hours/month (FREE for 12 months)
   - ✅ 1GB RAM, 1 vCPU
   - After 12 months: ~$8/month

3. **AWS RDS Free Tier** - MySQL Database (Optional)
   - ✅ db.t2.micro for 12 months (FREE)
   - ✅ 20GB storage (FREE)
   - After 12 months: ~$15/month

### Total Cost:
- **First 12 months: $0/month** ✅
- **After 12 months: ~$8-23/month** (EC2 required, RDS optional)

---

## Architecture:

```
Internet
  │
  ├─→ AWS Amplify (React Frontend) - FREE
  │     └─→ Global CDN + HTTPS
  │
  └─→ EC2 t2.micro (FastAPI Backend) - FREE (12 months)
        └─→ Port 8000
        └─→ Connects to RDS or local MySQL
```

---

## What We Need to Fix Before Deployment:

1. ✅ Update Dockerfile for FastAPI (instead of Streamlit)
2. ✅ Fix hardcoded `localhost:8000` in download function
3. ✅ Update CORS to allow Amplify domain
4. ✅ Create production Dockerfile and configuration
5. ✅ Set up environment variables

---

## Deployment Steps Overview:

### Part 1: Deploy React Frontend to AWS Amplify
1. Build React frontend
2. Push to GitHub
3. Connect GitHub to AWS Amplify
4. Configure environment variables
5. Deploy automatically

### Part 2: Deploy FastAPI Backend to EC2 Free Tier
1. Launch EC2 t2.micro instance (free tier)
2. Install Docker and dependencies
3. Clone GitHub repository
4. Set up environment variables
5. Run backend with Docker or directly
6. Configure security groups

### Part 3: Connect Frontend to Backend
1. Update Amplify environment variables with EC2 backend URL
2. Configure CORS on backend
3. Test connection

### Part 4: Database Setup (Optional)
- Use EC2 local MySQL (free) OR
- Use AWS RDS free tier (12 months free)

---

## Alternative: Everything on EC2 (Simpler)

**Single EC2 t2.micro Instance:**
- Run React frontend (Nginx)
- Run FastAPI backend
- Run MySQL locally
- **Cost: $0/month for 12 months**

This is simpler but less scalable.

---

## Recommendation:

**Use: AWS Amplify (Frontend) + EC2 Free Tier (Backend)**

**Why:**
- ✅ Completely free for 12 months
- ✅ Amplify gives you global CDN (faster worldwide)
- ✅ Automatic deployments from GitHub
- ✅ Professional setup
- ✅ SSL/HTTPS included free
- ✅ After 12 months, only ~$8/month for EC2

**Ready to proceed?** I'll create all necessary configuration files and provide step-by-step instructions.

