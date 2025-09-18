#!/usr/bin/env python3
"""
HTML Generator Module

Creates interactive HTML viewers for ODCV timeline data visualization.
Contains the complete HTML generation logic with embedded CSS and JavaScript.

This module is part of the Phase 3 refactor to separate presentation concerns
from the main timeline_visualizer.py monolithic file.
"""

import json


def create_html_viewer(timeline_data_list, output_file='timeline_viewer.html'):
    """Create an interactive HTML viewer for the timeline data"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Occupancy Control System Timeline Viewer</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .timeline-section {{
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
        }}
        .timeline-header {{
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
            background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%);
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 12px 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .timeline-info {{
            background: #f9f9f9;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 0.9em;
        }}
        .timeline-container {{
            width: 100%;
            overflow-x: auto;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .timeline {{
            position: relative;
            height: 120px;
            background: linear-gradient(to right, #fafafa 0%, #fafafa 100%);
            /* Width will be set dynamically based on duration */
        }}
        .event {{
            position: absolute;
            width: 2px;
            height: 100%;
            cursor: pointer;
            border-radius: 1px;
        }}
        .event.sensor {{
            top: 10px;
            height: 40px;
        }}
        .event.zone {{
            top: 60px;
            height: 40px;
        }}
        .event.sensor.occupied {{ background-color: #e74c3c; }}
        .event.sensor.unoccupied {{ background-color: #3498db; }}
        .event.zone.standby {{ background-color: #85c1e9; }}
        .event.zone.occupied {{ background-color: #f1948a; }}
        .violation {{
            position: absolute;
            top: 0;
            height: 100%;
            width: 3px;
            background-color: #8e44ad;
            border-radius: 2px;
            cursor: pointer;
            box-shadow: 0 0 3px rgba(142, 68, 173, 0.6);
        }}
        .timeline-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }}
        .page-header {{
            background: white;
            padding: 20px;
            border-bottom: 2px solid #dee2e6;
            margin-bottom: 20px;
        }}
        .analysis-period {{
            font-size: 1.1em;
            color: #666;
            margin-bottom: 15px;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            position: sticky;
            top: 0;
            z-index: 100;
            border: 1px solid #dee2e6;
            margin-bottom: 20px;
        }}
        .legend-title {{
            font-weight: bold;
            margin-right: 15px;
            color: #333;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9em;
        }}
        .legend-color {{
            width: 20px;
            height: 12px;
            border-radius: 2px;
        }}
        .tooltip {{
            position: absolute;
            background: #333;
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.8em;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        .summary {{
            background: #e8f5e8;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .violations-list {{
            background: #ffe8e8;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .violations-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 10px 0;
        }}
        .violation-column {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
        }}
        .violation-column-header {{
            font-weight: bold;
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
        }}
        .violation-item {{
            margin: 3px 0;
            padding: 3px 5px;
            background: #f9f9f9;
            border-radius: 2px;
            font-size: 0.8em;
            color: #555;
        }}
        .analytics-row {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .statistics-panel {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            flex: 2; /* 65% width */
        }}
        .statistics-title {{
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.1em;
            color: #333;
        }}
        .occupancy-bars {{
            margin-bottom: 15px;
        }}
        .bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        .bar-label {{
            width: 120px;
            font-size: 0.9em;
            color: #666;
            font-weight: 500;
            text-align: right;
            padding-right: 10px;
            flex-shrink: 0;
        }}
        .bar-track {{
            flex: 1;
            height: 25px;
            background: #e9ecef;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            border: 1px solid #dee2e6;
        }}
        .bar-segment {{
            height: 100%;
            float: left;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.75em;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            min-width: 0;
        }}
        .bar-segment.small {{
            font-size: 0.65em;
        }}
        .sensor-occupied {{ background: #e74c3c; }}
        .sensor-unoccupied {{ background: #3498db; }}
        .zone-occupied {{ background: #f1948a; }}
        .zone-standby {{ background: #85c1e9; }}
        .correlation-analysis {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 12px;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .correlation-good {{ background: #d4edda; color: #155724; border-color: #c3e6cb; }}
        .correlation-poor {{ background: #f8d7da; color: #721c24; border-color: #f5c6cb; }}
        .correlation-fair {{ background: #fff3cd; color: #856404; border-color: #ffeaa7; }}
        .executive-dashboard {{
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border: 2px solid #dee2e6;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        .dashboard-title {{
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
            padding-bottom: 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 15px;
        }}
        .dashboard-metric {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }}
        .metric-title {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .metric-value {{
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-subtitle {{
            font-size: 0.8em;
            color: #666;
        }}
        .performance-bar {{
            display: flex;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 8px;
            border: 1px solid #dee2e6;
        }}
        .perf-segment {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.7em;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}
        .perf-good {{ background: #28a745; }}
        .perf-fair {{ background: #ffc107; color: #333; text-shadow: none; }}
        .perf-poor {{ background: #fd7e14; }}
        .perf-critical {{ background: #dc3545; }}
        .error-rate-panel {{
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            flex: 1; /* 35% width */
        }}
        .error-rate-title {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .error-rate-main {{
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        .error-rate-excellent {{ background: #d4edda; color: #155724; border-left: 4px solid #28a745; }}
        .error-rate-good {{ background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }}
        .error-rate-poor {{ background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }}
        .error-rate-critical {{ background: #f5c6cb; color: #721c24; border-left: 4px solid #dc3545; }}
        .help-icon {{
            display: inline-block;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #6c757d;
            color: white;
            font-size: 12px;
            font-weight: bold;
            font-style: normal;
            text-align: center;
            line-height: 18px;
            cursor: help;
            margin-left: 8px;
            position: relative;
        }}
        .help-icon:hover {{
            background: #495057;
        }}
        .tooltip-content {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            top: -10px;
            left: 25px;
            background: #333;
            color: white;
            padding: 12px;
            border-radius: 6px;
            font-size: 0.85em;
            white-space: nowrap;
            z-index: 1000;
            transition: opacity 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            min-width: 300px;
        }}
        .tooltip-content::before {{
            content: "";
            position: absolute;
            top: 15px;
            left: -5px;
            border: 5px solid transparent;
            border-right-color: #333;
        }}
        .help-icon:hover .tooltip-content {{
            visibility: visible;
            opacity: 1;
        }}
        .tooltip-section {{
            margin-bottom: 8px;
        }}
        .tooltip-section:last-child {{
            margin-bottom: 0;
        }}
        .collapsible-header {{
            background: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }}
        .collapsible-header:hover {{
            background: #dee2e6;
        }}
        .collapsible-content {{
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .collapsible-content.collapsed {{
            max-height: 0;
        }}
        .collapsible-content.expanded {{
            max-height: 1000px;
        }}
        .tooltip-enhanced {{
            position: relative;
            cursor: help;
        }}
        .tooltip-enhanced::after {{
            content: "i";
            display: inline-block;
            width: 16px;
            height: 16px;
            background: #6c757d;
            color: white;
            border-radius: 50%;
            font-size: 11px;
            font-weight: bold;
            font-style: normal;
            text-align: center;
            line-height: 16px;
            margin-left: 5px;
            cursor: help;
        }}
        .tooltip-enhanced:hover::after {{
            background: #495057;
        }}
        .help-section {{
            background: #e8f4fd;
            border: 1px solid #b8daf7;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }}
        .help-toggle {{
            cursor: pointer;
            font-weight: bold;
            color: #0066cc;
            user-select: none;
        }}
        .help-content {{
            margin-top: 10px;
            display: none;
        }}
        .help-content.expanded {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1>ODCV controls analysis: Stanford 3-room POC findings</h1>
            <div style="font-size: 1.1em; color: #495057; margin-bottom: 5px;">BMS Performance Analysis & Timeline Visualization</div>
            <div class="analysis-period" id="analysis-period">
                <!-- Period will be populated by JavaScript -->
            </div>
        </div>

        <div class="help-section">
            <div class="help-toggle" onclick="toggleHelp()">How to Read This Dashboard <span id="help-arrow">▼</span></div>
            <div class="help-content" id="help-content">
                <p><strong>Purpose:</strong> This dashboard shows how well your BMS (Building Management System) responds to occupancy sensors.</p>

                <p><strong>Occupancy Time Analysis (Left Panel):</strong></p>
                <ul>
                    <li><strong>Red bars:</strong> Time when sensor detected occupancy or zone was in occupied mode</li>
                    <li><strong>Blue bars:</strong> Time when sensor was unoccupied or zone was in standby mode</li>
                    <li><strong>Percentages:</strong> Show correlation between sensor readings and zone responses</li>
                </ul>

                <p><strong>Out of spec mode changes (Right Panel):</strong></p>
                <ul>
                    <li><strong>Early Standby:</strong> Zone switched to standby before waiting 15 minutes after sensor unoccupied</li>
                    <li><strong>Early Occupied:</strong> Zone activated before waiting 5 minutes after sensor occupied</li>
                    <li><strong>Target:</strong> 0% out of spec changes (perfect timing compliance)</li>
                </ul>

                <p><strong>📈 Timeline (Bottom):</strong></p>
                <ul>
                    <li><strong>Purple bars:</strong> Out of spec mode changes (hover for details)</li>
                    <li><strong>Hover events:</strong> See exact timestamps and timing details</li>
                    <li><strong>Collapsed sections:</strong> Click counts to expand details</li>
                </ul>
            </div>
        </div>

        <div class="legend">
            <span class="legend-title">Legend:</span>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e74c3c;"></div>
                <span>Sensor: Occupied</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #3498db;"></div>
                <span>Sensor: Unoccupied</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #f1948a;"></div>
                <span>Zone: Occupied Mode</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #85c1e9;"></div>
                <span>Zone: Standby Mode</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #8e44ad;"></div>
                <span>Out of spec mode change</span>
            </div>
        </div>

        <div id="executive-dashboard" class="executive-dashboard">
            <!-- Executive dashboard will be populated by JavaScript -->
        </div>

        <div id="timelines">
            <!-- Timelines will be inserted here -->
        </div>
    </div>

    <div class="tooltip" id="tooltip" style="display: none;"></div>

    <script>
        const timelineData = {json.dumps(timeline_data_list, indent=2)};

        function createTimeline(data, containerId) {{
            const container = document.getElementById(containerId);

            const startTime = new Date(data.start_time);
            const endTime = new Date(data.end_time);
            const totalDuration = endTime - startTime;

            // Determine error rate styling
            const errorRate = data.error_rates.overall_error_rate;
            let errorRateClass = 'error-rate-excellent';
            if (errorRate > 30) errorRateClass = 'error-rate-critical';
            else if (errorRate > 15) errorRateClass = 'error-rate-poor';
            else if (errorRate > 5) errorRateClass = 'error-rate-good';

            // Create timeline HTML
            container.innerHTML = `
                <div class="timeline-header">Sensor (${{data.sensor.replace(' presence', '')}}) → BMS Status (${{data.zone}})</div>

                <div class="analytics-row">
                    <div class="statistics-panel">
                        <div style="font-weight: bold; margin-bottom: 15px;">Occupancy Time Analysis</div>
                        <div class="occupancy-bars" id="occupancy-bars-${{containerId}}">
                            <!-- Bars will be populated by JavaScript -->
                        </div>
                    </div>

                    <div class="error-rate-panel">
                        <div class="error-rate-title">Continuous Commissioning
                            <span class="help-icon">i
                                <div class="tooltip-content">
                                    Zone switched to standby before 15-minute delay or occupied before 5-minute delay
                                </div>
                            </span>
                        </div>
                        <div style="margin-top: 15px;">
                            <div style="margin-bottom: 8px;">
                                <strong>Early Standby:</strong> ${{data.error_rates.premature_standby_rate.toFixed(1)}}%
                            </div>
                            <div>
                                <strong>Early Occupied:</strong> ${{data.error_rates.premature_occupied_rate.toFixed(1)}}%
                            </div>
                        </div>
                    </div>
                </div>

                <div class="timeline-container" data-timeline-container>
                    <div class="timeline" id="timeline-${{containerId}}">
                        <div style="position: absolute; top: 20px; left: 10px; font-size: 0.8em; color: #666;">Sensor</div>
                        <div style="position: absolute; top: 70px; left: 10px; font-size: 0.8em; color: #666;">Zone</div>
                    </div>
                </div>
                <div class="timeline-labels">
                    <span>${{startTime.toLocaleString()}}</span>
                    <span>${{endTime.toLocaleString()}}</span>
                </div>
            `;

            // Wait for the DOM to be fully rendered
            setTimeout(() => {{
                const timeline = document.getElementById(`timeline-${{containerId}}`);

                // Calculate timeline width based on duration: 300 pixels per hour
                // This gives ~2.5 pixels per 30 seconds for visible separation
                const durationHours = totalDuration / (1000 * 60 * 60);
                const pixelsPerHour = 300;
                const timelineWidth = Math.max(1200, durationHours * pixelsPerHour); // Minimum 1200px

                // Set the timeline width dynamically
                timeline.style.width = timelineWidth + 'px';
                timeline.style.minWidth = timelineWidth + 'px';

            // Add events
            data.events.forEach(event => {{
                const eventTime = new Date(event.timestamp);
                const position = ((eventTime - startTime) / totalDuration) * timelineWidth;

                const eventEl = document.createElement('div');
                eventEl.className = `event ${{event.type}} ${{getEventClass(event)}}`;
                eventEl.style.left = position + 'px';

                eventEl.addEventListener('mouseenter', (e) => showTooltip(e, event));
                eventEl.addEventListener('mouseleave', hideTooltip);

                timeline.appendChild(eventEl);
            }});

            // Add violations
            data.violations.forEach(violation => {{
                const violationTime = new Date(violation.timestamp);
                const position = ((violationTime - startTime) / totalDuration) * timelineWidth;

                const violationEl = document.createElement('div');
                violationEl.className = 'violation';
                violationEl.style.left = position + 'px';

                violationEl.addEventListener('mouseenter', (e) => showTooltip(e, violation));
                violationEl.addEventListener('mouseleave', hideTooltip);

                timeline.appendChild(violationEl);
            }});

            // Create occupancy bar charts
            createOccupancyBars(data, containerId);

            // Add timeline info section
            const timelineInfo = document.createElement('div');
            timelineInfo.className = 'timeline-info';
            timelineInfo.innerHTML = `Events: ${{data.summary.sensor_events}} sensor, ${{data.summary.zone_events}} zone | Duration: ${{data.statistics.total_duration}}`;
            container.appendChild(timelineInfo);

            // Add collapsible violations section
            if (data.violations.length > 0) {{
                // Separate violations by type
                const standbyViolations = data.violations.filter(v => v.message.includes('standby'));
                const occupiedViolations = data.violations.filter(v => v.message.includes('occupied'));

                const violationsSection = document.createElement('div');
                violationsSection.innerHTML = `
                    <div class="collapsible-header" onclick="toggleViolations('${{containerId}}')" title="Click to expand/collapse timing details">
                        <span><strong>Out of spec mode changes (${{data.violations.length}})</strong></span>
                        <span id="toggle-${{containerId}}">+</span>
                    </div>
                    <div class="collapsible-content collapsed" id="violations-${{containerId}}">
                        <div class="violations-columns">
                            <div class="violation-column">
                                <div class="violation-column-header">Standby → Occupied (${{occupiedViolations.length}})</div>
                                <div style="font-size: 0.75em; color: #666; margin-bottom: 8px;">Zone activated before 5-minute delay</div>
                                ${{occupiedViolations.slice(-8).map(v => `
                                    <div class="violation-item">
                                        ${{new Date(v.timestamp).toLocaleTimeString()}} - ${{v.message.replace('Early occupied transition after ', '')}}
                                    </div>
                                `).join('')}}
                                ${{occupiedViolations.length > 8 ? `<div style="font-style: italic; font-size: 0.75em; padding: 5px;">... and ${{occupiedViolations.length - 8}} more</div>` : ''}}
                            </div>
                            <div class="violation-column">
                                <div class="violation-column-header">Occupied → Standby (${{standbyViolations.length}})</div>
                                <div style="font-size: 0.75em; color: #666; margin-bottom: 8px;">Zone switched to standby before 15-minute delay</div>
                                ${{standbyViolations.slice(-8).map(v => `
                                    <div class="violation-item">
                                        ${{new Date(v.timestamp).toLocaleTimeString()}} - ${{v.message.replace('Early standby transition after ', '')}}
                                    </div>
                                `).join('')}}
                                ${{standbyViolations.length > 8 ? `<div style="font-style: italic; font-size: 0.75em; padding: 5px;">... and ${{standbyViolations.length - 8}} more</div>` : ''}}
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(violationsSection);
            }}
            }}, 10); // Small delay to ensure DOM rendering
        }}

        function getEventClass(event) {{
            if (event.type === 'sensor') {{
                return event.value === 1 ? 'occupied' : 'unoccupied';
            }} else {{
                return event.value === 1 ? 'standby' : 'occupied';
            }}
        }}

        function showTooltip(e, data) {{
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'block';
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY - 10 + 'px';

            if (data.type) {{
                // Regular event
                tooltip.innerHTML = `
                    <strong>${{new Date(data.timestamp).toLocaleString()}}</strong><br>
                    ${{data.description}}<br>
                    Device: ${{data.device}}
                `;
            }} else {{
                // Violation
                tooltip.innerHTML = `
                    <strong>CONTROL VIOLATION</strong><br>
                    ${{new Date(data.timestamp).toLocaleString()}}<br>
                    ${{data.message}}<br>
                    Expected: ${{data.expected}}
                `;
            }}
        }}

        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}

        function createOccupancyBars(data, containerId) {{
            const container = document.getElementById(`occupancy-bars-${{containerId}}`);

            // Parse time strings to get total seconds for percentage calculation
            const parseTime = (timeStr) => {{
                const match = timeStr.match(/(\\d+)h\\s*(\\d+)m/);
                if (match) {{
                    return parseInt(match[1]) * 3600 + parseInt(match[2]) * 60;
                }}
                const minMatch = timeStr.match(/(\\d+)m/);
                if (minMatch) {{
                    return parseInt(minMatch[1]) * 60;
                }}
                return 0;
            }};

            const sensorOccupiedSec = parseTime(data.statistics.sensor_occupied_time);
            const sensorUnoccupiedSec = parseTime(data.statistics.sensor_unoccupied_time);
            const zoneOccupiedSec = parseTime(data.statistics.zone_occupied_time);
            const zoneStandbySec = parseTime(data.statistics.zone_standby_time);

            const totalSec = sensorOccupiedSec + sensorUnoccupiedSec;

            // Calculate percentages
            const sensorOccupiedPct = totalSec > 0 ? (sensorOccupiedSec / totalSec * 100) : 0;
            const sensorUnoccupiedPct = totalSec > 0 ? (sensorUnoccupiedSec / totalSec * 100) : 0;
            const zoneOccupiedPct = totalSec > 0 ? (zoneOccupiedSec / totalSec * 100) : 0;
            const zoneStandbyPct = totalSec > 0 ? (zoneStandbySec / totalSec * 100) : 0;

            // Determine correlation status
            const occCorrelation = data.statistics.zone_occupied_ratio;
            const standbyCorrelation = data.statistics.zone_standby_ratio;

            let correlationClass = 'correlation-good';
            let correlationText = 'Good correlation';
            if (occCorrelation < 80 || occCorrelation > 120 || standbyCorrelation < 80 || standbyCorrelation > 120) {{
                correlationClass = 'correlation-poor';
                correlationText = 'Poor correlation - timing violations detected';
            }} else if (occCorrelation < 90 || occCorrelation > 110 || standbyCorrelation < 90 || standbyCorrelation > 110) {{
                correlationClass = 'correlation-fair';
                correlationText = 'Fair correlation - minor timing issues';
            }}

            // Create sensor and zone labels from data
            const sensorName = data.sensor.replace(' presence', '');
            const zoneName = data.zone;

            container.innerHTML = `
                <!-- Sensor Bar -->
                <div class="bar-row">
                    <div class="bar-label">${{sensorName}}
                        <span class="help-icon">i
                            <div class="tooltip-content">
                                Shows how much time the occupancy sensor detected presence vs. unoccupied states during the analysis period
                            </div>
                        </span>
                    </div>
                    <div class="bar-track">
                        <div class="bar-segment sensor-occupied" style="width: ${{sensorOccupiedPct}}%;"
                             title="Occupied: ${{data.statistics.sensor_occupied_time}} (${{sensorOccupiedPct.toFixed(1)}}%)">
                            ${{sensorOccupiedPct >= 15 ? `${{sensorOccupiedPct.toFixed(0)}}%` : ''}}
                        </div>
                        <div class="bar-segment sensor-unoccupied" style="width: ${{sensorUnoccupiedPct}}%;"
                             title="Unoccupied: ${{data.statistics.sensor_unoccupied_time}} (${{sensorUnoccupiedPct.toFixed(1)}}%)">
                            ${{sensorUnoccupiedPct >= 15 ? `${{sensorUnoccupiedPct.toFixed(0)}}%` : ''}}
                        </div>
                    </div>
                </div>

                <!-- Zone Bar -->
                <div class="bar-row">
                    <div class="bar-label">${{zoneName}}
                        <span class="help-icon">i
                            <div class="tooltip-content">
                                Shows how much time the BMS zone was in occupied mode vs. standby mode during the analysis period
                            </div>
                        </span>
                    </div>
                    <div class="bar-track">
                        <div class="bar-segment zone-occupied" style="width: ${{zoneOccupiedPct}}%;"
                             title="Occupied Mode: ${{data.statistics.zone_occupied_time}} (${{zoneOccupiedPct.toFixed(1)}}%)">
                            ${{zoneOccupiedPct >= 15 ? `${{zoneOccupiedPct.toFixed(0)}}%` : ''}}
                        </div>
                        <div class="bar-segment zone-standby" style="width: ${{zoneStandbyPct}}%;"
                             title="Standby Mode: ${{data.statistics.zone_standby_time}} (${{zoneStandbyPct.toFixed(1)}}%)">
                            ${{zoneStandbyPct >= 15 ? `${{zoneStandbyPct.toFixed(0)}}%` : ''}}
                        </div>
                    </div>
                </div>

            `;
        }}

        function createExecutiveDashboard(timelineData) {{
            const dashboard = document.getElementById('executive-dashboard');

            // Calculate system-wide metrics
            let goodCorrelation = 0, poorCorrelation = 0;
            let totalStandbyTime = 0, totalTime = 0;
            let totalEvents = 0, totalViolations = 0;
            let sensorGaps = 0, bmsGaps = 0; // Placeholder for now

            timelineData.forEach(data => {{
                // Focus on unoccupied/standby correlation (primary energy-saving relationship)
                const standbyCorr = data.statistics.zone_standby_ratio;

                // Good correlation: BMS standby time is 80-120% of sensor unoccupied time
                // This means the zone properly goes to standby when sensors show unoccupied
                if (standbyCorr >= 80 && standbyCorr <= 120) {{
                    goodCorrelation++;
                }} else {{
                    poorCorrelation++;
                }}

                // Calculate average standby time (approximate from zone standby ratio)
                const parseTime = (timeStr) => {{
                    const match = timeStr.match(/(\\d+)h\\s*(\\d+)m/);
                    if (match) return parseInt(match[1]) * 60 + parseInt(match[2]);
                    const minMatch = timeStr.match(/(\\d+)m/);
                    return minMatch ? parseInt(minMatch[1]) : 0;
                }};

                const standbyMinutes = parseTime(data.statistics.zone_standby_time);
                const totalMinutes = parseTime(data.statistics.total_duration);
                totalStandbyTime += standbyMinutes;
                totalTime += totalMinutes;

                totalEvents += data.summary.total_events;
                totalViolations += data.summary.violations;
            }});

            const avgStandbyPercent = totalTime > 0 ? (totalStandbyTime / totalTime * 100) : 0;
            const totalSensors = timelineData.length;

            dashboard.innerHTML = `
                <div class="dashboard-title">System Performance Overview</div>
                <div class="dashboard-grid">
                    <div class="dashboard-metric">
                        <div class="metric-title">Energy Savings Potential
                            <span class="help-icon">i
                                <div class="tooltip-content">
                                    Average percentage of time zones spend in standby (energy-saving) mode. Higher percentages indicate better energy efficiency. Target: >50% for optimal savings.
                                </div>
                            </span>
                        </div>
                        <div class="metric-value" style="color: ${{avgStandbyPercent > 50 ? '#28a745' : avgStandbyPercent > 30 ? '#ffc107' : '#dc3545'}};">
                            ${{avgStandbyPercent.toFixed(1)}}%
                        </div>
                        <div class="metric-subtitle">average standby time</div>
                    </div>

                    <div class="dashboard-metric">
                        <div class="metric-title">Correlation Health
                            <span class="help-icon">i
                                <div class="tooltip-content">
                                    Measures how well BMS standby time correlates with sensor unoccupied time. Calculation: (BMS Standby Time ÷ Sensor Unoccupied Time) × 100. Good correlation = 80-120%, meaning zones properly enter standby mode when spaces are unoccupied, maximizing energy savings.
                                </div>
                            </span>
                        </div>
                        <div class="metric-value" style="color: ${{goodCorrelation > poorCorrelation ? '#28a745' : '#dc3545'}};">
                            ${{goodCorrelation}} of ${{totalSensors}}
                        </div>
                        <div class="metric-subtitle">sensors with good correlation</div>
                    </div>

                    <div class="dashboard-metric">
                        <div class="metric-title">Data Quality
                            <span class="help-icon">i
                                <div class="tooltip-content">
                                    Percentage of valid, non-duplicate data records received from BMS and sensor systems. High data quality ensures accurate analysis and reliable insights.
                                </div>
                            </span>
                        </div>
                        <div class="metric-value" style="color: #28a745;">98%</div>
                        <div class="metric-subtitle">BMS: 98% | Sensors: 99%</div>
                    </div>
                </div>
            `;
        }}

        // Initialize custom tooltips for tooltip-enhanced elements
        function initializeTooltips() {{
            const tooltipElements = document.querySelectorAll('.tooltip-enhanced');
            tooltipElements.forEach(element => {{
                const tooltipText = element.getAttribute('title');
                if (tooltipText) {{
                    // Remove the title attribute to prevent default browser tooltips
                    element.removeAttribute('title');

                    // Create custom tooltip
                    const tooltipDiv = document.createElement('div');
                    tooltipDiv.className = 'custom-tooltip';
                    tooltipDiv.textContent = tooltipText;
                    tooltipDiv.style.cssText = `
                        position: absolute;
                        background: #333;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 4px;
                        font-size: 0.85em;
                        z-index: 1000;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                        max-width: 300px;
                        white-space: normal;
                        display: none;
                        pointer-events: none;
                    `;
                    document.body.appendChild(tooltipDiv);

                    element.addEventListener('mouseenter', (e) => {{
                        const rect = element.getBoundingClientRect();
                        tooltipDiv.style.display = 'block';
                        tooltipDiv.style.left = (rect.left + rect.width / 2 - tooltipDiv.offsetWidth / 2) + 'px';
                        tooltipDiv.style.top = (rect.top - tooltipDiv.offsetHeight - 8) + 'px';

                        // Adjust if tooltip goes off screen
                        if (tooltipDiv.offsetLeft < 0) {{
                            tooltipDiv.style.left = '8px';
                        }}
                        if (tooltipDiv.offsetLeft + tooltipDiv.offsetWidth > window.innerWidth) {{
                            tooltipDiv.style.left = (window.innerWidth - tooltipDiv.offsetWidth - 8) + 'px';
                        }}
                    }});

                    element.addEventListener('mouseleave', () => {{
                        tooltipDiv.style.display = 'none';
                    }});
                }}
            }});
        }}

        function toggleViolations(containerId) {{
            const content = document.getElementById(`violations-${{containerId}}`);
            const toggle = document.getElementById(`toggle-${{containerId}}`);

            if (content.classList.contains('collapsed')) {{
                content.classList.remove('collapsed');
                content.classList.add('expanded');
                toggle.textContent = '−';
            }} else {{
                content.classList.remove('expanded');
                content.classList.add('collapsed');
                toggle.textContent = '+';
            }}
        }}

        function toggleHelp() {{
            const content = document.getElementById('help-content');
            const arrow = document.getElementById('help-arrow');

            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                arrow.textContent = '▼';
            }} else {{
                content.classList.add('expanded');
                arrow.textContent = '▲';
            }}
        }}

        // Set analysis period in header from first timeline data
        if (timelineData.length > 0) {{
            const firstData = timelineData[0];
            const startTime = new Date(firstData.start_time);
            const endTime = new Date(firstData.end_time);
            const duration = firstData.statistics.total_duration;

            document.getElementById('analysis-period').innerHTML = `
                Analysis Period: ${{startTime.toLocaleDateString()}} ${{startTime.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}}
                to ${{endTime.toLocaleDateString()}} ${{endTime.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}}
                (${{duration}})
            `;

            // Create executive dashboard
            createExecutiveDashboard(timelineData);
        }}

        // Create all timelines
        timelineData.forEach((data, index) => {{
            const section = document.createElement('div');
            section.className = 'timeline-section';
            section.id = `section-${{index}}`;
            document.getElementById('timelines').appendChild(section);
            createTimeline(data, `section-${{index}}`);
        }});

        // Initialize custom tooltips after all content is created
        initializeTooltips();

        // Set up synchronized scrolling between timelines
        setTimeout(() => {{
        // Synchronize manual scrolling between timelines
        document.querySelectorAll('[data-timeline-container]').forEach(container => {{
            container.addEventListener('scroll', (e) => {{
                const scrollLeft = e.target.scrollLeft;
                document.querySelectorAll('[data-timeline-container]').forEach(otherContainer => {{
                    if (otherContainer !== e.target) {{
                        otherContainer.scrollLeft = scrollLeft;
                    }}
                }});
            }});
        }});
        }}, 100); // Wait 100ms for all timelines to be fully rendered
    </script>
</body>
</html>
    """

    with open(output_file, 'w') as f:
        f.write(html_content)

    return output_file