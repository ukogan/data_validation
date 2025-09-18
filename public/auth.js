/**
 * ODCV Analytics Authentication Manager
 * Simplified authentication for timeline viewer
 */

class ODCVAnalyticsAuth {
    constructor() {
        this.session = null;

        console.log('[ODCV-Analytics-Auth] Initializing authentication...');

        // Check authentication first
        if (!this.checkAuthentication()) {
            return; // Will redirect to login
        }

        this.initializeElements();
        this.bindEvents();
        this.displayUserInfo();

        console.log('[ODCV-Analytics-Auth] ✅ Authentication initialized successfully');
    }

    checkAuthentication() {
        console.log('[ODCV-Analytics-Auth] Checking authentication status...');

        try {
            const sessionData = localStorage.getItem('odcv_analytics_session');
            if (!sessionData) {
                console.log('[ODCV-Analytics-Auth] No session found, redirecting to login');
                window.location.href = '/login.html';
                return false;
            }

            const session = JSON.parse(sessionData);
            if (!session.authenticated || !session.user) {
                console.log('[ODCV-Analytics-Auth] Invalid session, redirecting to login');
                localStorage.removeItem('odcv_analytics_session');
                window.location.href = '/login.html';
                return false;
            }

            // Check if session is too old (24 hours)
            const sessionAge = Date.now() - new Date(session.authenticatedAt).getTime();
            if (sessionAge > 24 * 60 * 60 * 1000) {
                console.log('[ODCV-Analytics-Auth] Session expired, redirecting to login');
                localStorage.removeItem('odcv_analytics_session');
                window.location.href = '/login.html';
                return false;
            }

            this.session = session;
            console.log('[ODCV-Analytics-Auth] ✅ User authenticated:', session.user.name);
            return true;

        } catch (error) {
            console.error('[ODCV-Analytics-Auth] Error checking authentication:', error);
            localStorage.removeItem('odcv_analytics_session');
            window.location.href = '/login.html';
            return false;
        }
    }

    initializeElements() {
        // Try to find user info elements in the navigation
        this.userInfo = document.getElementById('user-info');
        this.userAvatar = document.getElementById('user-avatar');
        this.userName = document.getElementById('user-name');
        this.userEmail = document.getElementById('user-email');
        this.logoutBtn = document.getElementById('logout-btn');

        // Create user info elements if they don't exist (for pages without navigation)
        if (!this.userInfo) {
            this.createUserInfoSection();
        }
    }

    createUserInfoSection() {
        // Create a simple user info section at the top of the page
        const userInfoHtml = `
            <div id="user-info" style="
                position: fixed;
                top: 10px;
                right: 10px;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
            ">
                <img id="user-avatar" src="" alt="User" style="width: 32px; height: 32px; border-radius: 50%; border: 2px solid #e5e7eb;">
                <div>
                    <div id="user-name" style="font-weight: 600; color: #1f2937;">-</div>
                    <div id="user-email" style="font-size: 12px; color: #6b7280;">-</div>
                </div>
                <button id="logout-btn" style="
                    background: #ef4444;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    font-weight: 600;
                ">Sign Out</button>
            </div>
        `;

        document.body.insertAdjacentHTML('afterbegin', userInfoHtml);

        // Re-initialize elements
        this.userInfo = document.getElementById('user-info');
        this.userAvatar = document.getElementById('user-avatar');
        this.userName = document.getElementById('user-name');
        this.userEmail = document.getElementById('user-email');
        this.logoutBtn = document.getElementById('logout-btn');
    }

    bindEvents() {
        // Logout button
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }

    displayUserInfo() {
        if (!this.session || !this.session.user) {
            return;
        }

        const user = this.session.user;

        // Show user info section
        if (this.userInfo) {
            this.userInfo.style.display = 'flex';
            if (this.userInfo.classList) {
                this.userInfo.classList.add('authenticated');
            }
        }

        // Update user avatar
        if (this.userAvatar) {
            if (user.imageUrl) {
                this.userAvatar.src = user.imageUrl;
            } else {
                // Use a default avatar or initials
                this.userAvatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=1e3a8a&color=fff`;
            }
            this.userAvatar.alt = user.name;
        }

        // Update user name
        if (this.userName) {
            this.userName.textContent = user.name;
        }

        // Update user email
        if (this.userEmail) {
            this.userEmail.textContent = user.email;
        }

        console.log('[ODCV-Analytics-Auth] User info displayed for:', user.name);
    }

    logout() {
        console.log('[ODCV-Analytics-Auth] Logging out user...');

        // Clear session
        localStorage.removeItem('odcv_analytics_session');

        // Clear any cached data
        if (window.odcvAnalyticsSession) {
            delete window.odcvAnalyticsSession;
        }

        // Redirect to login
        window.location.href = '/login.html';
    }

    // Utility method to get current user info
    getCurrentUser() {
        return this.session ? this.session.user : null;
    }

    // Utility method to get access token
    getAccessToken() {
        return this.session ? this.session.accessToken : null;
    }

    // Utility method to check if user is authenticated
    isAuthenticated() {
        return this.session && this.session.authenticated;
    }
}

// Initialize authentication when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[ODCV-Analytics-Auth] DOM loaded, initializing authentication...');
    window.odcvAnalyticsAuth = new ODCVAnalyticsAuth();
});

// Also expose globally for other scripts
window.ODCVAnalyticsAuth = ODCVAnalyticsAuth;