#!/usr/bin/env python3
"""
Frontend Data Validation Test
Tests whether data actually displays correctly on the frontend (not just API responses)
"""

from playwright.sync_api import sync_playwright
import time
import json
import requests
from datetime import datetime
import os

def test_frontend_data_validation():
    """Test that frontend actually displays real data, not zeros"""

    datasets_to_test = [
        {
            'key': '30_days_test_subset',
            'name': '30 Days / 4 Sensors + 4 BV',
            'expected_non_zero': True  # Should have real data
        },
        {
            'key': '1_day_mock',
            'name': '1 Day / 100 Sensors',
            'expected_non_zero': True  # Should have real data
        },
        {
            'key': '5_days_mock',
            'name': '5 Days / 100 Sensors',
            'expected_non_zero': True  # Should have real data
        }
    ]

    time_periods = ['24h', '5d', '30d']

    results = {
        'timestamp': datetime.now().isoformat(),
        'critical_findings': [],
        'dataset_results': {},
        'overall_status': 'unknown'
    }

    print("🔍 FRONTEND DATA VALIDATION TEST")
    print("Testing whether data actually displays on frontend...")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        for dataset_info in datasets_to_test:
            dataset_key = dataset_info['key']
            dataset_name = dataset_info['name']

            print(f"\n📊 Testing Dataset: {dataset_name}")
            print("-" * 50)

            dataset_results = {
                'dataset_info': dataset_info,
                'load_time': 0,
                'data_validation': {},
                'time_period_validation': {},
                'issues_found': [],
                'data_loads_correctly': False
            }

            try:
                # Load dashboard
                load_start = time.time()
                page.goto("http://localhost:8000")
                page.wait_for_selector(".upload-section", timeout=30000)

                # Load dataset
                page.click(f'button:has-text("{dataset_name}")')
                page.wait_for_selector('#uploadStatus .success', timeout=60000)

                dataset_results['load_time'] = round(time.time() - load_start, 2)
                print(f"   ✅ Dataset loaded in {dataset_results['load_time']}s")

                # Wait for data to actually load on frontend
                print("   ⏳ Waiting for frontend data to load...")
                time.sleep(5)  # Give time for frontend to process data

                # Test each time period
                for period in time_periods:
                    print(f"   🔍 Testing {period} period...")

                    # Click time period button
                    if period == '24h':
                        page.click('button:has-text("Latest 24 Hrs")')
                    elif period == '5d':
                        page.click('button:has-text("5 Days")')
                    else:  # 30d
                        page.click('button:has-text("30 Days")')

                    # Wait for data to update
                    time.sleep(3)

                    # Extract actual displayed values
                    period_validation = {
                        'period': period,
                        'executive_metrics': {},
                        'sensor_data_found': False,
                        'data_appears_valid': False,
                        'screenshot_file': f'screenshots/validation/{dataset_key}_{period}_validation.png'
                    }

                    try:
                        # Look for executive metrics values
                        metric_elements = page.query_selector_all('.metric-value, .exec-value, .stat-value')
                        executive_values = []

                        for elem in metric_elements:
                            try:
                                text = elem.inner_text().strip()
                                if text and text != '0.0%' and text != '0%' and text != '0':
                                    executive_values.append(text)
                            except:
                                pass

                        period_validation['executive_metrics']['non_zero_values_found'] = len(executive_values)
                        period_validation['executive_metrics']['sample_values'] = executive_values[:5]

                        # Check for percentage values that are not 0.0%
                        percentage_elements = page.query_selector_all('text-content=/[0-9]+\.[0-9]+%/')
                        non_zero_percentages = []
                        for elem in percentage_elements:
                            try:
                                text = elem.inner_text().strip()
                                if text and '0.0%' not in text and '0%' not in text:
                                    non_zero_percentages.append(text)
                            except:
                                pass

                        period_validation['executive_metrics']['non_zero_percentages'] = non_zero_percentages[:3]

                        # Check for sensor/zone data
                        sensor_rows = page.query_selector_all('.sensor-row, .zone-row, .floor-section')
                        period_validation['sensor_data_found'] = len(sensor_rows) > 0

                        # Determine if data appears valid
                        has_non_zero_executive = len(executive_values) > 0 or len(non_zero_percentages) > 0
                        has_sensor_data = period_validation['sensor_data_found']

                        period_validation['data_appears_valid'] = has_non_zero_executive or has_sensor_data

                        # Capture screenshot for evidence
                        os.makedirs('screenshots/validation', exist_ok=True)
                        page.screenshot(path=period_validation['screenshot_file'], full_page=True)

                        # Log findings
                        if period_validation['data_appears_valid']:
                            print(f"     ✅ {period}: Data appears valid - found {len(executive_values)} non-zero values")
                            if executive_values:
                                print(f"       Sample values: {executive_values[:3]}")
                        else:
                            print(f"     ❌ {period}: NO VALID DATA FOUND - all values appear to be zero")
                            dataset_results['issues_found'].append(f"{period}: All displayed values are zero")
                            results['critical_findings'].append(f"{dataset_name} {period}: Frontend shows zero values")

                    except Exception as e:
                        period_validation['error'] = str(e)
                        print(f"     ❌ {period}: Error extracting data - {e}")
                        dataset_results['issues_found'].append(f"{period}: Data extraction error - {e}")

                    dataset_results['time_period_validation'][period] = period_validation

                # Overall dataset assessment
                valid_periods = [p for p in dataset_results['time_period_validation'].values()
                               if p.get('data_appears_valid', False)]

                dataset_results['data_loads_correctly'] = len(valid_periods) > 0
                dataset_results['valid_periods_count'] = len(valid_periods)
                dataset_results['total_periods_tested'] = len(time_periods)

                if dataset_results['data_loads_correctly']:
                    print(f"   ✅ Dataset validation: {len(valid_periods)}/{len(time_periods)} periods show valid data")
                else:
                    print(f"   🚨 CRITICAL: Dataset shows NO valid data in any time period")
                    results['critical_findings'].append(f"{dataset_name}: NO valid data in any time period")

            except Exception as e:
                print(f"   ❌ Dataset test failed: {e}")
                dataset_results['test_error'] = str(e)
                results['critical_findings'].append(f"{dataset_name}: Test failed - {e}")

            results['dataset_results'][dataset_key] = dataset_results

        browser.close()

    # Overall Assessment
    datasets_with_valid_data = [d for d in results['dataset_results'].values()
                              if d.get('data_loads_correctly', False)]

    total_datasets = len(results['dataset_results'])
    valid_datasets = len(datasets_with_valid_data)

    if valid_datasets == 0:
        results['overall_status'] = 'CRITICAL_FAILURE'
        results['summary'] = "🚨 CRITICAL: NO datasets display valid data on frontend"
    elif valid_datasets < total_datasets:
        results['overall_status'] = 'PARTIAL_FAILURE'
        results['summary'] = f"⚠️ PARTIAL: {valid_datasets}/{total_datasets} datasets display valid data"
    else:
        results['overall_status'] = 'SUCCESS'
        results['summary'] = f"✅ SUCCESS: All {valid_datasets} datasets display valid data"

    # Save detailed results
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'frontend_validation_results_{timestamp_str}.json'

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print final report
    print("\n" + "="*70)
    print("🎯 FRONTEND DATA VALIDATION RESULTS")
    print("="*70)

    print(f"\n📊 Overall Status: {results['overall_status']}")
    print(f"📝 Summary: {results['summary']}")

    if results['critical_findings']:
        print(f"\n🚨 Critical Issues Found ({len(results['critical_findings'])}):")
        for issue in results['critical_findings']:
            print(f"   • {issue}")

    print(f"\n📁 Detailed Results:")
    print(f"   • Full results: {results_file}")
    print(f"   • Screenshots: screenshots/validation/")

    for dataset_key, dataset_data in results['dataset_results'].items():
        valid_count = dataset_data.get('valid_periods_count', 0)
        total_count = dataset_data.get('total_periods_tested', 0)
        status = "✅" if dataset_data.get('data_loads_correctly') else "❌"
        print(f"   • {dataset_key}: {status} {valid_count}/{total_count} periods valid")

    return results

if __name__ == "__main__":
    test_frontend_data_validation()