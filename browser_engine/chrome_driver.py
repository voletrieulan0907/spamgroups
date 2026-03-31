"""
chrome_driver.py - Quản lý Chrome WebDriver (selenium-manager only)
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ChromiumDriver:

    BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
    PROFILES_DIR = os.path.join(BASE_DIR, '..', 'data', 'profiles')

    @staticmethod
    def get_driver(profile_name: str,
                   start_url: str = "https://www.facebook.com",
                   headless: bool = False,
                   no_images: bool = False):

        os.makedirs(ChromiumDriver.PROFILES_DIR, exist_ok=True)

        profile_dir = os.path.normpath(
            os.path.join(ChromiumDriver.PROFILES_DIR, profile_name)
        )
        os.makedirs(profile_dir, exist_ok=True)

        opts = Options()

        # ===== PROFILE =====
        opts.add_argument(f"--user-data-dir={profile_dir}")
        opts.add_argument("--profile-directory=Default")

        # ===== BASIC =====
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-popup-blocking")
        opts.add_argument("--window-size=390,844")

        # ===== USER AGENT =====
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

        # ===== HEADLESS =====
        if headless:
            opts.add_argument("--headless=new")

        # ===== ANTI DETECT =====
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        # ===== PERFORMANCE LOGGING (để lấy network/graphql logs) =====
        opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = None
        try:
            driver = webdriver.Chrome(options=opts)

            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            print(f"[SUCCESS] Chrome '{profile_name}' đã mở thành công", flush=True)
            driver.get(start_url)
            return driver

        except Exception as e:
            print(f"[ERROR] Lỗi mở Chrome: {e}", flush=True)
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return None

    @staticmethod
    def close_driver(driver):
        if driver is not None:
            try:
                driver.quit()
                print("[INFO] Chrome đã đóng.", flush=True)
            except Exception as e:
                print(f"[ERROR] Lỗi đóng Chrome: {e}", flush=True)