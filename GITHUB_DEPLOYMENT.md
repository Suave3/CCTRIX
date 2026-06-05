# 🚀 CCTRIX - Deploy to GitHub

Your project is ready for GitHub! Follow these steps to push your code to GitHub.

## Step 1: Create a Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `cctrix` (or your preferred name)
3. **Important**: Make it **PRIVATE** (free private repos available)
4. **Do NOT** initialize with README, .gitignore, or license (you already have these)
5. Click "Create repository"

## Step 2: Configure Git User (First Time Only)

```powershell
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```

## Step 3: Push to GitHub

Replace `YOUR_USERNAME` with your GitHub username:

```powershell
cd c:\Users\User\OneDrive\Documents\cctrix-main

# Add GitHub as origin
git remote add origin https://github.com/YOUR_USERNAME/cctrix.git

# Rename branch to main (if not already)
git branch -M main

# Push to GitHub
git push -u origin main
```

You'll be prompted for GitHub credentials:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (see below)

## Step 4: Create a Personal Access Token

If you get authentication errors:

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: `cctrix-deployment`
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)
7. Use this token as your password when git asks

## What's Excluded (for Security)

These files are **NOT** pushed (protected by .gitignore):
- `.env` - Contains database passwords and API keys
- `__pycache__/` - Python cache files
- `venv/` - Virtual environment
- `static/logs/*` - Motion detection images
- Database files

## What IS Included

✅ Source code (app.py, database.py, etc.)
✅ Templates (HTML/CSS)
✅ Configuration templates (.env.example)
✅ Requirements (requirements.txt for dependencies)
✅ Documentation (README.md)
✅ Docker setup (Dockerfile, docker-compose.yml)

## After Pushing

Your repository is now on GitHub and can be:
- Deployed to Railway, Heroku, or any cloud platform
- Cloned by others for local development
- Tracked for version control and history

## Verify Push

```powershell
git remote -v  # Should show origin pointing to GitHub
git log        # Should show your commits
```

---

**Current Commit**: `97d0760` - Motion detection optimization with infinite logging
**Last 3 Changes**:
- ✅ Infinite motion logging (every 1 second)
- ✅ Reduced false positive green squares (MIN_CONTOUR_AREA: 150→800)
- ✅ Sync image saves (prevents race conditions)

---

Need help? Check the main README.md for setup and deployment info!
