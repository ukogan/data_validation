#!/usr/bin/env python3
"""
Simple Playwright test for debugging dashboard issues
"""

from playwright.sync_api import sync_playwright
import time
import requests

def test_simple_dashboard():
    """Simple test to debug dashboard loading issues"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        print("📊 Simple Dashboard Test - Debug Mode")

        # Go to dashboard
        print("🔄 Loading dashboard...")
        page.goto("http://localhost:8000")
        page.wait_for_selector(".upload-section", timeout=10000)

        # Take initial screenshot
        page.screenshot(path="screenshots/debug_initial.png", full_page=True)
        print("   ✅ Initial screenshot taken")

        # Try to click the test subset button
        print("🔄 Clicking test subset button...")
        try:
            # Find all buttons and their text
            buttons = page.query_selector_all('button')
            print(f"   Found {len(buttons)} buttons:")
            for i, button in enumerate(buttons):
                button_text = button.inner_text()
                print(f"   Button {i}: '{button_text}'")

            # Try to click the test subset button specifically
            page.click('button:has-text("4 Sensors + 4 BV")')
            print("   ✅ Clicked test subset button")

            # Wait a bit and take screenshot
            time.sleep(3)
            page.screenshot(path="screenshots/debug_after_click.png", full_page=True)
            print("   ✅ Screenshot after click taken")

            # Check what's in the status div
            status_div = page.query_selector('#uploadStatus')
            if status_div:
                status_content = status_div.inner_html()
                print(f"   Status div content: {status_content}")
            else:
                print("   ❌ Status div not found")

            # Check if current dataset info was updated
            dataset_name = page.query_selector('#currentDatasetName')
            if dataset_name:
                name_text = dataset_name.inner_text()
                print(f"   Current dataset name: {name_text}")
            else:
                print("   ❌ Dataset name element not found")

        except Exception as e:
            print(f"   ❌ Button click failed: {e}")
            page.screenshot(path="screenshots/debug_error.png", full_page=True)

        # Test API directly
        print("🔄 Testing API directly...")
        try:
            response = requests.post("http://localhost:8000/api/load-dataset",
                                   json={"dataset": "30_days_test_subset"})
            print(f"   API response status: {response.status_code}")
            print(f"   API response: {response.text}")
        except Exception as e:
            print(f"   ❌ API test failed: {e}")

        # Final screenshot
        page.screenshot(path="screenshots/debug_final.png", full_page=True)
        print("   ✅ Final screenshot taken")

        browser.close()

if __name__ == "__main__":
    import os
    os.makedirs('screenshots', exist_ok=True)
    test_simple_dashboard()