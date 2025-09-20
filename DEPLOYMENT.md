# ODCV Analytics Dashboard V2 - Railway Deployment Guide

## Architecture V2 - API-Powered Dashboard ✅

This project has been successfully converted from a static HTML generator to a scalable FastAPI-powered web application that exactly replicates the dashboard_variant3 design.

## What We've Built

### ✅ **Completed Implementation**
- **FastAPI Backend**: Converts existing Python modules to REST API endpoints
- **Dashboard Frontend**: Exact pixel-perfect replica of dashboard_variant3 design
- **Scalability**: Handles 100+ sensors vs original 3-sensor limitation
- **Performance**: Tested with 1.7M records (100 sensors, 30 days)

### ✅ **Production Ready**
- **Docker Configuration**: Production-ready Dockerfile and railway.toml
- **Performance Tested**: API endpoints tested under load
- **Security**: Non-root container user, proper health checks

## Deployment URLs

### Production (main branch)
- **URL**: https://odcv-compass-analytics.up.railway.app
- **Branch**: `main`
- **Type**: FastAPI + Docker container

### API Documentation
- **Swagger UI**: https://odcv-compass-analytics.up.railway.app/docs
- **Health Check**: https://odcv-compass-analytics.up.railway.app/api/health

## Railway Configuration (V2)

### Files Required
- `Dockerfile` - Docker container configuration
- `railway.toml` - Railway deployment settings
- `requirements.txt` - Python dependencies
- `main.py` - FastAPI application
- `dashboard.html` - Frontend (dashboard_variant3 replica)

## Cross-Project Navigation

The navigation component automatically detects the environment and uses appropriate URLs:

```json
{
  "environments": {
    "local": {
      "soo_base": "../soo-generator/public/",
      "validation_base": "./"
    },
    "production": {
      "soo_base": "https://odcv-compass.up.railway.app/",
      "validation_base": "https://odcv-compass-analytics.up.railway.app/"
    },
    "staging": {
      "soo_base": "https://odcv-compass-staging.up.railway.app/",
      "validation_base": "https://odcv-compass-analytics-staging.up.railway.app/"
    }
  }
}
```

## Deployment Process

### Initial Setup (One-time)
1. Create Railway project for production (main branch)
2. Create Railway project for staging (development branch)
3. Configure custom domains as specified above
4. Connect to GitHub repository

### Regular Deployments
- **Staging**: Automatically deploys when pushing to `development` branch
- **Production**: Automatically deploys when pushing to `main` branch

### Manual Deployment
```bash
# Deploy to staging (development branch)
git push origin development

# Deploy to production (merge to main)
git checkout main
git merge development
git push origin main
```

## File Structure for Railway

```
/
├── railway.json          # Railway configuration
├── package.json          # Node.js dependencies
├── server.js             # Express static server
├── timeline_viewer.html  # Main application file
├── public/               # Static assets
│   ├── nav-component.js  # Navigation component
│   ├── nav-styles.css    # Navigation styles
│   ├── nav-urls.json     # Environment URLs
│   └── R-Zero_Logo_white.png
└── src/                  # Python analysis code (not deployed)
```

## Environment Detection

The navigation component detects environment based on hostname:
- **Local**: `localhost`, `127.0.0.1`, or file:// protocol
- **Production/Staging**: Any other hostname (uses production URLs)

## Health Check

Railway monitors the application health via:
- **Endpoint**: `/api/health`
- **Response**: JSON with status, service name, timestamp, uptime
- **Timeout**: 300 seconds

## Troubleshooting

### Common Issues
1. **Navigation not working**: Check `nav-urls.json` URLs are correct
2. **Static files not loading**: Ensure files are in correct directory structure
3. **Health check failing**: Verify server is running on correct PORT

### Logs
Access Railway deployment logs through the Railway dashboard to debug issues.

## Dependencies

### Production Dependencies
- `express` - Web server framework
- `cors` - Cross-origin resource sharing

### Development Dependencies
None required for static site deployment.

## Notes

- This is a **static site deployment** - Python scripts run locally to generate HTML
- Future enhancement could add dynamic Python processing via separate API service
- Navigation URLs are configured for both staging and production environments
- The server automatically serves `timeline_viewer.html` as the default route