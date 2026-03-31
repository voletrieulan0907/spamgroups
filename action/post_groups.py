"""
Post Groups Module - Đăng bài lên các nhóm Facebook
"""

import time
import os
import re
import json
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PostGroups:
    """Lớp xử lý việc đăng bài lên các nhóm Facebook."""

    def __init__(self, driver, data, log_callback=None, success_callback=None, fail_callback=None):
        self.driver   = driver
        self.data     = data
        self.profile  = data.get('profile', 'Unknown')
        self.groups   = data.get('groups', [])
        self.content  = data.get('content', '')
        self.media    = data.get('media', [])
        self.random_media = data.get('random_media', False)
        self.media_count  = data.get('media_count', 1)
        self.delay_min    = data.get('delay_min', 5)
        self.delay_max    = data.get('delay_max', 10)

        self.log_callback     = log_callback
        self.success_callback = success_callback
        self.fail_callback    = fail_callback

        self.success_count = 0
        self.fail_count    = 0

    # ─────────────────────────────────────────────────────────────
    #  LOGGING
    # ─────────────────────────────────────────────────────────────

    def _log(self, msg):
        print(msg, flush=True)
        if self.log_callback:
            self.log_callback(msg)

    def _ts(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def _get_media_path(self, media_item):
        """Lấy path từ media item (handle cả string và dict)"""
        if isinstance(media_item, dict):
            return media_item.get('path', '')
        return media_item

    # ─────────────────────────────────────────────────────────────
    #  SPIN CONTENT
    # ─────────────────────────────────────────────────────────────

    def _spin_content(self, text: str) -> str:
        normalized = re.sub(r'\s*\|\s*', ' | ', text)
        segments = self._split_by_pipe(normalized)

        if len(segments) > 1:
            chosen = random.choice(segments).strip()
            try:
                seg_num = segments.index(chosen) + 1
            except ValueError:
                seg_num = '?'
            self._log(f"[SPIN] 🎲 Chọn đoạn #{seg_num} / {len(segments)}")
        else:
            chosen = normalized.strip()

        def replacer(m):
            choices = m.group(1).split('|')
            return random.choice(choices).strip()

        return re.sub(r'\{([^}]+)\}', replacer, chosen)

    def _split_by_pipe(self, text: str) -> list:
        segments = []
        depth    = 0
        buf      = []
        i        = 0
        while i < len(text):
            c = text[i]
            if c == '{':
                depth += 1
                buf.append(c)
            elif c == '}':
                depth = max(0, depth - 1)
                buf.append(c)
            elif depth == 0 and text[i:i+3] == ' | ':
                segments.append(''.join(buf))
                buf = []
                i += 3
                continue
            else:
                buf.append(c)
            i += 1
        segments.append(''.join(buf))
        return [s for s in segments if s.strip()]

    # ─────────────────────────────────────────────────────────────
    #  UPLOAD HELPERS
    # ─────────────────────────────────────────────────────────────

    def _wait_upload_complete(self, timeout=60):
        self._log("[INFO] ⏳ Đang chờ upload hoàn tất...")
        time.sleep(2)
        start = time.time()
        while time.time() - start < timeout:
            try:
                still_loading = self.driver.execute_script("""
                    const pb = document.querySelector('[role="progressbar"]');
                    const ls = document.querySelector('[data-visualcompletion="loading-state"]');
                    const ul = document.querySelector(
                        '[aria-label*="uploading" i],[aria-label*="đang tải" i]'
                    );
                    const sp = document.querySelector('svg[aria-valuemax="100"]');
                    return !!(pb || ls || ul || sp);
                """)
                if not still_loading:
                    self._log("[OK] ✅ Upload hoàn tất")
                    return True
            except Exception:
                pass
            time.sleep(1.5)
        self._log("[WARN] ⚠ Timeout chờ upload")
        return False

    def _count_uploaded_previews(self) -> int:
        try:
            return self.driver.execute_script("""
                const dlg = document.querySelector('div[role="dialog"]');
                if (!dlg) return 0;
                const imgs = dlg.querySelectorAll(
                    'img[src*="blob:"], img[src*="scontent"], '
                    '[data-visualcompletion="media-vc-image"]'
                );
                return imgs.length;
            """)
        except Exception:
            return 0

    def _click_photo_button_in_dialog(self) -> bool:
        """
        FIX: Click nút Photo/Video trong dialog TRƯỚC khi upload.
        Facebook yêu cầu bước này để hiện input[type=file] đúng.
        """
        self._log("[INFO] 🖼 Click nút Photo/Video trong dialog...")
        try:
            clicked = self.driver.execute_script("""
                // Tìm dialog đang mở
                const dialogs = document.querySelectorAll('div[role="dialog"]');
                const dlg = dialogs[dialogs.length - 1];
                if (!dlg) return 'no_dialog';

                // Ưu tiên tìm label/button có chứa text ảnh/video
                const candidates = dlg.querySelectorAll(
                    'div[role="button"], button, label, [tabindex]'
                );
                const keywords = ['photo', 'video', 'ảnh', 'hình', 'image', 'media'];

                for (let el of candidates) {
                    const txt = (
                        (el.innerText || '') + ' ' +
                        (el.getAttribute('aria-label') || '') + ' ' +
                        (el.getAttribute('data-tooltip-content') || '')
                    ).toLowerCase();
                    for (let kw of keywords) {
                        if (txt.includes(kw)) {
                            el.click();
                            return 'clicked:' + txt.trim().slice(0, 40);
                        }
                    }
                }

                // Fallback: tìm SVG icon camera/image trong dialog
                const svgs = dlg.querySelectorAll('svg');
                for (let svg of svgs) {
                    const parent = svg.closest('div[role="button"], button, label');
                    if (parent) {
                        const label = parent.getAttribute('aria-label') || '';
                        if (/photo|video|ảnh|image/i.test(label)) {
                            parent.click();
                            return 'svg_clicked:' + label;
                        }
                    }
                }
                return 'not_found';
            """)
            self._log(f"[DEBUG] Click photo btn: {clicked}")
            time.sleep(1.5)

            # Kiểm tra xem input file có xuất hiện không
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            self._log(f"[DEBUG] File inputs sau click: {len(inputs)}")
            return len(inputs) > 0
        except Exception as e:
            self._log(f"[WARN] Click photo button lỗi: {e}")
            return False

    def _show_file_inputs(self):
        """Hiện tất cả input[type=file] ẩn trong trang."""
        self.driver.execute_script(
            "document.querySelectorAll('input[type=\"file\"]').forEach(function(i){"
            "i.style.display='block';"
            "i.style.visibility='visible';"
            "i.style.opacity='1';"
            "i.style.width='1px';"
            "i.style.height='1px';"
            "i.style.position='fixed';"
            "i.style.top='0';"
            "i.style.left='0';"
            "i.style.zIndex='99999';"
            "})"
        )
        time.sleep(0.4)

    def _get_best_file_input(self):
        """
        Lấy input[type=file] phù hợp nhất.
        Ưu tiên: có image/* VÀ có multiple → có image/* → bỏ qua video-only
        """
        self._show_file_inputs()
        inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        self._log(f"[DEBUG] Tổng file inputs: {len(inputs)}")

        best_multi  = None   # có image + multiple
        best_image  = None   # có image, không multiple
        best_any    = None   # fallback

        for idx, inp in enumerate(inputs):
            accept   = (inp.get_attribute("accept") or "").lower()
            multiple = inp.get_attribute("multiple")  # None nếu không có attr
            self._log(f"[DEBUG] Input[{idx}] accept='{accept[:80]}' multiple={multiple!r}")

            has_image = "image" in accept
            has_video = "video" in accept
            is_multi  = multiple is not None  # attr tồn tại = True

            # Bỏ qua input chỉ nhận video (không có image)
            if has_video and not has_image:
                self._log(f"[DEBUG] Bỏ input[{idx}] (video-only)")
                continue

            if has_image and is_multi and best_multi is None:
                best_multi = inp
                self._log(f"[DEBUG] Chọn input[{idx}] làm best_multi (image+multiple)")
            elif has_image and best_image is None:
                best_image = inp
                self._log(f"[DEBUG] Chọn input[{idx}] làm best_image")
            elif best_any is None:
                best_any = inp

        result = best_multi or best_image or best_any
        if result is None:
            self._log("[WARN] Không tìm được input phù hợp")
        return result

    def _upload_files(self, valid_paths: list) -> bool:
        if not valid_paths:
            return True

        # ── BƯỚC 1: Click nút Photo/Video ────────────────────────
        before_inputs = len(self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']"))
        self._click_photo_button_in_dialog()
        time.sleep(1)
        after_inputs = len(self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']"))
        self._log(f"[DEBUG] File inputs: {before_inputs} → {after_inputs}")

        # ── BƯỚC 2: Bật multiple trên tất cả input image ─────────
        try:
            self.driver.execute_script("""
                document.querySelectorAll('input[type="file"]').forEach(function(inp) {
                    const accept = (inp.getAttribute('accept') || '').toLowerCase();
                    // Chỉ bật multiple cho input có image (không phải video-only)
                    const hasImage = accept.includes('image');
                    const videoOnly = accept.includes('video') && !hasImage;
                    if (!videoOnly) {
                        inp.removeAttribute('multiple');
                        inp.setAttribute('multiple', '');
                    }
                });
            """)
            self._log("[DEBUG] Đã bật multiple cho các input image")
        except Exception as e:
            self._log(f"[WARN] Bật multiple lỗi: {e}")

        # ── BƯỚC 3: Gửi tất cả file cùng 1 lần ──────────────────
        inp = self._get_best_file_input()
        if inp is None:
            self._log("[WARN] Không tìm thấy file input phù hợp")
            return False

        # Kiểm tra lại multiple sau khi đã set
        has_multiple = self.driver.execute_script(
            "return arguments[0].hasAttribute('multiple');", inp
        )
        self._log(f"[DEBUG] Input multiple={has_multiple}, files={len(valid_paths)}")

        if has_multiple and len(valid_paths) > 1:
            # Gửi tất cả cùng lúc
            try:
                all_files = "\n".join(valid_paths)
                before_prev = self._count_uploaded_previews()
                inp.send_keys(all_files)
                wait_time = 2 + len(valid_paths) * 1.5
                time.sleep(wait_time)
                after_prev = self._count_uploaded_previews()
                self._log(f"[DEBUG] Preview sau gửi gộp: {before_prev} → {after_prev}")
                if after_prev > before_prev:
                    self._log(f"[OK] ✅ Upload gộp: {after_prev - before_prev} file")
                    self._wait_upload_complete(timeout=90)
                    return True
            except Exception as e:
                self._log(f"[WARN] Gửi gộp lỗi: {e}")

        # ── BƯỚC 4: Fallback — gửi từng file, mỗi lần click Photo lại ──
        self._log("[INFO] Fallback: gửi từng file, click Photo trước mỗi file...")
        success_count = 0
        for j, path in enumerate(valid_paths):
            try:
                if j > 0:
                    # Click thêm ảnh (nút + hoặc Add more trong dialog)
                    added = self.driver.execute_script("""
                        const dlg = document.querySelectorAll('div[role="dialog"]');
                        const d = dlg[dlg.length - 1];
                        if (!d) return 'no_dialog';
                        // Tìm nút thêm ảnh (dấu +, "Add photos", "Thêm ảnh")
                        const btns = d.querySelectorAll('div[role="button"], button, label');
                        for (let b of btns) {
                            const txt = (
                                (b.innerText||'') + ' ' + (b.getAttribute('aria-label')||'')
                            ).toLowerCase();
                            if (txt.includes('add') || txt.includes('thêm') ||
                                txt.includes('+') || txt.includes('photo')) {
                                b.click();
                                return 'add_btn: ' + txt.slice(0,30);
                            }
                        }
                        return 'no_add_btn';
                    """)
                    self._log(f"[DEBUG] Add more btn: {added}")
                    time.sleep(1)
                    # Bật lại multiple
                    self.driver.execute_script("""
                        document.querySelectorAll('input[type="file"]').forEach(function(i){
                            const a = (i.getAttribute('accept')||'').toLowerCase();
                            if (!( a.includes('video') && !a.includes('image') )) {
                                i.setAttribute('multiple','');
                            }
                        });
                    """)

                inp = self._get_best_file_input()
                if inp is None:
                    self._log(f"[WARN] Không có input cho file {j+1}")
                    continue

                b_prev = self._count_uploaded_previews()
                inp.send_keys(path)
                time.sleep(3)
                a_prev = self._count_uploaded_previews()

                if a_prev > b_prev:
                    success_count += 1
                    self._log(f"[OK] ✅ File {j+1}/{len(valid_paths)}: {os.path.basename(path)}")
                else:
                    self._log(f"[WARN] File {j+1} không nhận: {os.path.basename(path)}")
            except Exception as e:
                self._log(f"[WARN] File {j+1} lỗi: {e}")

        if success_count > 0:
            self._log(f"[OK] Fallback: {success_count}/{len(valid_paths)} file thành công")
            self._wait_upload_complete(timeout=90)
            return True

        self._log("[ERROR] ❌ Không upload được ảnh")
        return False

    # ─────────────────────────────────────────────────────────────
    #  GRAPHQL / URL CAPTURE
    # ─────────────────────────────────────────────────────────────

    def _find_post_url_in_json(self, obj, depth=0):
        if depth > 10:
            return None
        if isinstance(obj, dict):
            for key in ["url", "permalink_url", "link", "story_url"]:
                val = obj.get(key, "")
                if val and "facebook.com/groups/" in str(val) and "/posts/" in str(val):
                    return val
            for v in obj.values():
                r = self._find_post_url_in_json(v, depth + 1)
                if r:
                    return r
        elif isinstance(obj, list):
            for item in obj:
                r = self._find_post_url_in_json(item, depth + 1)
                if r:
                    return r
        return None

    def _capture_post_url(self, timeout=20):
        self._log("[INFO] Đang chờ graphql response...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                logs = self.driver.get_log("performance")
                for entry in logs:
                    try:
                        msg = json.loads(entry["message"])["message"]
                        if msg.get("method") != "Network.responseReceived":
                            continue
                        url = msg["params"]["response"]["url"]
                        if "graphql" not in url.lower():
                            continue
                        request_id = msg["params"]["requestId"]
                        try:
                            body_resp = self.driver.execute_cdp_cmd(
                                "Network.getResponseBody", {"requestId": request_id}
                            )
                            body_text = body_resp.get("body", "")
                            body_json = json.loads(body_text)
                            body_str  = json.dumps(body_json)

                            post_url = self._find_post_url_in_json(body_json.get("data", {}))
                            if post_url:
                                self._log(f"[SUCCESS] URL bài đăng: {post_url}")
                                return post_url

                            for match in re.findall(
                                r'https://www\.facebook\.com/groups/[^"\\]+/posts/\d+/?',
                                body_str
                            ):
                                clean = match.replace("\\", "").strip('"').rstrip("/") + "/"
                                self._log(f"[SUCCESS] URL bài đăng (regex): {clean}")
                                return clean
                        except Exception:
                            continue
                    except Exception:
                        continue
            except Exception as e:
                self._log(f"[ERROR] Lấy log thất bại: {e}")
                break
            time.sleep(1)

        try:
            cur = self.driver.current_url
            if "/groups/" in cur and "/posts/" in cur:
                self._log(f"[SUCCESS] URL bài đăng (browser): {cur}")
                return cur
        except Exception:
            pass

        self._log(f"[WARN] Không lấy được URL sau {timeout}s")
        return None

    # ─────────────────────────────────────────────────────────────
    #  CORE: MỞ DIALOG ĐĂNG BÀI
    # ─────────────────────────────────────────────────────────────

    def _open_post_dialog(self) -> bool:
        self._log("[INFO] 📝 Đang mở dialog đăng bài...")

        # Scroll lên đầu trước
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1.5)
        except Exception:
            pass

        # Cách 1: Tìm composer ở BẤT KỲ vị trí nào trên trang
        try:
            clicked = self.driver.execute_script("""
                // Ưu tiên 1: có pagelet GroupInlineComposer
                const composer = document.querySelector('[data-pagelet="GroupInlineComposer"]');
                if (composer) {
                    const btn = composer.querySelector(
                        'div[role="button"][tabindex="0"], div[role="textbox"], div[role="button"]'
                    );
                    if (btn) {
                        btn.scrollIntoView({behavior:'instant', block:'center'});
                        btn.click();
                        return 'pagelet_btn: ' + (btn.innerText||'').slice(0,40);
                    }
                }

                // Ưu tiên 2: tìm theo keyword TOÀN TRANG (không giới hạn vị trí)
                const keywords = [
                    'bạn viết gì đi', 'bạn đang nghĩ gì',
                    'write something', "what's on your mind",
                    'viết gì đó', 'đăng lên nhóm'
                ];
                const allEls = document.querySelectorAll(
                    'div[role="button"], div[role="textbox"], span[role="button"]'
                );
                for (let el of allEls) {
                    const txt = (
                        (el.innerText || '') + ' ' +
                        (el.getAttribute('aria-label') || '') + ' ' +
                        (el.getAttribute('placeholder') || '')
                    ).toLowerCase().trim();
                    for (let kw of keywords) {
                        if (txt.includes(kw)) {
                            el.scrollIntoView({behavior:'instant', block:'center'});
                            el.click();
                            return 'keyword_found: ' + txt.slice(0, 60);
                        }
                    }
                }
                return 'not_found';
            """)
            self._log(f"[DEBUG] Open dialog JS: {clicked}")
            if 'not_found' not in clicked:
                time.sleep(2)
                if self._is_dialog_open():
                    self._log("[OK] ✅ Dialog mở thành công (Cách 1)")
                    return True
        except Exception as e:
            self._log(f"[WARN] Cách 1 lỗi: {e}")

        # Cách 2: Scroll từng bước xuống để tìm composer (trường hợp lazy load)
        self._log("[INFO] Cách 2: Scroll tìm composer...")
        try:
            found = self.driver.execute_script("""
                return new Promise((resolve) => {
                    const keywords = [
                        'bạn viết gì đi', 'bạn đang nghĩ gì',
                        'write something', "what's on your mind"
                    ];

                    let scrollY = 0;
                    const maxScroll = 3000;
                    const step = 300;

                    const tryFind = () => {
                        // Tìm pagelet trước
                        const composer = document.querySelector('[data-pagelet="GroupInlineComposer"]');
                        if (composer) {
                            const btn = composer.querySelector('div[role="button"][tabindex="0"], div[role="textbox"]');
                            if (btn) {
                                btn.scrollIntoView({behavior:'instant', block:'center'});
                                btn.click();
                                resolve('scroll_pagelet: ' + (btn.innerText||'').slice(0,30));
                                return true;
                            }
                        }
                        // Tìm keyword
                        const els = document.querySelectorAll('div[role="button"], div[role="textbox"]');
                        for (let el of els) {
                            const txt = (
                                (el.innerText||'') + ' ' + (el.getAttribute('aria-label')||'')
                            ).toLowerCase();
                            for (let kw of keywords) {
                                if (txt.includes(kw)) {
                                    el.scrollIntoView({behavior:'instant', block:'center'});
                                    el.click();
                                    resolve('scroll_keyword: ' + txt.slice(0,40));
                                    return true;
                                }
                            }
                        }
                        return false;
                    };

                    // Thử ngay lập tức
                    if (tryFind()) return;

                    // Scroll dần và thử
                    const interval = setInterval(() => {
                        scrollY += step;
                        window.scrollTo(0, scrollY);
                        if (tryFind() || scrollY >= maxScroll) {
                            clearInterval(interval);
                            if (scrollY >= maxScroll) resolve('scroll_exhausted');
                        }
                    }, 300);
                });
            """)
            self._log(f"[DEBUG] Scroll find: {found}")
            time.sleep(2)
            if self._is_dialog_open():
                self._log("[OK] ✅ Dialog mở sau scroll")
                return True
        except Exception as e:
            self._log(f"[WARN] Cách 2 lỗi: {e}")

        # Cách 3: XPath không giới hạn vị trí
        self._log("[INFO] Cách 3: XPath toàn trang...")
        xpaths = [
            "//div[@data-pagelet='GroupInlineComposer']//div[@role='button'][@tabindex='0']",
            "//div[@data-pagelet='GroupInlineComposer']//div[@role='textbox']",
            "//div[@data-pagelet='GroupInlineComposer']//div[@role='button']",
            "//span[contains(text(),'Bạn viết gì đi')]/ancestor::div[@role='button']",
            "//span[contains(text(),'Bạn đang nghĩ')]/ancestor::div[@role='button']",
            "//div[@role='textbox'][contains(@aria-label,'Bạn')]",
            "//div[@role='textbox'][contains(@aria-label,'Write')]",
        ]
        for xp in xpaths:
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xp))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el
                )
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", el)
                time.sleep(2)
                if self._is_dialog_open():
                    self._log(f"[OK] ✅ Dialog mở bằng XPath: {xp[:70]}")
                    return True
            except Exception:
                pass

        self._log("[ERROR] ❌ Không mở được dialog đăng bài")
        return False


    def _is_dialog_open(self) -> bool:
        """Kiểm tra xem dialog đăng bài đã mở chưa."""
        try:
            result = self.driver.execute_script("""
                const dlg = document.querySelector('div[role="dialog"]');
                if (!dlg) return false;
                const tb = dlg.querySelector('div[role="textbox"]');
                return !!tb;
            """)
            return bool(result)
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────
    #  CORE: NHẬP NỘI DUNG + UPLOAD + ĐĂNG BÀI
    # ─────────────────────────────────────────────────────────────

    def _click_post_button(self) -> bool:
        """
        FIX: Click nút đăng bài bằng nhiều cách fallback.
        """
        self._log("[INFO] 🖊 Click nút đăng bài...")

        # Cách 1: JS tìm nút trong dialog
        try:
            result = self.driver.execute_script("""
                // Tìm tất cả dialog, lấy cái cuối
                const dialogs = document.querySelectorAll('div[role="dialog"]');
                const dlg = dialogs[dialogs.length - 1];
                if (!dlg) return 'no_dialog';

                // Tìm nút Post/Đăng
                const btns = dlg.querySelectorAll('div[role="button"], button');
                for (let btn of btns) {
                    const txt = (btn.innerText || '').trim().toLowerCase();
                    const lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
                    if (txt === 'post' || txt === 'đăng' ||
                        lbl === 'post' || lbl === 'đăng') {
                        // Kiểm tra không bị disabled
                        if (!btn.getAttribute('aria-disabled') &&
                            !btn.classList.contains('disabled') &&
                            btn.getAttribute('aria-disabled') !== 'true') {
                            btn.click();
                            return 'clicked:' + (txt || lbl);
                        }
                    }
                }
                // Fallback: tìm nút submit cuối cùng trong dialog
                const allBtns = [...dlg.querySelectorAll('div[role="button"]')];
                // Nút Post thường là nút cuối và có màu xanh (background không phải transparent)
                for (let i = allBtns.length - 1; i >= 0; i--) {
                    const b = allBtns[i];
                    const style = window.getComputedStyle(b);
                    const bg = style.backgroundColor;
                    // Facebook dùng màu xanh #0866FF hoặc tương tự
                    if (bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)') {
                        const txt = (b.innerText || '').trim();
                        if (txt && txt.length < 20) {
                            b.click();
                            return 'fallback_last_btn:' + txt;
                        }
                    }
                }
                return 'not_found';
            """)
            self._log(f"[DEBUG] Click Post JS: {result}")
            if 'clicked' in result or 'fallback' in result:
                return True
        except Exception as e:
            self._log(f"[WARN] Click Post JS lỗi: {e}")

        # Cách 2: XPath linh hoạt
        xpaths = [
            "//div[@role='dialog']//div[@role='button' and @aria-label='Post']",
            "//div[@role='dialog']//div[@role='button' and @aria-label='Đăng']",
            "//div[@role='dialog']//div[@role='button' and normalize-space()='Post']",
            "//div[@role='dialog']//div[@role='button' and normalize-space()='Đăng']",
            "//div[@role='dialog']//button[normalize-space()='Post']",
            "//div[@role='dialog']//button[normalize-space()='Đăng']",
        ]
        for xp in xpaths:
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                self._log(f"[OK] Click Post XPath: {xp[:60]}")
                return True
            except Exception:
                pass

        # Cách 3: Keyboard shortcut Ctrl+Enter
        try:
            self._log("[WARN] Thử Ctrl+Enter...")
            from selenium.webdriver.common.keys import Keys
            textarea = self.driver.find_element(
                By.XPATH, "//div[@role='dialog']//div[@role='textbox']")
            textarea.send_keys(Keys.CONTROL + Keys.RETURN)
            return True
        except Exception as e:
            self._log(f"[WARN] Ctrl+Enter lỗi: {e}")

        self._log("[ERROR] ❌ Không click được nút đăng")
        return False

    def input_content(self, content, media_paths):
        if isinstance(media_paths, str):
            media_paths = [media_paths]
        media_paths = media_paths or []

        valid_paths = []
        for p in media_paths:
            normalized = str(Path(p).resolve())
            if os.path.isfile(normalized):
                valid_paths.append(normalized)
                self._log(f"[OK] File hợp lệ: {normalized}")
            else:
                self._log(f"[WARN] File không tồn tại: {normalized}")

        # ── Bước 1: Mở dialog ────────────────────────────────────
        if not self._open_post_dialog():
            self._log("[ERROR] ❌ Không mở được dialog, bỏ qua nhóm này")
            return None

        # ── Bước 2: Nhập text ─────────────────────────────────────
        try:
            textarea = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@role='dialog']//div[@role='textbox' and "
                    "not(contains(@aria-label,'comment'))]"
                ))
            )
            self.driver.execute_script("arguments[0].click();", textarea)
            time.sleep(0.5)
            textarea.send_keys(content)
            self._log("[OK] Đã nhập nội dung")
        except Exception as e:
            self._log(f"[WARN] Thử nhập text qua ActionChains: {e}")
            try:
                self.driver.execute_script("""
                    const dlg = document.querySelector('div[role="dialog"]');
                    if (!dlg) return;
                    const boxes = dlg.querySelectorAll('div[role="textbox"]');
                    for (let b of boxes) {
                        const lbl = (b.getAttribute('aria-label') || '').toLowerCase();
                        if (!lbl.includes('comment')) { b.focus(); break; }
                    }
                """)
                time.sleep(0.5)
                ActionChains(self.driver).send_keys(content).perform()
                self._log("[OK] Đã nhập nội dung qua ActionChains")
            except Exception as e2:
                self._log(f"[ERROR] Không nhập được text: {e2}")

        # ── Bước 3: Upload ảnh ─────────────────────────────────────
        if valid_paths:
            self._upload_files(valid_paths)

        time.sleep(1)

        # ── Bước 4: Click Post ────────────────────────────────────
        self._click_post_button()

        self._log("[INFO] Đã click đăng bài, chờ response...")
        post_url = self._capture_post_url(timeout=20)
        if post_url:
            self._log(f"[RESULT] {post_url}")
        return post_url

    # ─────────────────────────────────────────────────────────────
    #  POST TO GROUP
    # ─────────────────────────────────────────────────────────────

    def post_to_group(self, group):
        group_name = group.get('name', group.get('url', '?'))
        try:
            self._log(f"\n[INFO] Đang đăng vào '{group_name}'...")
            self.driver.get(group['url'])
            time.sleep(3)

            # ── Chọn ảnh ──────────────────────────────────────────
            if self.media:
                if self.random_media:
                    count = min(self.media_count, len(self.media))
                    selected_media = random.sample(self.media, count)
                    media_names = [os.path.basename(self._get_media_path(m)) for m in selected_media]
                    self._log(f"[INFO] 🎲 Random {count}/{len(self.media)} ảnh: {media_names}")
                else:
                    count = min(self.media_count, len(self.media))
                    selected_media = self.media[:count]
                    media_names = [os.path.basename(self._get_media_path(m)) for m in selected_media]
                    self._log(f"[INFO] 📎 Tuần tự {count} ảnh: {media_names}")
            else:
                selected_media = []

            # ── Spin content ──────────────────────────────────────
            content = self._spin_content(self.content)
            preview = content[:80] + ('...' if len(content) > 80 else '')
            self._log(f"[INFO] 📝 Nội dung: {preview}")

            # Lấy path từ selected_media
            media_paths = [self._get_media_path(m) for m in selected_media] if selected_media else []
            post_url = self.input_content(content, media_paths)

            if post_url:
                self.success_count += 1
                self._log(f"[SUCCESS] ✅ '{group_name}' → {post_url}")
                if self.success_callback:
                    self.success_callback(self._ts(), group_name, post_url)
            else:
                self.fail_count += 1
                err = "Đăng xong nhưng không lấy được URL"
                self._log(f"[WARN] {err} — '{group_name}'")
                if self.fail_callback:
                    self.fail_callback(self._ts(), group_name, err)

        except Exception as e:
            self.fail_count += 1
            self._log(f"[ERROR] ❌ Lỗi '{group_name}': {e}")
            if self.fail_callback:
                self.fail_callback(self._ts(), group_name, str(e))

    # ─────────────────────────────────────────────────────────────
    #  MAIN LOOP
    # ─────────────────────────────────────────────────────────────

    def main_post(self):
        total = len(self.groups)
        self._log(f"[INFO] 🚀 Bắt đầu đăng {total} nhóm | "
                  f"Delay: {self.delay_min}~{self.delay_max}s")

        for idx, group in enumerate(self.groups, 1):
            self._log(f"\n[INFO] ═══ Nhóm {idx}/{total}: {group.get('name', '')} ═══")
            try:
                self.post_to_group(group)
            except Exception as e:
                self._log(f"[ERROR] {e}")
                self.fail_count += 1

            if idx < total:
                delay = random.randint(self.delay_min, self.delay_max)
                next_name = self.groups[idx].get('name', '')
                self._log(
                    f"[INFO] ⏳ Chờ {delay}s trước nhóm tiếp theo "
                    f"({idx + 1}/{total}: {next_name})..."
                )
                elapsed = 0
                while elapsed < delay:
                    step = min(5, delay - elapsed)
                    time.sleep(step)
                    elapsed += step
                    remaining = delay - elapsed
                    if remaining > 0:
                        self._log(f"[INFO] ⏱ Còn {remaining}s...")

        self._log(
            f"\n[DONE] ✅ Thành công: {self.success_count} | "
            f"❌ Lỗi: {self.fail_count} / {total}"
        )