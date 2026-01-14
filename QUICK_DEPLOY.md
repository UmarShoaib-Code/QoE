# 🚀 Quick Deploy Guide - 5 Minutes

## Step 1: Push to GitHub (2 min)

```bash
# If not already a git repo
git init
git add .
git commit -m "Ready for deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/qoe_tool.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Streamlit Cloud (3 min)

1. **Go to:** https://share.streamlit.io
2. **Sign in** with GitHub
3. **Click:** "New app"
4. **Fill in:**
   - Repository: `YOUR_USERNAME/qoe_tool`
   - Branch: `main`
   - Main file path: `app/ui/app.py`
5. **Click:** "Deploy"

## Step 3: Done! 🎉

Your app will be live at:
```
https://YOUR_APP_NAME.streamlit.app
```

---

## ✅ Files Already Created:

- ✅ `requirements.txt` - Dependencies
- ✅ `.streamlit/config.toml` - Streamlit config
- ✅ `DEPLOYMENT_GUIDE.md` - Full deployment guide

## 📝 That's It!

Your QoE Tool will be:
- ✅ Free forever
- ✅ Auto-updates on git push
- ✅ HTTPS enabled
- ✅ No server management needed

**Total time: ~5 minutes!**

