#!/usr/bin/env python3
"""
Complete testing of remaining datasets with resilient error handling
"""

from playwright.sync_api import sync_playwright
import time
import json
import requests
from datetime import datetime
import os

def test_remaining_datasets():
    """Test remaining datasets with improved error handling"""

    # Datasets to test (excluding the already completed 30_days_test_subset)
    datasets_to_test = [
        {
            'key': '1_day_mock',
            'name': '1 Day / 100 Sensors',
            'description': 'Quick test dataset'
        },
        {
            'key': '5_days_mock',
            'name': '5 Days / 100 Sensors',
            'description': 'Medium dataset with BV zones'
        },
        {
            'key': '30_days_sensors_01_04',
            'name': '30 Days / 16 Sensors',
            'description': 'Sensors only (no BV zones)'
        }
    ]

    time_periods = [
        {'key': '24h', 'button_text': 'Latest 24 Hrs', 'name': '24 Hours'},
        {'key': '5d', 'button_text': '5 Days', 'name': '5 Days'},
        {'key': '30d', 'button_text': '30 Days', 'name': '30 Days'}
    ]

    results = {
        'timestamp': datetime.now().isoformat(),
        'completed_datasets': {},
        'performance_summary': {}
    }

    print("🔬 Completing Testing of Remaining Datasets...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        for dataset_info in datasets_to_test:
            dataset_key = dataset_info['key']
            dataset_name = dataset_info['name']

            print(f"\n🎯 Testing Dataset: {dataset_name}")
            print("=" * 60)

            dataset_results = {
                'dataset_info': dataset_info,
                'load_performance': {},
                'time_period_tests': {},
                'api_performance': {},
                'performance_summary': {}
            }

            try:
                # Load dashboard with longer timeout
                print("📊 Loading Dashboard...")
                page.goto("http://localhost:8000", timeout=60000)
                page.wait_for_selector(".upload-section", timeout=30000)

                # Capture initial state
                page.screenshot(path=f"screenshots/comprehensive/{dataset_key}/00_initial_dashboard.png", full_page=True)

                # Load the dataset
                print(f"📥 Loading dataset: {dataset_name}")
                dataset_load_start = time.time()

                page.click(f'button:has-text("{dataset_name}")')
                page.wait_for_selector('#uploadStatus .success', timeout=120000)  # Longer timeout for large datasets

                dataset_load_time = time.time() - dataset_load_start
                dataset_results['load_performance']['dataset_load_time'] = round(dataset_load_time, 2)
                dataset_results['load_performance']['status'] = 'success'

                print(f"   ✅ Dataset loaded in {dataset_load_time:.2f} seconds")

                # Capture post-load state
                page.screenshot(path=f"screenshots/comprehensive/{dataset_key}/01_dataset_loaded.png", full_page=True)

                # Test API Performance
                print("🔧 Testing API Performance...")
                api_endpoints = [
                    '/api/health',
                    '/api/sensors',
                    '/api/dashboard/metrics?period=24h',
                    '/api/dashboard/metrics?period=5d',
                    '/api/dashboard/metrics?period=30d',
                    '/api/sensors/metrics?period=24h'
                ]

                api_results = {}
                for endpoint in api_endpoints:
                    try:
                        start_time = time.time()
                        response = requests.get(f"http://localhost:8000{endpoint}", timeout=30)
                        response_time = time.time() - start_time

                        api_results[endpoint] = {
                            'status_code': response.status_code,
                            'response_time': round(response_time, 3),
                            'success': response.status_code == 200
                        }

                        print(f"   ✅ {endpoint}: {response_time:.3f}s")

                    except Exception as e:
                        api_results[endpoint] = {'error': str(e), 'success': False}
                        print(f"   ❌ {endpoint}: {e}")

                dataset_results['api_performance'] = api_results

                # Test Time Period Switching
                print("⏱️ Testing Time Period Switching...")

                for period_info in time_periods:
                    period_key = period_info['key']
                    button_text = period_info['button_text']
                    period_name = period_info['name']

                    print(f"   Testing {period_name} period...")

                    try:
                        # Time the period switch
                        switch_start = time.time()
                        page.click(f'button:has-text("{button_text}")')
                        page.wait_for_timeout(3000)  # Allow time for processing

                        switch_time = time.time() - switch_start

                        # Capture screenshots
                        screenshot_base = f"screenshots/comprehensive/{dataset_key}/{period_key}"

                        # Full dashboard screenshot
                        page.screenshot(path=f"{screenshot_base}_full_dashboard.png", full_page=True)

                        # Try to capture specific sections
                        try:
                            exec_section = page.query_selector('.executive-dashboard, .exec-summary, .summary-section')
                            if exec_section:
                                exec_section.screenshot(path=f"{screenshot_base}_executive.png")
                        except:
                            pass

                        try:
                            sensor_section = page.query_selector('.sensor-metrics, .grouped-container, .floor-section')
                            if sensor_section:
                                sensor_section.screenshot(path=f"{screenshot_base}_sensors.png")
                        except:
                            pass

                        dataset_results['time_period_tests'][period_key] = {
                            'switch_time': round(switch_time, 2),
                            'status': 'success',
                            'screenshots_captured': True
                        }

                        print(f"     ✅ {period_name}: {switch_time:.2f}s")

                    except Exception as e:
                        dataset_results['time_period_tests'][period_key] = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        print(f"     ❌ {period_name}: {e}")

                # Calculate performance summary
                api_times = [r.get('response_time', 0) for r in api_results.values() if r.get('response_time')]
                switch_times = [p.get('switch_time', 0) for p in dataset_results['time_period_tests'].values() if p.get('switch_time')]

                dataset_results['performance_summary'] = {
                    'dataset_load_time': dataset_results['load_performance']['dataset_load_time'],
                    'avg_api_response_time': round(sum(api_times) / len(api_times), 3) if api_times else 0,
                    'avg_period_switch_time': round(sum(switch_times) / len(switch_times), 2) if switch_times else 0,
                    'successful_api_calls': sum(1 for r in api_results.values() if r.get('success')),
                    'total_api_calls': len(api_results),
                    'successful_period_switches': len([p for p in dataset_results['time_period_tests'].values() if p.get('status') == 'success'])
                }

                perf = dataset_results['performance_summary']
                print(f"📈 Performance Summary:")
                print(f"     Dataset Load: {perf['dataset_load_time']}s")
                print(f"     Avg API Response: {perf['avg_api_response_time']}s")
                print(f"     Avg Period Switch: {perf['avg_period_switch_time']}s")
                print(f"     API Success Rate: {perf['successful_api_calls']}/{perf['total_api_calls']}")

            except Exception as e:
                print(f"❌ Dataset {dataset_name} failed: {e}")
                dataset_results['status'] = 'failed'
                dataset_results['error'] = str(e)

            results['completed_datasets'][dataset_key] = dataset_results
            print(f"✅ Completed {dataset_name}")

        browser.close()

    # Save results
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'remaining_datasets_results_{timestamp_str}.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Remaining datasets testing complete!")
    return results

if __name__ == "__main__":
    test_remaining_datasets()