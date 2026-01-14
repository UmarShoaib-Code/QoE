# Fix SSH Permission Denied Error

## Quick Fixes (Try in Order)

### Fix 1: Use Git Bash or WSL (Recommended)

**Option A: Git Bash**
1. Open Git Bash (if installed)
2. Navigate to Downloads:
   ```bash
   cd /c/Users/"HP ULTRA 7"/Downloads
   ```
3. Set permissions:
   ```bash
   chmod 400 pm.pem
   ```
4. Connect:
   ```bash
   ssh -i pm.pem ec2-user@16.170.248.106
   ```

**Option B: WSL (Windows Subsystem for Linux)**
```bash
# In WSL terminal
cd /mnt/c/Users/"HP ULTRA 7"/Downloads
chmod 400 pm.pem
ssh -i pm.pem ec2-user@16.170.248.106
```

### Fix 2: Verify Key Pair Name

1. **Check EC2 Instance:**
   - AWS Console → EC2 → Instances
   - Select your instance
   - Check "Key pair name" in details
   - Make sure it matches your `pm.pem` key

2. **If key doesn't match:**
   - You need to use the correct key pair
   - Or launch a new instance with `pm` key pair

### Fix 3: Use OpenSSH Format (Windows 10/11)

```powershell
# In PowerShell (as Administrator)
cd "C:\Users\HP ULTRA 7\Downloads"

# Try with verbose output to see error
ssh -v -i "pm.pem" ec2-user@16.170.248.106

# Or try specifying the key explicitly
ssh -i ".\pm.pem" -o IdentitiesOnly=yes ec2-user@16.170.248.106
```

### Fix 4: Check Security Group

1. **AWS Console → EC2 → Security Groups**
2. Find your instance's security group
3. **Inbound rules** must allow:
   - **Type:** SSH
   - **Port:** 22
   - **Source:** Your IP or 0.0.0.0/0 (temporarily for testing)

### Fix 5: Use PuTTY (Alternative)

1. **Download PuTTY:** https://www.putty.org/
2. **Download PuTTYgen:** Included with PuTTY
3. **Convert .pem to .ppk:**
   - Open PuTTYgen
   - Click "Load" → Select `pm.pem`
   - Click "Save private key" → Save as `pm.ppk`
4. **Connect with PuTTY:**
   - Host: `16.170.248.106`
   - Port: `22`
   - Connection type: SSH
   - Auth → Credentials → Browse → Select `pm.ppk`
   - Click "Open"

### Fix 6: Verify Instance Status

1. **AWS Console → EC2 → Instances**
2. Check instance state: Must be "Running"
3. Check status checks: Should be "2/2 checks passed"

---

## Most Likely Solution

**The key pair name doesn't match!**

1. **Check your instance:**
   - EC2 → Instances → Select instance
   - Look at "Key pair name" in details tab

2. **If it's different:**
   - You need the correct `.pem` file
   - Or create new key pair and relaunch instance

---

## Quick Test Command

Try this in PowerShell:
```powershell
ssh -v -i "C:\Users\HP ULTRA 7\Downloads\pm.pem" ec2-user@16.170.248.106
```

The `-v` flag shows detailed error messages to help diagnose.

---

## Alternative: Use AWS Systems Manager Session Manager

If SSH still doesn't work:

1. **AWS Console → EC2 → Instances**
2. Select your instance
3. Click "Connect" → "Session Manager" tab
4. Click "Connect"
5. Opens browser-based terminal (no SSH needed!)

---

**Most common issue:** Key pair name mismatch. Check your instance details first!

