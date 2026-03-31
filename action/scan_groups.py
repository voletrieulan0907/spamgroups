"""
action/scan_groups.py
"""

import os, json, time
from selenium.webdriver.common.by import By


class GroupScanner:
    # ← Bỏ "-> dict" sai ở __init__ (không phải hàm trả dict)
    def __init__(self, driver, profile_name: str):
        self.driver       = driver
        self.name_profile = profile_name
        self.path_profile = os.path.join('data', 'profile.json')
        self.profiles     = []

        if os.path.isfile(self.path_profile):
            with open(self.path_profile, 'r', encoding='utf-8') as f:
                self.profiles = json.load(f)

    def scroll_get_page(self, pixels=2000):
        """Cuộn trang cho đến hết."""
        while True:
            self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            curr  = self.driver.execute_script(
                "return window.pageYOffset + window.innerHeight;")
            total = self.driver.execute_script(
                "return document.body.scrollHeight;")
            if curr >= total:
                return

    def check_login(self) -> bool:
        """
        Kiểm tra xem đã đăng nhập Facebook chưa.
        Không nhận driver làm tham số — dùng self.driver.
        """
        # ← Kiểm tra self.driver thay vì tham số
        if self.driver is None:
            print("[GroupScanner] Driver chưa được khởi tạo.", flush=True)
            return False
        try:
            page_source = self.driver.page_source
            if '"username":"' not in page_source:
                return False

            # Cập nhật status + uid vào profile nếu chưa có
            uid = ""
            try:
                uid = page_source.split(
                    '"is_additional_profile_plus":false,"id":"')[1].split('"')[0]
            except (IndexError, ValueError):
                pass

            for profile in self.profiles:
                if profile.get('profile') == self.name_profile:
                    if profile.get('status') == 'disconnect':
                        profile['status'] = 'connected'
                    if uid:
                        profile['uid'] = uid
                    # Lưu lại
                    with open(self.path_profile, 'w', encoding='utf-8') as f:
                        json.dump(self.profiles, f, ensure_ascii=False, indent=4)
                    break

            return True

        except Exception as e:
            print(f"[GroupScanner] Lỗi check_login: {e}", flush=True)
            return False

    def get_page(self):
        """Lấy danh sách groups bằng cách duyệt index XPath tăng dần."""
        groups = []
        index = 1

        # Base path đến container chứa list groups
        BASE = (
            "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]"
            "/div[1]/div[2]/div/div/div/div/div/div/div/div/div/div[3]"
        )

        while True:
            xpath = (
                f"{BASE}/div[{index}]/div/div[1]/div[2]"
                f"/div/div[1]/span/span/div/span/a"
            )
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                ten = el.text.strip()
                url = el.get_attribute("href")
                if ten and url:
                    print(f"  [{index}] {ten} → {url}", flush=True)
                    groups.append({'name': ten, 'url': url})
                index += 1

            except Exception:
                # Không tìm thấy phần tử → hết danh sách
                print(f"  → Dừng tại index {index}, tổng: {len(groups)} groups", flush=True)
                break

        return groups

    def scan_groups(self) -> dict:
        """Truy cập trang Facebook groups và lấy danh sách."""
        try:
            # ← Gọi self.check_login() không truyền tham số
            if not self.check_login():
                return {
                    'success': False,
                    'message': 'Chưa đăng nhập Facebook. Vui lòng đăng nhập trước.',
                }

            self.driver.get("https://www.facebook.com/groups/joins/?nav_source=tab")
            time.sleep(2)
            self.scroll_get_page()   # ← cuộn hết trang trước
            time.sleep(1)
            groups = self.get_page() # ← rồi mới lấy
            return {
                'success': True,
                'message': f'✓ Tìm thấy {len(groups)} groups',
                'groups': groups,
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Lỗi: {e}',
            }