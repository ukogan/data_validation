#!/usr/bin/env python3
"""
Updated Playwright test script for ODCV Analytics Dashboard
Tests the new dataset selection interface and metric validation
"""

from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import requests

def test_new_dashboard():
    """Test the updated dashboard with dataset selection interface"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_results': {}
    }

    # First verify server is running
    try:
        response = requests.get("http://localhost:8000/api/health")
        print(f"✅ Server health check: {response.status_code}")
        results['test_results']['server_health'] = response.status_code
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        page = browser.new_page()

        # Set viewport for consistent screenshots
        page.set_viewport_size({"width": 1920, "height": 1080})

        print("📊 Starting New Dashboard Testing...")

        # Test 1: Initial Load - Dataset Selection Interface
        print("🔄 Test 1: Initial Load - Dataset Selection Interface")
        start_time = time.time()
        page.goto("http://localhost:8000")

        # Wait for dataset selection interface to load
        page.wait_for_selector(".upload-section", timeout=30000)
        page.wait_for_selector("#currentDatasetInfo", timeout=30000)

        load_time = time.time() - start_time
        results['test_results']['initial_load_time'] = round(load_time, 2)
        print(f"   ✅ Dataset selection interface loaded in {load_time:.2f} seconds")

        # Capture initial state (no data loaded)
        page.screenshot(path="screenshots/new_dashboard_no_data.png", full_page=True)

        # Test 2: Dataset Loading
        print("🔄 Test 2: Dataset Loading")

        datasets_to_test = [
            ('30_days_test_subset', '30 Days / 4 Sensors + 4 BV'),
            ('1_day_mock', '1 Day / 100 Sensors')
        ]

        dataset_load_times = {}

        for dataset_key, dataset_button_text in datasets_to_test:
            print(f"   Testing dataset: {dataset_key}")
            start_time = time.time()

            # Click the dataset button
            page.click(f'button:has-text("{dataset_button_text}")')

            # Wait for loading to complete - look for success message in status div
            page.wait_for_selector('#uploadStatus .success', timeout=30000)

            load_time = time.time() - start_time
            dataset_load_times[dataset_key] = round(load_time, 2)
            print(f"   ✅ {dataset_key} loaded in {load_time:.2f} seconds")

            # Verify current dataset info was updated
            current_dataset = page.query_selector('#currentDatasetName')
            if current_dataset:
                dataset_name = current_dataset.inner_text()
                print(f"   ✅ Current dataset display: {dataset_name}")
                results['test_results'][f'{dataset_key}_display_name'] = dataset_name

            # Wait for data to fully load before next test
            page.wait_for_timeout(2000)

            # Capture screenshot after dataset load
            page.screenshot(path=f"screenshots/new_dashboard_{dataset_key}_loaded.png", full_page=True)

        results['test_results']['dataset_load_times'] = dataset_load_times

        # Test 3: API Endpoint Validation with Loaded Data
        print("🔄 Test 3: API Endpoint Validation")

        # Test with the last loaded dataset
        api_endpoints = [
            '/api/health',
            '/api/dashboard/metrics?period=24h',
            '/api/dashboard/metrics?period=5d',
            '/api/dashboard/metrics?period=30d',
            '/api/sensors',
            '/api/sensors/metrics?period=24h'
        ]

        api_results = {}
        for endpoint in api_endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"http://localhost:8000{endpoint}")
                api_time = time.time() - start_time

                api_results[endpoint] = {
                    'response_time': round(api_time, 3),
                    'status': response.status_code,
                    'has_data': len(response.text) > 100  # Simple check for non-empty response
                }
                print(f"   ✅ {endpoint}: {api_time:.3f}s (Status: {response.status_code})")

                # For metrics endpoints, check if we get actual data instead of errors
                if 'metrics' in endpoint and response.status_code == 200:
                    data = response.json()
                    if 'error' in str(data).lower():
                        api_results[endpoint]['has_error'] = True
                        print(f"   ⚠️  {endpoint} returned error in response")
                    else:
                        api_results[endpoint]['has_error'] = False

            except Exception as e:
                api_results[endpoint] = {
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"   ❌ {endpoint}: Failed - {e}")

        results['test_results']['api_validation'] = api_results

        # Test 4: Time Period Switching (if UI elements exist)
        print("🔄 Test 4: Time Period Switching")

        # Check if time period buttons exist on the page
        time_period_buttons = page.query_selector_all('button')
        period_buttons_found = []

        for button in time_period_buttons:
            button_text = button.inner_text()
            if any(period in button_text.lower() for period in ['24h', '24 hr', '5d', '5 day', '30d', '30 day']):
                period_buttons_found.append(button_text)

        results['test_results']['time_period_buttons_found'] = period_buttons_found
        print(f"   ✅ Found time period buttons: {period_buttons_found}")

        if period_buttons_found:
            # Test clicking different time periods
            period_switch_times = {}
            for button_text in period_buttons_found[:3]:  # Test first 3 buttons
                try:
                    start_time = time.time()
                    page.click(f'button:has-text("{button_text}")')
                    page.wait_for_timeout(1000)  # Wait for any API calls

                    switch_time = time.time() - start_time
                    period_switch_times[button_text] = round(switch_time, 2)
                    print(f"   ✅ {button_text} switch: {switch_time:.2f}s")

                except Exception as e:
                    print(f"   ⚠️  Failed to test {button_text}: {e}")

            results['test_results']['period_switch_times'] = period_switch_times

        # Test 5: Error Handling - Test with No Data Loaded
        print("🔄 Test 5: Error Handling")

        # Navigate to a fresh page (clears any loaded data)
        page.goto("http://localhost:8000")
        page.wait_for_selector(".upload-section", timeout=10000)

        # Try to access metrics API without loading data first
        try:
            response = requests.get("http://localhost:8000/api/dashboard/metrics?period=24h")
            results['test_results']['no_data_error_handling'] = {
                'status': response.status_code,
                'response_preview': response.text[:200]
            }

            if response.status_code == 400:
                print("   ✅ Proper error handling: API returns 400 when no data loaded")
            else:
                print(f"   ⚠️  Unexpected status when no data loaded: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error testing no-data scenario: {e}")

        browser.close()

    # Save results to file
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'test_results_new_dashboard_{timestamp_str}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 New Dashboard Testing Complete!")
    print(f"🎯 Results Summary:")
    print(f"   • Initial Load: {results['test_results']['initial_load_time']}s")
    print(f"   • Dataset Loading: {results['test_results'].get('dataset_load_times', 'N/A')}")
    print(f"   • Server Health: {results['test_results']['server_health']}")
    print(f"   • Screenshots saved to screenshots/ directory")
    print(f"   • Full results saved to {results_file}")

    return results

if __name__ == "__main__":
    # Create screenshots directory
    import os
    os.makedirs('screenshots', exist_ok=True)

    # Run the test
    test_new_dashboard()