# Step-by-Step: Deploy Frontend to AWS Amplify

## Step 1: Access AWS Amplify

1. Go to **AWS Console**: https://console.aws.amazon.com
2. Login with your AWS account
3. In the top search bar, type: **"Amplify"**
4. Click on **"AWS Amplify"** service

---

## Step 2: Create New App

1. Click the orange **"New app"** button (top right)
2. From dropdown, click **"Host web app"**

---

## Step 3: Connect GitHub Repository

1. You'll see options: **"GitHub"**, **"GitLab"**, **"Bitbucket"**, **"CodeCommit"**
2. Click **"GitHub"**
3. Click **"Connect branch"** button

**First Time?**
- If you see "Authorize AWS Amplify", click **"Authorize AWS Amplify"**
- You'll be redirected to GitHub
- Click **"Authorize"** button
- Return to AWS Amplify console

**Already Connected?**
- You'll see your GitHub account name

---

## Step 4: Select Repository and Branch

1. **Repository dropdown:** Select **"UmarShoaib-Code/QoE"**
2. **Branch dropdown:** Select **"main"**
3. Click **"Next"** (bottom right)

---

## Step 5: Configure Build Settings

**Option A: Auto-detection (Recommended)**

If Amplify auto-detects `amplify.yml`:
- ✅ Leave everything as is
- Click **"Next"**

**Option B: Manual Configuration**

If no auto-detection:
1. Click **"Edit"** button (in Build settings section)
2. **App build specification:** Select **"amplify.yml"**
3. Confirm the file path shows: `amplify.yml`
4. Click **"Next"**

*(Note: Your `amplify.yml` file should already be in the repository root)*

---

## Step 6: Set Environment Variable (CRITICAL!)

This connects your frontend to the backend.

1. Scroll down to **"Environment variables"** section
2. Click **"Add environment variable"**
3. Fill in:
   - **Key:** `VITE_API_URL`
   - **Value:** `http://13.62.98.63:8000`
4. Click **"Save"** (next to the variable)

**IMPORTANT:** Double-check the value is exactly: `http://13.62.98.63:8000`

---

## Step 7: Review and Deploy

1. Review your settings:
   - ✅ Repository: UmarShoaib-Code/QoE
   - ✅ Branch: main
   - ✅ Build settings: amplify.yml
   - ✅ Environment variable: VITE_API_URL = http://13.62.98.63:8000

2. Click **"Save and deploy"** (orange button, bottom right)

---

## Step 8: Watch Deployment Progress

You'll see a deployment screen with stages:

**Stage 1: Provision**
- Creating Amplify app...
- ⏳ Wait ~30 seconds

**Stage 2: Build**
- Installing dependencies...
- Building React app...
- ⏳ Wait 3-5 minutes

**Stage 3: Deploy**
- Uploading to CDN...
- ⏳ Wait 1-2 minutes

**Total time: 5-10 minutes**

You can see live logs by clicking on each stage.

---

## Step 9: Get Your Live URL

Once you see **green checkmarks** ✅ on all stages:

1. Look at the top of the page
2. You'll see: **"Deployment completed successfully"**
3. Find the **"App URL"** or **"Live URL"**
4. It looks like: `https://main.xxxxx.amplifyapp.com`

**Click on this URL to open your live app!**

---

## Step 10: Test Your Live Application

1. Open the Amplify URL in browser
2. Test the app:
   - ✅ Landing page loads
   - ✅ Login/Signup works
   - ✅ Dashboard loads
   - ✅ File upload works
   - ✅ Backend API calls work

---

## Troubleshooting

### Build Failed?

**Check:**
1. Go to **"Build settings"** → Click on failed build
2. Look at logs - usually shows the error
3. Common issues:
   - Missing `amplify.yml` → Verify it's in repository root
   - Node version issue → Check `package.json`
   - Build errors → Check frontend code

**Fix:**
- Update code on GitHub
- Amplify auto-rebuilds (or click "Redeploy")

### Frontend Can't Connect to Backend?

**Check:**
1. Verify environment variable:
   - Amplify Console → App Settings → Environment variables
   - `VITE_API_URL` = `http://13.62.98.63:8000`

2. Test backend directly:
   - Open: `http://13.62.98.63:8000/docs`
   - Should show FastAPI docs

3. Rebuild frontend:
   - Amplify Console → Click "Redeploy this version"

### Environment Variable Not Working?

**Solution:**
1. Amplify Console → App Settings → Environment variables
2. Edit `VITE_API_URL`
3. Save
4. Redeploy (click "Redeploy this version")

---

## Quick Reference

**Your URLs:**
- Frontend: `https://main.xxxxx.amplifyapp.com` (from Amplify)
- Backend: `http://13.62.98.63:8000` (EC2)
- API Docs: `http://13.62.98.63:8000/docs`

**Where to Find:**
- Amplify Console: https://console.aws.amazon.com/amplify
- Your App: Search "qoe" in Amplify apps list

---

## Success Checklist

After deployment, verify:
- ✅ Frontend loads without errors
- ✅ Login page works
- ✅ Dashboard accessible
- ✅ File upload connects to backend
- ✅ API calls return data

**You're live! 🚀**

