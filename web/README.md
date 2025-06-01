# MCP Hub Download Service

A simple web service that serves the MCP Hub installation script and provides a user-friendly landing page.

## Features

- **Smart Content Delivery**: Serves raw script to curl/wget, landing page to browsers
- **Fallback Support**: Uses local script if GitHub is unavailable
- **API Endpoints**: Provides release information via REST API
- **Health Checks**: Built-in health monitoring endpoint

## Deployment

### Local Development

```bash
cd web
pip install -r requirements.txt
python server.py
```

### Production Deployment

#### Heroku

```bash
# Create Procfile
echo "web: gunicorn server:app" > Procfile

# Deploy
heroku create mcphub-download
git push heroku main
heroku config:set DEBUG=false
```

#### Railway

```bash
# railway.toml will be auto-detected
railway up
```

#### Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

#### Docker

```bash
docker build -t mcphub-download .
docker run -p 5000:5000 mcphub-download
```

## Environment Variables

- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: false)

## Endpoints

- `GET /`: Landing page or install script (based on User-Agent)
- `GET /install.sh`: Force download install script
- `GET /api/releases`: Get all releases from GitHub
- `GET /api/latest`: Get latest release information
- `GET /health`: Health check endpoint

## Usage

Once deployed, users can install MCP Hub with:

```bash
curl -fsSL https://get.mcphub.io | bash
```

(Replace `get.mcphub.io` with your actual domain)
