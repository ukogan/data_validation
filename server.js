/**
 * ODCV Analytics Static File Server
 * Express server for serving static analytics dashboard files with Google authentication
 */

// Load environment variables from .env file (if it exists)
try {
    require('dotenv').config({ path: require('path').join(__dirname, '.env') });
} catch (error) {
    // .env file not found or dotenv not available - use environment variables directly
    console.log('[ODCV Analytics] Using environment variables directly (no .env file)');
}

const express = require('express');
const path = require('path');
const cors = require('cors');
// Note: Using built-in fetch (Node.js 18+) instead of node-fetch

const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS for cross-origin requests
app.use(cors());

// Parse JSON request bodies
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// Serve static files from public directory
app.use('/public', express.static(path.join(__dirname, 'public')));

// Serve static files from root directory (for HTML files)
app.use(express.static(__dirname));

// Google authentication configuration endpoint
app.get('/api/google-config', (req, res) => {
  // Ensure the Google OAuth credentials are set
  const clientId = process.env.GOOGLE_CLIENT_ID;
  if (!clientId || clientId === 'your-google-oauth-client-id') {
    console.warn('[ODCV Analytics] WARNING: GOOGLE_CLIENT_ID not properly configured');
  }

  res.json({
    clientId: process.env.GOOGLE_CLIENT_ID,
    apiKey: process.env.GOOGLE_API_KEY,
    scopes: 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
    discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest']
  });
});

// Google Drive document download proxy (for future use)
app.post('/api/google-drive/download', async (req, res) => {
  try {
    const { fileId, mimeType, accessToken } = req.body;

    if (!fileId || !accessToken) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fileId or accessToken'
      });
    }

    console.log(`[ODCV Analytics] Proxying Google Drive download for file: ${fileId}`);

    // Determine download URL based on MIME type
    let downloadUrl;
    if (mimeType === 'application/vnd.google-apps.document') {
      downloadUrl = `https://www.googleapis.com/drive/v3/files/${fileId}/export?mimeType=text/plain`;
    } else if (mimeType === 'application/pdf') {
      downloadUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`;
    } else if (mimeType.startsWith('text/')) {
      downloadUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`;
    } else {
      downloadUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`;
    }

    const response = await fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (!response.ok) {
      throw new Error(`Google Drive API error: ${response.status} ${response.statusText}`);
    }

    const content = await response.text();
    console.log(`[ODCV Analytics] Document downloaded successfully, length: ${content.length} characters`);

    res.json({
      success: true,
      content: content
    });

  } catch (error) {
    console.error('[ODCV Analytics] Google Drive download error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Health check endpoint for Railway
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'odcv-analytics',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// Root route - serve timeline viewer
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'timeline_viewer.html'));
});

// Login route - serve login page from public directory
app.get('/login.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

// Catch-all route for SPA behavior
app.get('*', (req, res) => {
    // For any other route, try to serve the requested file
    // or fall back to timeline viewer
    const requestedFile = req.path.slice(1); // Remove leading slash
    const filePath = path.join(__dirname, requestedFile);

    // Check if it's an HTML file request
    if (requestedFile.endsWith('.html')) {
        res.sendFile(filePath, (err) => {
            if (err) {
                // If file doesn't exist, serve timeline viewer as fallback
                res.sendFile(path.join(__dirname, 'timeline_viewer.html'));
            }
        });
    } else {
        // For non-HTML requests, return 404
        res.status(404).json({ error: 'File not found' });
    }
});

// Add global error handling for unhandled errors
process.on('uncaughtException', (error) => {
    console.error('[ODCV Analytics] Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('[ODCV Analytics] Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

app.listen(PORT, '0.0.0.0', (err) => {
    if (err) {
        console.error('[ODCV Analytics] Failed to start server:', err);
        process.exit(1);
    }
    console.log(`[ODCV Analytics] Server running on port ${PORT}`);
    console.log(`[ODCV Analytics] Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`[ODCV Analytics] Health check: http://localhost:${PORT}/api/health`);
    console.log(`[ODCV Analytics] Timeline viewer: http://localhost:${PORT}/`);
});

module.exports = app;