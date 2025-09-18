/**
 * Compass-SOO Navigation Component v3.0
 * Environment-aware navigation component with external URL configuration
 * Provides consistent left navigation across all pages and projects
 * Updated: 2025-09-17 - Added cross-project navigation support
 * Development ready for future enhancements
 */

(function() {
    'use strict';

    // URL configuration cache
    let urlConfig = null;
    let configLoaded = false;

    /**
     * Load URL configuration from external file
     */
    async function loadUrlConfig() {
        if (configLoaded) return urlConfig;

        try {
            const response = await fetch('nav-urls.json');
            if (!response.ok) {
                throw new Error(`Failed to load nav-urls.json: ${response.status}`);
            }
            urlConfig = await response.json();
            configLoaded = true;
            console.log('Navigation URL config loaded:', urlConfig);
            return urlConfig;
        } catch (error) {
            console.warn('Failed to load navigation URL config, falling back to relative URLs:', error);
            // Fallback configuration for when external config fails
            urlConfig = {
                environments: {
                    local: { soo_base: '', validation_base: '' },
                    production: { soo_base: '', validation_base: '' }
                }
            };
            configLoaded = true;
            return urlConfig;
        }
    }

    /**
     * Detect current environment
     */
    function detectEnvironment() {
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '' || hostname.startsWith('file://')) {
            return 'local';
        }
        return 'production';
    }

    /**
     * Build URL for cross-project navigation
     */
    function buildUrl(project, filename) {
        if (!urlConfig) {
            console.warn('URL config not loaded, using relative path');
            return filename;
        }

        const env = detectEnvironment();
        const envConfig = urlConfig.environments[env];

        if (!envConfig) {
            console.warn(`No configuration found for environment: ${env}`);
            return filename;
        }

        const baseUrl = envConfig[`${project}_base`] || '';
        return baseUrl + filename;
    }

    // Base navigation configuration (URLs will be resolved dynamically)
    const NAV_CONFIG_TEMPLATE = {
        title: 'ODCV Compass',
        logo: 'R-Zero_Logo_white.png',
        items: [
            {
                id: 'generator',
                label: 'Create Draft',
                project: 'soo',
                filename: 'index.html',
                section: 'soo',
                working: true
            },
            {
                id: 'ahu-calculator',
                label: 'Calculate (AHU)',
                project: 'soo',
                filename: 'SOO-calculator.html',
                section: 'soo',
                working: true
            },
            {
                id: 'zone-calculator',
                label: 'Calculate (Zone)',
                project: 'soo',
                filename: 'SOO-zone-calculator.html',
                section: 'soo',
                working: false
            },
            {
                id: 'bacnet-points',
                label: 'BACNET POINTS',
                project: null,
                filename: '#',
                section: 'standalone',
                working: false
            },
            {
                id: 'stanford',
                label: 'Stanford',
                project: 'validation',
                filename: 'timeline_viewer.html',
                section: 'validation',
                working: true
            },
            {
                id: 'energy-savings',
                label: 'ENERGY SAVINGS',
                project: null,
                filename: '#',
                section: 'standalone',
                working: false
            },
            {
                id: 'cost-savings',
                label: 'COST SAVINGS',
                project: null,
                filename: '#',
                section: 'standalone',
                working: false
            }
        ]
    };

    /**
     * Build navigation config with resolved URLs
     */
    async function buildNavigationConfig() {
        await loadUrlConfig();

        const config = {
            title: NAV_CONFIG_TEMPLATE.title,
            logo: NAV_CONFIG_TEMPLATE.logo,
            items: NAV_CONFIG_TEMPLATE.items.map(item => ({
                ...item,
                href: item.project ? buildUrl(item.project, item.filename) : item.filename
            }))
        };

        return config;
    }

    /**
     * Determines active page based on current URL
     */
    function getCurrentPageId() {
        const pathname = window.location.pathname;
        const filename = pathname.split('/').pop() || 'index.html';

        switch(filename) {
            case 'index.html':
            case '':
                return 'generator';
            case 'SOO-calculator.html':
                return 'ahu-calculator';
            case 'SOO-zone-calculator.html':
                return 'zone-calculator';
            case 'timeline_viewer.html':
                return 'stanford';
            default:
                return 'generator'; // fallback
        }
    }

    /**
     * Generates navigation HTML
     */
    async function generateNavigationHTML(activePageId) {
        const NAV_CONFIG = await buildNavigationConfig();

        // Group items by section
        const sooItems = NAV_CONFIG.items.filter(item => item.section === 'soo');
        const validationItems = NAV_CONFIG.items.filter(item => item.section === 'validation');
        const standaloneItems = NAV_CONFIG.items.filter(item => item.section === 'standalone');

        function generateNavItem(item, isActive) {
            const cautionIcon = item.working ? '' : ' <span class="caution-icon">⚠️</span>';
            const itemClass = `nav-item ${isActive ? 'active' : ''} ${!item.working ? 'disabled' : ''}`;
            const onclick = item.working ? `onclick="CompassNavigation.navigateTo('${item.id}')"` : '';

            return `
                <button class="${itemClass}" ${onclick} id="nav-${item.id}">
                    <span class="nav-item-content">
                        ${item.label}${cautionIcon}
                    </span>
                </button>
            `;
        }

        const sooSection = sooItems.map(item =>
            generateNavItem(item, item.id === activePageId)
        ).join('');

        const validationSection = validationItems.map(item =>
            generateNavItem(item, item.id === activePageId)
        ).join('');

        const standaloneItems1 = standaloneItems.filter(item => item.id === 'bacnet-points');
        const standaloneItems2 = standaloneItems.filter(item => item.id === 'energy-savings');
        const standaloneItems3 = standaloneItems.filter(item => item.id === 'cost-savings');

        const bacnetSection = standaloneItems1.map(item =>
            generateNavItem(item, item.id === activePageId)
        ).join('');

        const energySection = standaloneItems2.map(item =>
            generateNavItem(item, item.id === activePageId)
        ).join('');

        const costSection = standaloneItems3.map(item =>
            generateNavItem(item, item.id === activePageId)
        ).join('');

        return `
            <div class="left-nav">
                <div class="nav-header">
                    <div class="nav-logo">
                        <img src="${NAV_CONFIG.logo}" alt="R-Zero Logo" class="logo-image">
                    </div>
                    <div class="nav-title">
                        <h1>${NAV_CONFIG.title}</h1>
                    </div>
                </div>

                <nav class="nav-menu">
                    <div class="nav-section">
                        <div class="nav-section-header">Sequence of Operations</div>
                        ${sooSection}
                    </div>

                    ${bacnetSection}

                    <div class="nav-section">
                        <div class="nav-section-header">Validate Performance</div>
                        ${validationSection}
                    </div>

                    ${energySection}

                    ${costSection}
                </nav>
            </div>
        `;
    }

    /**
     * Navigation handler
     */
    async function navigateTo(pageId) {
        // Get navigation target from config
        const NAV_CONFIG = await buildNavigationConfig();
        const navItem = NAV_CONFIG.items.find(item => item.id === pageId);

        // Only navigate if item is working and has a valid href
        if (navItem && navItem.working && navItem.href !== '#') {
            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });

            // Add active class to clicked item
            const activeItem = document.getElementById(`nav-${pageId}`);
            if (activeItem) {
                activeItem.classList.add('active');
            }

            // Navigate if it's a different page
            if (navItem.href !== window.location.pathname.split('/').pop()) {
                window.location.href = navItem.href;
            }
        }
    }

    /**
     * Updates main header content (for pages that support it)
     */
    function updateMainHeader(title, description) {
        const titleEl = document.querySelector('.header-text h1');
        const descEl = document.querySelector('.header-text p');
        if (titleEl) titleEl.textContent = title;
        if (descEl) descEl.textContent = description;
    }

    /**
     * Initialize navigation component
     */
    async function init(containerId = 'compass-navigation', explicitActivePageId = null) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`CompassNavigation: Container element '${containerId}' not found`);
            return false;
        }

        const activePageId = explicitActivePageId || getCurrentPageId();
        container.innerHTML = await generateNavigationHTML(activePageId);

        const NAV_CONFIG = await buildNavigationConfig();
        console.log(`CompassNavigation v3.0: Initialized with active page '${activePageId}'`);
        console.log('Navigation config:', NAV_CONFIG);
        console.log('Environment detected:', detectEnvironment());
        return true;
    }

    // Global API
    window.CompassNavigation = {
        init: init,
        navigateTo: navigateTo,
        updateMainHeader: updateMainHeader,
        getCurrentPageId: getCurrentPageId
    };

    // Auto-initialize if container exists when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', async function() {
            const container = document.getElementById('compass-navigation');
            if (container) {
                await init();
            }
        });
    } else {
        // DOM already loaded
        const container = document.getElementById('compass-navigation');
        if (container) {
            init(); // async but fire-and-forget for immediate loading
        }
    }

})();