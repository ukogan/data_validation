#!/usr/bin/env python3
"""
Comprehensive API testing script for ODCV Analytics Dashboard
Tests all API endpoints with different datasets and time periods
"""

import requests
import json
import time
from datetime import datetime

def test_comprehensive_api():
    """Test all API endpoints comprehensively"""

    base_url = "http://localhost:8000"
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_results': {}
    }

    print("🔧 Starting Comprehensive API Testing...")

    # Test 1: Health Check
    print("🔄 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/api/health")
        health_data = response.json()
        results['test_results']['health_check'] = {
            'status': response.status_code,
            'response_time': response.elapsed.total_seconds(),
            'data_loaded': health_data.get('data_loaded', False),
            'status_level': health_data.get('status', 'unknown')
        }
        print(f"   ✅ Health check: {response.status_code} - {health_data.get('status', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        results['test_results']['health_check'] = {'error': str(e)}

    # Test 2: Dataset Loading
    print("🔄 Test 2: Dataset Loading")
    datasets_to_test = [
        '30_days_test_subset',
        '1_day_mock',
        '5_days_mock'
    ]

    dataset_results = {}

    for dataset in datasets_to_test:
        print(f"   Testing dataset: {dataset}")
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/api/load-dataset",
                                   json={"dataset": dataset})
            load_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                dataset_results[dataset] = {
                    'status': 'success',
                    'load_time': round(load_time, 2),
                    'records_count': data.get('records_count', 0),
                    'sensors_found': data.get('sensors_found', 0),
                    'zones_found': data.get('zones_found', 0),
                    'mappings_created': data.get('mappings_created', 0)
                }
                print(f"   ✅ {dataset}: {data.get('records_count', 0)} records, {load_time:.2f}s")
            else:
                dataset_results[dataset] = {
                    'status': 'failed',
                    'status_code': response.status_code,
                    'error': response.text
                }
                print(f"   ❌ {dataset}: Failed - {response.status_code}")

        except Exception as e:
            dataset_results[dataset] = {'status': 'error', 'error': str(e)}
            print(f"   ❌ {dataset}: Error - {e}")

    results['test_results']['dataset_loading'] = dataset_results

    # Test 3: API Endpoints with Data Loaded (using 30_days_test_subset)
    print("🔄 Test 3: API Endpoints with Data Loaded")

    # Load the test dataset first
    requests.post(f"{base_url}/api/load-dataset", json={"dataset": "30_days_test_subset"})

    api_endpoints = [
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
        print(f"   Testing: {endpoint}")
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}")
            response_time = time.time() - start_time

            result = {
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'content_length': len(response.text)
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result['has_data'] = len(str(data)) > 50
                    result['data_type'] = type(data).__name__

                    # Check for specific data structures
                    if isinstance(data, dict):
                        result['keys'] = list(data.keys())[:5]  # First 5 keys
                    elif isinstance(data, list):
                        result['list_length'] = len(data)

                    print(f"   ✅ {endpoint}: {response.status_code} - {response_time:.3f}s")
                except json.JSONDecodeError:
                    result['json_error'] = True
                    print(f"   ⚠️  {endpoint}: Invalid JSON response")
            else:
                result['error_text'] = response.text[:200]
                print(f"   ❌ {endpoint}: {response.status_code}")

            api_results[endpoint] = result

        except Exception as e:
            api_results[endpoint] = {'error': str(e)}
            print(f"   ❌ {endpoint}: Exception - {e}")

    results['test_results']['api_endpoints'] = api_results

    # Test 4: Time Period Consistency
    print("🔄 Test 4: Time Period Consistency")

    time_periods = ['24h', '5d', '30d']
    consistency_results = {}

    for period in time_periods:
        print(f"   Testing period: {period}")
        try:
            # Test dashboard metrics
            dashboard_response = requests.get(f"{base_url}/api/dashboard/metrics?period={period}")
            sensor_response = requests.get(f"{base_url}/api/sensors/metrics?period={period}")

            consistency_results[period] = {
                'dashboard_status': dashboard_response.status_code,
                'sensor_status': sensor_response.status_code,
                'both_successful': dashboard_response.status_code == 200 and sensor_response.status_code == 200
            }

            if dashboard_response.status_code == 200 and sensor_response.status_code == 200:
                print(f"   ✅ {period}: Both endpoints successful")
            else:
                print(f"   ⚠️  {period}: Status codes - Dashboard: {dashboard_response.status_code}, Sensors: {sensor_response.status_code}")

        except Exception as e:
            consistency_results[period] = {'error': str(e)}
            print(f"   ❌ {period}: Error - {e}")

    results['test_results']['time_period_consistency'] = consistency_results

    # Test 5: Error Handling - No Data Loaded
    print("🔄 Test 5: Error Handling - No Data Loaded")

    # Clear data by loading the dashboard (which clears any loaded data)
    requests.get(f"{base_url}/")

    error_test_endpoints = [
        '/api/dashboard/metrics?period=24h',
        '/api/sensors/metrics?period=24h'
    ]

    error_results = {}

    for endpoint in error_test_endpoints:
        print(f"   Testing no-data error: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}")
            error_results[endpoint] = {
                'status_code': response.status_code,
                'returns_error': response.status_code >= 400,
                'response_preview': response.text[:150]
            }

            if response.status_code >= 400:
                print(f"   ✅ {endpoint}: Properly returns error {response.status_code}")
            else:
                print(f"   ⚠️  {endpoint}: Should return error but got {response.status_code}")

        except Exception as e:
            error_results[endpoint] = {'error': str(e)}
            print(f"   ❌ {endpoint}: Exception - {e}")

    results['test_results']['error_handling'] = error_results

    # Test 6: Performance Benchmarks
    print("🔄 Test 6: Performance Benchmarks")

    # Reload test dataset for performance testing
    requests.post(f"{base_url}/api/load-dataset", json={"dataset": "30_days_test_subset"})

    performance_endpoints = [
        '/api/dashboard/metrics?period=24h',
        '/api/sensors/metrics?period=24h',
        '/api/sensors'
    ]

    performance_results = {}

    for endpoint in performance_endpoints:
        times = []
        print(f"   Benchmarking: {endpoint} (5 runs)")

        for run in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}")
                end_time = time.time()

                if response.status_code == 200:
                    times.append(end_time - start_time)

            except Exception as e:
                print(f"   ⚠️  Run {run+1} failed: {e}")

        if times:
            performance_results[endpoint] = {
                'avg_time': round(sum(times) / len(times), 3),
                'min_time': round(min(times), 3),
                'max_time': round(max(times), 3),
                'successful_runs': len(times)
            }
            print(f"   ✅ {endpoint}: Avg {performance_results[endpoint]['avg_time']}s")
        else:
            performance_results[endpoint] = {'error': 'No successful runs'}
            print(f"   ❌ {endpoint}: No successful runs")

    results['test_results']['performance_benchmarks'] = performance_results

    # Save results
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'api_test_results_{timestamp_str}.json'

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    print(f"\n🎯 Comprehensive API Testing Complete!")
    print(f"📊 Results Summary:")
    print(f"   • Health Check: {results['test_results']['health_check'].get('status', 'Failed')}")
    print(f"   • Datasets Tested: {len(dataset_results)}")
    print(f"   • API Endpoints Tested: {len(api_results)}")
    print(f"   • Performance Benchmarks: {len(performance_results)}")
    print(f"   • Full results saved to: {results_file}")

    return results

if __name__ == "__main__":
    test_comprehensive_api()