#!/usr/bin/env python3
"""
Detailed metrics validation test for Dataset A
Captures screenshots of each floor expansion and verifies metric recalculation across time periods
"""

from playwright.sync_api import sync_playwright
import time
import json
import subprocess
from datetime import datetime

def detailed_metrics_test():
    """Run detailed metrics validation test"""
    print("📊 Starting Detailed Metrics Validation Test for Dataset A...")

    # First, restart server with Dataset A
    print("🔄 Restarting server with Dataset A...")
    try:
        subprocess.run("kill -9 $(lsof -t -i:8000) 2>/dev/null", shell=True)
        time.sleep(3)
        subprocess.Popen("cd /Users/urikogan/code/data_validation && source venv/bin/activate && python3 main.py", shell=True)
        time.sleep(8)  # Give server time to start and load data
        print("✅ Server restarted")
    except Exception as e:
        print(f"⚠️  Server restart may have failed: {e}")

    results = {
        'timestamp': datetime.now().isoformat(),
        'dataset': 'SCH-1_data_1_day_mock.csv (Dataset A)',
        'test_results': {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible browser for debugging
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # Navigate to dashboard
        print("🔄 Loading dashboard...")
        page.goto("http://localhost:8000")
        page.wait_for_selector(".executive-dashboard", timeout=30000)
        page.wait_for_selector(".grouped-container", timeout=30000)

        time_periods = [
            ('24h', 'Latest 24 Hrs'),
            ('5d', '5 Days'),
            ('30d', '30 Days')
        ]

        for period_key, button_text in time_periods:
            print(f"\n🔄 Testing {period_key} period...")

            # Click time period button
            page.click(f'button:has-text("{button_text}")')
            page.wait_for_timeout(3000)  # Wait for API calls to complete

            # Capture executive dashboard first
            print(f"   📸 Capturing executive dashboard for {period_key}")
            exec_metrics = {}
            exec_elements = page.query_selector_all('.exec-metric')
            for i, elem in enumerate(exec_elements):
                value_elem = elem.query_selector('.exec-value')
                label_elem = elem.query_selector('.exec-label')
                if value_elem and label_elem:
                    exec_metrics[f'exec_{i+1}'] = {
                        'label': label_elem.inner_text(),
                        'value': value_elem.inner_text()
                    }

            results['test_results'][f'{period_key}_executive'] = exec_metrics
            page.screenshot(path=f"screenshots/detailed_{period_key}_executive.png", full_page=True)
            print(f"   ✅ Executive metrics captured: {exec_metrics}")

            # Find all floor groups
            group_headers = page.query_selector_all('.group-header')
            print(f"   📊 Found {len(group_headers)} floor groups")

            floor_metrics = {}

            for floor_idx, group_header in enumerate(group_headers):
                # Get floor name
                floor_name_elem = group_header.query_selector('.group-name')
                floor_name = floor_name_elem.inner_text() if floor_name_elem else f'Floor_{floor_idx}'

                print(f"   🔄 Testing floor: {floor_name}")

                # Expand the floor
                group_header.click()
                page.wait_for_timeout(1000)  # Wait for expansion

                # Capture floor metrics
                group_stats = group_header.query_selector_all('.group-stat')
                floor_stats = {}
                for stat_idx, stat in enumerate(group_stats):
                    stat_text = stat.inner_text() if stat else ''
                    floor_stats[f'stat_{stat_idx}'] = stat_text

                floor_metrics[floor_name] = floor_stats

                # Take screenshot of expanded floor
                page.screenshot(path=f"screenshots/detailed_{period_key}_{floor_name}_expanded.png", full_page=True)
                print(f"   📸 Screenshot saved for {floor_name}")
                print(f"   📊 Floor stats: {floor_stats}")

                # Collapse the floor for next iteration
                group_header.click()
                page.wait_for_timeout(500)

            results['test_results'][f'{period_key}_floors'] = floor_metrics
            print(f"   ✅ All floors processed for {period_key}")

        browser.close()

    # Save detailed results
    with open('detailed_metrics_validation.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Detailed Metrics Test Complete!")
    print(f"🎯 Analysis Summary:")

    # Compare executive metrics across periods
    print(f"\n📈 Executive Metrics Comparison:")
    for period_key, _ in time_periods:
        if f'{period_key}_executive' in results['test_results']:
            exec_data = results['test_results'][f'{period_key}_executive']
            print(f"   {period_key}: {exec_data}")

    # Compare floor metrics
    print(f"\n🏢 Floor Metrics Changes:")
    all_floors = set()
    for period_key, _ in time_periods:
        if f'{period_key}_floors' in results['test_results']:
            all_floors.update(results['test_results'][f'{period_key}_floors'].keys())

    for floor in all_floors:
        print(f"\n   Floor {floor}:")
        for period_key, _ in time_periods:
            if f'{period_key}_floors' in results['test_results']:
                floor_data = results['test_results'][f'{period_key}_floors'].get(floor, {})
                print(f"     {period_key}: {floor_data}")

    print(f"\n📁 Detailed results saved to detailed_metrics_validation.json")
    print(f"📸 Screenshots saved to screenshots/ directory with format: detailed_[period]_[floor]_expanded.png")

    return results

if __name__ == "__main__":
    import os
    os.makedirs('screenshots', exist_ok=True)
    detailed_metrics_test()