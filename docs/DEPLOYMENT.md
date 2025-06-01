# MCP Hub Bootstrap Installer Deployment Guide

This guide covers deploying the complete bootstrap installer system for MCP Hub.

## Architecture Overview

```
User runs: curl -fsSL https://get.mcphub.io | bash
     ↓
Web Service (get.mcphub.io)
     ↓
Detects User-Agent → Serves install.sh script
     ↓
Script detects platform → Downloads pre-built binaries from GitHub Releases
     ↓
Fallback: Build from source if binaries unavailable
```

## Deployment Steps

### 1. Set Up GitHub Releases

The system is already configured with GitHub Actions that will:
- Build multi-platform binaries on every tag push
- Create releases with proper binary naming
- Host install.sh script in releases

To trigger a release:
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 2. Deploy Web Service

Choose one of these hosting options:

#### Option A: Heroku (Recommended for simplicity)
```bash
cd web
heroku create your-app-name
git add .
git commit -m "Add web service"
git subtree push --prefix web heroku main
```

#### Option B: Railway
```bash
cd web
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

#### Option C: Vercel
```bash
cd web
npm i -g vercel
vercel --prod
```

#### Option D: Self-hosted with Docker
```bash
cd web
docker build -t mcphub-download .
docker run -p 80:5000 mcphub-download
```

### 3. Configure Domain

Point your domain (e.g., `get.mcphub.io`) to your hosting service:

- **Heroku**: Add custom domain in Heroku dashboard
- **Railway**: Configure custom domain in Railway dashboard  
- **Vercel**: Add domain in Vercel dashboard
- **Self-hosted**: Point A record to your server IP

### 4. Test Installation

Once deployed, test the complete system:

```bash
# Test the web service
curl -fsSL https://your-domain.com | head

# Test with browser (should show landing page)
open https://your-domain.com

# Test full installation (use --skip-deps for safety)
curl -fsSL https://your-domain.com | bash -s -- --skip-deps
```

## Configuration

### Environment Variables

For the web service, you can configure:

- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: false)

### GitHub Repository

Update these in the web service if you fork the project:
- `GITHUB_REPO`: Your repository (default: "saxyguy81/mcp-hub")

## Monitoring

### Health Checks

The web service includes a health endpoint:
```bash
curl https://your-domain.com/health
```

### Logs

Monitor your hosting platform's logs for errors:
- **Heroku**: `heroku logs --tail`
- **Railway**: Check Railway dashboard
- **Vercel**: Check Vercel dashboard

## Security

### SSL/TLS

Ensure your domain uses HTTPS:
- Most hosting platforms provide automatic SSL
- For self-hosted, use Let's Encrypt or similar

### Rate Limiting

Consider adding rate limiting for production:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)
```

## Troubleshooting

### Common Issues

1. **Script not found**: Check GitHub releases have `install.sh`
2. **Download failures**: Verify release binary naming matches install script
3. **CORS issues**: Web browsers may block mixed HTTP/HTTPS content

### Debug Mode

Enable debug mode for troubleshooting:
```bash
export DEBUG=true
python server.py
```

## Backup Strategy

The system is designed to be resilient:
- **Primary**: Download from GitHub releases
- **Fallback 1**: Local install.sh in web service
- **Fallback 2**: Build from source

This ensures installation works even if one component fails.

## Future Enhancements

Consider adding:
- Analytics/usage tracking
- CDN for faster global downloads  
- Package manager support (Homebrew, apt, chocolatey)
- Signature verification for enhanced security
