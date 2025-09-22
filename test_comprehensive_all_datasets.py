#!/usr/bin/env python3
"""
Comprehensive testing script for all ODCV Analytics Dashboard datasets
Tests load times, executive metrics, sensor/BMS metrics, and UI across all time periods
Generates detailed performance report with screenshots
"""

from playwright.sync_api import sync_playwright
import time
import json
import requests
from datetime import datetime
import os

def test_comprehensive_all_datasets():
    """Test all datasets comprehensively with detailed performance analysis"""

    # Test configuration - exclude the large 30 days/100 sensors dataset as requested
    datasets_to_test = [
        {
            'key': '30_days_test_subset',
            'name': '30 Days / 4 Sensors + 4 BV',
            'description': 'Test dataset with known mappings'
        },
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
        'test_summary': {},
        'dataset_results': {},
        'performance_analysis': {},
        'findings': []
    }

    print("🔬 Starting Comprehensive All Datasets Testing...")
    print(f"📋 Testing {len(datasets_to_test)} datasets across {len(time_periods)} time periods")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # Create organized screenshot directories
        os.makedirs('screenshots/comprehensive', exist_ok=True)
        for dataset in datasets_to_test:
            os.makedirs(f'screenshots/comprehensive/{dataset["key"]}', exist_ok=True)

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
                'ui_screenshots': {},
                'issues_found': []
            }

            # Step 1: Load Dashboard and Dataset
            print("📊 Step 1: Loading Dashboard and Dataset")
            start_time = time.time()

            page.goto("http://localhost:8000")
            page.wait_for_selector(".upload-section", timeout=30000)

            # Capture initial state
            page.screenshot(path=f"screenshots/comprehensive/{dataset_key}/00_initial_dashboard.png", full_page=True)

            # Load the dataset
            dataset_load_start = time.time()
            try:
                page.click(f'button:has-text("{dataset_name}")')
                page.wait_for_selector('#uploadStatus .success', timeout=60000)
                dataset_load_time = time.time() - dataset_load_start

                dataset_results['load_performance']['dataset_load_time'] = round(dataset_load_time, 2)
                dataset_results['load_performance']['status'] = 'success'

                print(f"   ✅ Dataset loaded in {dataset_load_time:.2f} seconds")

                # Get dataset info from status
                current_dataset = page.query_selector('#currentDatasetName')
                if current_dataset:
                    dataset_results['load_performance']['display_name'] = current_dataset.inner_text()

                # Capture post-load state
                page.screenshot(path=f"screenshots/comprehensive/{dataset_key}/01_dataset_loaded.png", full_page=True)

            except Exception as e:
                dataset_results['load_performance']['status'] = 'failed'
                dataset_results['load_performance']['error'] = str(e)
                dataset_results['issues_found'].append(f"Dataset loading failed: {e}")
                print(f"   ❌ Dataset loading failed: {e}")
                continue

            # Step 2: Test API Performance for this dataset
            print("🔧 Step 2: Testing API Performance")
            api_endpoints = [
                '/api/health',
                '/api/sensors',
                '/api/dashboard/metrics?period=24h',
                '/api/dashboard/metrics?period=5d',
                '/api/dashboard/metrics?period=30d',
                '/api/sensors/metrics?period=24h',
                '/api/sensors/metrics?period=5d',
                '/api/sensors/metrics?period=30d'
            ]

            api_results = {}
            for endpoint in api_endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"http://localhost:8000{endpoint}")
                    response_time = time.time() - start_time

                    api_results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': round(response_time, 3),
                        'success': response.status_code == 200,
                        'content_length': len(response.text)
                    }

                    if response.status_code == 200:
                        print(f"   ✅ {endpoint}: {response_time:.3f}s")
                    else:
                        print(f"   ❌ {endpoint}: {response.status_code}")
                        dataset_results['issues_found'].append(f"API {endpoint} returned {response.status_code}")

                except Exception as e:
                    api_results[endpoint] = {'error': str(e), 'success': False}
                    print(f"   ❌ {endpoint}: Exception - {e}")
                    dataset_results['issues_found'].append(f"API {endpoint} exception: {e}")

            dataset_results['api_performance'] = api_results

            # Step 3: Test Time Period Switching with Screenshots
            print("⏱️ Step 3: Testing Time Period Switching")

            for period_info in time_periods:
                period_key = period_info['key']
                button_text = period_info['button_text']
                period_name = period_info['name']

                print(f"   Testing {period_name} period...")

                period_results = {
                    'period_info': period_info,
                    'switch_performance': {},
                    'metrics_captured': {},
                    'screenshot_files': {}
                }

                try:
                    # Time the period switch
                    switch_start = time.time()
                    page.click(f'button:has-text("{button_text}")')

                    # Wait for any loading/updating to complete
                    page.wait_for_timeout(2000)  # Allow time for API calls and UI updates

                    switch_time = time.time() - switch_start
                    period_results['switch_performance']['switch_time'] = round(switch_time, 2)
                    period_results['switch_performance']['status'] = 'success'

                    print(f"     ✅ Switched to {period_name} in {switch_time:.2f}s")

                    # Capture comprehensive screenshots
                    screenshot_base = f"screenshots/comprehensive/{dataset_key}/{period_key}"

                    # Full dashboard screenshot
                    full_screenshot = f"{screenshot_base}_full_dashboard.png"
                    page.screenshot(path=full_screenshot, full_page=True)
                    period_results['screenshot_files']['full_dashboard'] = full_screenshot

                    # Capture specific UI elements if they exist
                    try:
                        # Executive dashboard section
                        exec_section = page.query_selector('.executive-dashboard, .exec-summary, .summary-section')
                        if exec_section:
                            exec_screenshot = f"{screenshot_base}_executive.png"
                            exec_section.screenshot(path=exec_screenshot)
                            period_results['screenshot_files']['executive'] = exec_screenshot
                    except:
                        pass

                    try:
                        # Sensor metrics section
                        sensor_section = page.query_selector('.sensor-metrics, .grouped-container, .floor-section')
                        if sensor_section:
                            sensor_screenshot = f"{screenshot_base}_sensors.png"
                            sensor_section.screenshot(path=sensor_screenshot)
                            period_results['screenshot_files']['sensors'] = sensor_screenshot
                    except:
                        pass

                    # Extract any visible metrics from the page
                    try:
                        # Look for executive metrics
                        exec_metrics = {}
                        metric_elements = page.query_selector_all('.metric-value, .exec-value, .stat-value')
                        for i, elem in enumerate(metric_elements[:10]):  # Limit to first 10
                            try:
                                value = elem.inner_text().strip()
                                if value:
                                    exec_metrics[f'metric_{i+1}'] = value
                            except:
                                pass

                        if exec_metrics:
                            period_results['metrics_captured']['executive'] = exec_metrics

                        # Look for sensor count or other info
                        sensor_rows = page.query_selector_all('.sensor-row, .zone-row')
                        if sensor_rows:
                            period_results['metrics_captured']['sensor_count'] = len(sensor_rows)

                    except Exception as e:
                        period_results['metrics_captured']['extraction_error'] = str(e)

                    print(f"     📸 Screenshots captured for {period_name}")

                except Exception as e:
                    period_results['switch_performance']['status'] = 'failed'
                    period_results['switch_performance']['error'] = str(e)
                    dataset_results['issues_found'].append(f"Time period {period_name} switch failed: {e}")
                    print(f"     ❌ {period_name} switch failed: {e}")

                dataset_results['time_period_tests'][period_key] = period_results

            # Step 4: Performance Summary for this dataset
            print("📈 Step 4: Performance Summary")

            api_times = [r.get('response_time', 0) for r in api_results.values() if r.get('response_time')]
            switch_times = [p.get('switch_performance', {}).get('switch_time', 0)
                          for p in dataset_results['time_period_tests'].values()]

            dataset_results['performance_summary'] = {
                'dataset_load_time': dataset_results['load_performance'].get('dataset_load_time', 0),
                'avg_api_response_time': round(sum(api_times) / len(api_times), 3) if api_times else 0,
                'max_api_response_time': max(api_times) if api_times else 0,
                'avg_period_switch_time': round(sum(switch_times) / len(switch_times), 2) if switch_times else 0,
                'successful_api_calls': sum(1 for r in api_results.values() if r.get('success', False)),
                'total_api_calls': len(api_results),
                'successful_period_switches': sum(1 for p in dataset_results['time_period_tests'].values()
                                                if p.get('switch_performance', {}).get('status') == 'success'),
                'total_screenshots': sum(len(p.get('screenshot_files', {}))
                                       for p in dataset_results['time_period_tests'].values())
            }

            perf = dataset_results['performance_summary']
            print(f"     Dataset Load: {perf['dataset_load_time']}s")
            print(f"     Avg API Response: {perf['avg_api_response_time']}s")
            print(f"     Avg Period Switch: {perf['avg_period_switch_time']}s")
            print(f"     API Success Rate: {perf['successful_api_calls']}/{perf['total_api_calls']}")
            print(f"     Screenshots Captured: {perf['total_screenshots']}")

            results['dataset_results'][dataset_key] = dataset_results
            print(f"✅ Completed testing {dataset_name}")

        browser.close()

    # Generate comprehensive analysis
    print("\n📊 Generating Comprehensive Analysis...")

    # Overall performance analysis
    all_load_times = [d['performance_summary']['dataset_load_time']
                     for d in results['dataset_results'].values()]
    all_api_times = [d['performance_summary']['avg_api_response_time']
                    for d in results['dataset_results'].values()]
    all_switch_times = [d['performance_summary']['avg_period_switch_time']
                       for d in results['dataset_results'].values()]

    results['performance_analysis'] = {
        'overall_stats': {
            'datasets_tested': len(results['dataset_results']),
            'total_screenshots': sum(d['performance_summary']['total_screenshots']
                                   for d in results['dataset_results'].values()),
            'avg_dataset_load_time': round(sum(all_load_times) / len(all_load_times), 2) if all_load_times else 0,
            'avg_api_response_time': round(sum(all_api_times) / len(all_api_times), 3) if all_api_times else 0,
            'avg_period_switch_time': round(sum(all_switch_times) / len(all_switch_times), 2) if all_switch_times else 0
        },
        'performance_rankings': {
            'fastest_loading_dataset': min(results['dataset_results'].items(),
                                         key=lambda x: x[1]['performance_summary']['dataset_load_time'])[0] if results['dataset_results'] else None,
            'slowest_loading_dataset': max(results['dataset_results'].items(),
                                         key=lambda x: x[1]['performance_summary']['dataset_load_time'])[0] if results['dataset_results'] else None,
            'best_api_performance': min(results['dataset_results'].items(),
                                      key=lambda x: x[1]['performance_summary']['avg_api_response_time'])[0] if results['dataset_results'] else None
        }
    }

    # Findings and issues
    all_issues = []
    for dataset_key, dataset_data in results['dataset_results'].items():
        for issue in dataset_data.get('issues_found', []):
            all_issues.append(f"{dataset_key}: {issue}")

    results['findings'] = {
        'total_issues_found': len(all_issues),
        'issues_by_dataset': {k: len(v.get('issues_found', [])) for k, v in results['dataset_results'].items()},
        'all_issues': all_issues,
        'recommendations': []
    }

    # Generate recommendations based on findings
    if results['performance_analysis']['overall_stats']['avg_dataset_load_time'] > 5:
        results['findings']['recommendations'].append("Dataset loading times exceed 5 seconds - consider optimization")

    if results['performance_analysis']['overall_stats']['avg_api_response_time'] > 0.5:
        results['findings']['recommendations'].append("API response times exceed 500ms - consider caching or optimization")

    if results['findings']['total_issues_found'] > 0:
        results['findings']['recommendations'].append("Issues found during testing - review error handling and data validation")

    # Save comprehensive results
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'comprehensive_test_results_{timestamp_str}.json'

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Generate summary report
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE TESTING RESULTS SUMMARY")
    print("="*80)

    print(f"\n📊 Overall Performance:")
    perf = results['performance_analysis']['overall_stats']
    print(f"   • Datasets Tested: {perf['datasets_tested']}")
    print(f"   • Total Screenshots: {perf['total_screenshots']}")
    print(f"   • Average Dataset Load Time: {perf['avg_dataset_load_time']}s")
    print(f"   • Average API Response Time: {perf['avg_api_response_time']}s")
    print(f"   • Average Period Switch Time: {perf['avg_period_switch_time']}s")

    print(f"\n🏆 Performance Rankings:")
    rankings = results['performance_analysis']['performance_rankings']
    if rankings['fastest_loading_dataset']:
        print(f"   • Fastest Loading: {rankings['fastest_loading_dataset']}")
    if rankings['slowest_loading_dataset']:
        print(f"   • Slowest Loading: {rankings['slowest_loading_dataset']}")
    if rankings['best_api_performance']:
        print(f"   • Best API Performance: {rankings['best_api_performance']}")

    print(f"\n🔍 Issues and Findings:")
    findings = results['findings']
    print(f"   • Total Issues Found: {findings['total_issues_found']}")
    for dataset, issue_count in findings['issues_by_dataset'].items():
        print(f"   • {dataset}: {issue_count} issues")

    if findings['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in findings['recommendations']:
            print(f"   • {rec}")

    print(f"\n📁 Detailed Results:")
    print(f"   • Full results saved to: {results_file}")
    print(f"   • Screenshots organized in: screenshots/comprehensive/")
    print(f"   • Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results

if __name__ == "__main__":
    test_comprehensive_all_datasets()