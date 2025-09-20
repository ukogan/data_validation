#!/usr/bin/env python3
"""
Quick performance test for Dataset B (5 days, 100 sensors)
Focuses on scale testing and API performance with realistic building data
"""

import time
import requests
import json
from datetime import datetime

def test_dataset_b_performance():
    """Test Dataset B performance and scaling"""
    print("📊 Starting Dataset B (5 days, 100 sensors) Testing...")

    results = {
        'timestamp': datetime.now().isoformat(),
        'dataset': 'SCH-1_data_5_days_mock.csv',
        'test_results': {}
    }

    base_url = "http://localhost:8000"

    # Test 1: API Response Times with Large Dataset
    print("🔄 Test 2.1: API Performance with 100 Sensors")

    api_endpoints = [
        '/api/sensors',
        '/api/dashboard/metrics?period=24h',
        '/api/sensors/metrics?period=24h',
        '/api/dashboard/metrics?period=5d'
    ]

    api_timings = {}
    for endpoint in api_endpoints:
        print(f"   Testing {endpoint}...")
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            api_time = time.time() - start_time
            api_timings[endpoint] = {
                'response_time': round(api_time, 3),
                'status': response.status_code
            }
            print(f"   ✅ {endpoint}: {api_time:.3f}s (Status: {response.status_code})")
        except Exception as e:
            api_timings[endpoint] = {
                'response_time': -1,
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ {endpoint}: Error - {e}")

    results['test_results']['api_response_times'] = api_timings

    # Test 2: Sensor Count Validation
    print("🔄 Test 2.2: Sensor Count and Grouping")
    try:
        sensors_response = requests.get(f"{base_url}/api/sensors", timeout=10)
        if sensors_response.status_code == 200:
            sensors = sensors_response.json()
            sensor_count = len(sensors)
            results['test_results']['sensor_count'] = sensor_count
            print(f"   ✅ Total sensors found: {sensor_count}")

            # Count presence sensors vs BMS zones
            presence_sensors = [s for s in sensors if 'presence' in s]
            bms_zones = [s for s in sensors if s.startswith('BV')]

            results['test_results']['presence_sensors'] = len(presence_sensors)
            results['test_results']['bms_zones'] = len(bms_zones)
            print(f"   ✅ Presence sensors: {len(presence_sensors)}")
            print(f"   ✅ BMS zones: {len(bms_zones)}")
        else:
            print(f"   ❌ Failed to get sensors: {sensors_response.status_code}")
    except Exception as e:
        print(f"   ❌ Sensor count test failed: {e}")

    # Test 3: Time Period Switching Performance
    print("🔄 Test 2.3: Time Period Performance at Scale")

    time_periods = ['24h', '5d']  # Skip 30d since we only have 5 days
    period_timings = {}

    for period in time_periods:
        print(f"   Testing {period} period...")
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/api/dashboard/metrics?period={period}", timeout=20)
            period_time = time.time() - start_time
            period_timings[period] = {
                'response_time': round(period_time, 3),
                'status': response.status_code
            }
            print(f"   ✅ {period} period: {period_time:.3f}s (Status: {response.status_code})")
        except Exception as e:
            period_timings[period] = {
                'response_time': -1,
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ {period} period failed: {e}")

    results['test_results']['period_switching_times'] = period_timings

    # Test 4: Executive Metrics Validation
    print("🔄 Test 2.4: Executive Metrics with Building Scale")
    try:
        exec_response = requests.get(f"{base_url}/api/dashboard/metrics?period=5d", timeout=15)
        if exec_response.status_code == 200:
            exec_data = exec_response.json()
            results['test_results']['executive_metrics_sample'] = {
                'standby_mode_percent': exec_data.get('standby_mode_percent', 'N/A'),
                'airflow_reduction_percent': exec_data.get('airflow_reduction_percent', 'N/A'),
                'data_quality_percent': exec_data.get('data_quality_percent', 'N/A')
            }
            print(f"   ✅ Standby Mode: {exec_data.get('standby_mode_percent', 'N/A')}%")
            print(f"   ✅ Airflow Reduction: {exec_data.get('airflow_reduction_percent', 'N/A')}%")
            print(f"   ✅ Data Quality: {exec_data.get('data_quality_percent', 'N/A')}%")
        else:
            print(f"   ❌ Failed to get executive metrics: {exec_response.status_code}")
    except Exception as e:
        print(f"   ❌ Executive metrics test failed: {e}")

    # Save results
    with open('test_results_dataset_b.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Dataset B Testing Complete!")
    print(f"🎯 Results Summary:")
    print(f"   • Sensor Count: {results['test_results'].get('sensor_count', 'Unknown')}")
    print(f"   • API Performance: {api_timings}")
    print(f"   • Full results saved to test_results_dataset_b.json")

    return results

if __name__ == "__main__":
    # Kill existing server and restart with new dataset
    import subprocess
    import os

    print("🔄 Restarting server with Dataset B...")
    try:
        subprocess.run("kill -9 $(lsof -t -i:8000) 2>/dev/null", shell=True)
        time.sleep(2)
        # Start server in background
        subprocess.Popen("cd /Users/urikogan/code/data_validation && source venv/bin/activate && python3 main.py", shell=True)
        time.sleep(5)  # Give server time to start
        print("✅ Server restarted")
    except Exception as e:
        print(f"⚠️  Server restart may have failed: {e}")

    # Run the test
    test_dataset_b_performance()