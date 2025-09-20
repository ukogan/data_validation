#!/usr/bin/env python3
"""
Playwright automated testing script for ODCV Analytics Dashboard
Tests performance, time period switching, and visual validation across different datasets
"""

from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime

def test_dashboard_performance():
    """Run comprehensive dashboard performance tests"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'dataset': 'SCH-1_data_30_days_sensors_01-04.csv',
        'test_results': {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        page = browser.new_page()

        # Set viewport for consistent screenshots
        page.set_viewport_size({"width": 1920, "height": 1080})

        print("📊 Starting Dataset A (30 days, 4 sensors) Testing...")

        # Test 1: Initial Load Performance
        print("🔄 Test 1.1: Initial Load Performance")
        start_time = time.time()
        page.goto("http://localhost:8000")

        # Wait for dashboard to fully load
        page.wait_for_selector(".executive-dashboard", timeout=30000)
        page.wait_for_selector(".grouped-container", timeout=30000)

        load_time = time.time() - start_time
        results['test_results']['initial_load_time'] = round(load_time, 2)
        print(f"   ✅ Dashboard loaded in {load_time:.2f} seconds")

        # Capture initial state
        page.screenshot(path="screenshots/dataset_a_initial_load.png", full_page=True)

        # Test 2: Time Period Switching Performance
        print("🔄 Test 1.2: Time Period Switching Performance")
        time_periods = [
            ('24h', 'Latest 24 Hrs'),
            ('5d', '5 Days'),
            ('30d', '30 Days')
        ]
        period_timings = {}

        for period_key, button_text in time_periods:
            print(f"   Testing {period_key} period...")
            start_time = time.time()

            # Click the time period button
            page.click(f'button:has-text("{button_text}")')

            # Wait for API calls to complete and UI to update
            page.wait_for_timeout(1000)  # Brief wait for API calls

            # Wait for any loading states to clear
            page.wait_for_function(
                "() => !document.querySelector('.loading') && document.querySelector('.executive-dashboard')",
                timeout=10000
            )

            period_time = time.time() - start_time
            period_timings[period_key] = round(period_time, 2)
            print(f"   ✅ {period_key} period loaded in {period_time:.2f} seconds")

            # Capture screenshot for each time period
            page.screenshot(path=f"screenshots/dataset_a_period_{period_key}.png", full_page=True)

            # Brief pause between switches
            time.sleep(0.5)

        results['test_results']['period_switching_times'] = period_timings

        # Test 3: Metric Accuracy Validation
        print("🔄 Test 1.3: Metric Accuracy Validation")

        # Extract executive metrics for each time period
        executive_metrics = {}
        for period_key, button_text in time_periods:
            page.click(f'button:has-text("{button_text}")')
            page.wait_for_timeout(1000)

            # Extract executive metrics
            exec_metrics = {}
            exec_elements = page.query_selector_all('.exec-metric')
            for i, elem in enumerate(exec_elements):
                label = elem.query_selector('.exec-label')
                value = elem.query_selector('.exec-value')
                if label and value:
                    exec_metrics[f'exec_{i+1}'] = {
                        'label': label.inner_text(),
                        'value': value.inner_text()
                    }

            executive_metrics[period_key] = exec_metrics
            print(f"   ✅ Captured metrics for {period_key} period")

        results['test_results']['executive_metrics'] = executive_metrics

        # Test 4: Individual Sensor Metrics
        print("🔄 Test 1.4: Individual Sensor Metrics")

        # Click back to 24h for baseline
        page.click('button:has-text("Latest 24 Hrs")')
        page.wait_for_timeout(1000)

        # Expand first sensor group to test individual metrics
        group_headers = page.query_selector_all('.group-header')
        if group_headers:
            group_headers[0].click()
            page.wait_for_timeout(500)

            # Capture expanded view
            page.screenshot(path="screenshots/dataset_a_expanded_sensors.png", full_page=True)

            # Extract individual sensor metrics
            sensor_rows = page.query_selector_all('.sensor-row')
            sensor_count = len(sensor_rows)
            results['test_results']['sensor_count'] = sensor_count
            print(f"   ✅ Found {sensor_count} individual sensors")

        # Test 5: 24h Trend Chart Consistency
        print("🔄 Test 1.5: 24h Trend Chart Consistency")

        # Capture 24h trend charts for each time period to verify they remain static
        trend_screenshots = {}
        for period_key, button_text in time_periods:
            page.click(f'button:has-text("{button_text}")')
            page.wait_for_timeout(1000)

            # Find and capture trend charts
            trend_elements = page.query_selector_all('.mini-chart')
            if trend_elements:
                # Capture just the first sensor's trend chart area
                first_sensor_row = page.query_selector('.sensor-row')
                if first_sensor_row:
                    trend_chart = first_sensor_row.query_selector('.mini-chart')
                    if trend_chart:
                        trend_chart.screenshot(path=f"screenshots/trend_chart_{period_key}.png")
                        trend_screenshots[period_key] = f"trend_chart_{period_key}.png"
                        print(f"   ✅ Captured trend chart for {period_key}")

        results['test_results']['trend_chart_screenshots'] = trend_screenshots

        # Test 6: Performance Metrics
        print("🔄 Test 1.6: Performance Metrics")

        # Test API response times
        api_timings = {}
        api_endpoints = [
            '/api/sensors',
            '/api/dashboard/metrics?period=24h',
            '/api/sensors/metrics?period=24h'
        ]

        for endpoint in api_endpoints:
            start_time = time.time()
            response = page.request.get(f"http://localhost:8000{endpoint}")
            api_time = time.time() - start_time
            api_timings[endpoint] = {
                'response_time': round(api_time, 3),
                'status': response.status
            }
            print(f"   ✅ {endpoint}: {api_time:.3f}s (Status: {response.status})")

        results['test_results']['api_response_times'] = api_timings

        browser.close()

    # Save results to file
    with open('test_results_dataset_a.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Dataset A Testing Complete!")
    print(f"🎯 Results Summary:")
    print(f"   • Initial Load: {results['test_results']['initial_load_time']}s")
    print(f"   • Period Switching: {period_timings}")
    print(f"   • Sensor Count: {results['test_results']['sensor_count']}")
    print(f"   • Screenshots saved to screenshots/ directory")
    print(f"   • Full results saved to test_results_dataset_a.json")

    return results

if __name__ == "__main__":
    # Create screenshots directory
    import os
    os.makedirs('screenshots', exist_ok=True)

    # Run the test
    test_dashboard_performance()