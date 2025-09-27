# Screenshot-Based Email Reporting Plan

## Summary
Create an automated daily email reporting system that takes screenshots of the live ODCV dashboard and emails them to recipients. This approach eliminates code duplication and ensures the email reports always match the web interface exactly.

## Implementation Plan

### Phase 1: Headless Browser Integration
1. **Add browser automation dependency** to requirements.txt
   - Add `playwright` or `puppeteer` for headless browser screenshots
   - Include browser installation in Railway deployment

2. **Create screenshot service** (`src/services/screenshot_service.py`)
   - Launch headless browser instance
   - Navigate to dashboard URL with latest data loaded
   - Wait for data loading and chart rendering completion
   - Capture full-page screenshot of dashboard
   - Handle any authentication requirements
   - Save screenshot to temporary file

### Phase 2: Email Service with Screenshot
1. **Create email service** (`src/services/email_service.py`)
   - SMTP configuration using environment variables
   - Email template with embedded screenshot image
   - Attach screenshot file to email
   - Basic text summary (timestamp, data coverage, sensor count)
   - Error handling and delivery confirmation

### Phase 3: Railway Cron Job Implementation
1. **Create scheduled screenshot job** (`daily_screenshot_report.py`)
   - Trigger database data refresh via existing API endpoints
   - Wait for data processing to complete
   - Take dashboard screenshot using screenshot service
   - Send email with screenshot attachment
   - Clean up temporary screenshot files
   - Log execution status and any errors

### Phase 4: Railway Deployment Configuration
1. **Environment variables for Railway**:
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
   - `REPORT_EMAIL_RECIPIENTS` (comma-separated list)
   - `DASHBOARD_URL` (Railway internal or external URL)
   - `REPORT_SCHEDULE` (cron expression for daily timing)

2. **Railway cron job configuration**
   - Set up cron schedule (minimum 5-minute intervals)
   - Configure service to run headless browser
   - Ensure sufficient memory allocation for browser

### Technical Benefits
- ✅ **Zero logic duplication** - uses exact same dashboard rendering
- ✅ **Always synchronized** - any dashboard changes automatically reflected in emails
- ✅ **Visual consistency** - recipients see identical interface to web users
- ✅ **Simpler maintenance** - single source of truth for all metrics
- ✅ **Railway compatible** - headless browsers supported on Railway platform

### Implementation Files to Create
- `src/services/screenshot_service.py` - Browser automation and screenshot capture
- `src/services/email_service.py` - SMTP email delivery with attachments
- `daily_screenshot_report.py` - Main cron job script
- `templates/email_report.html` - Email template with screenshot embedding
- Update `requirements.txt` with browser automation dependencies

### Error Handling Strategy
- Database connection validation before screenshot
- Browser launch failure recovery
- Email delivery retry logic with exponential backoff
- Screenshot file cleanup on success/failure
- Admin notification for repeated failures

This approach leverages existing dashboard functionality while providing automated daily reporting through Railway's cron job capabilities.