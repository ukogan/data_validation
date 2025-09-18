/**
 * ODCV Analytics Static File Server
 * Simple Express server for serving static analytics dashboard files
 */

const express = require('express');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS for cross-origin requests
app.use(cors());

// Serve static files from public directory
app.use('/public', express.static(path.join(__dirname, 'public')));

// Serve static files from root directory (for HTML files)
app.use(express.static(__dirname));

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

app.listen(PORT, () => {
    console.log(`ODCV Analytics server running on port ${PORT}`);
    console.log(`Health check available at: http://localhost:${PORT}/api/health`);
    console.log(`Timeline viewer at: http://localhost:${PORT}/`);
});

module.exports = app;