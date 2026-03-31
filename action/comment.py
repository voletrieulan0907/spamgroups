"""
Comment Groups Module - Bình luận trên các bài viết trong nhóm Facebook
"""

import time
import json
import re
import os
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CommentGroups:
    """Lớp xử lý việc bình luận trên các bài viết trong nhóm Facebook."""

    def __init__(self, driver, data, log_callback=None, success_callback=None, fail_callback=None):
        self.driver   = driver
        self.data     = data
        self.profile  = data.get('profile', 'Unknown')
        self.groups   = data.get('groups', [])
        self.content  = data.get('content', '')
        self.media    = data.get('media', [])
        self.random_media = data.get('random_media', False)
        self.media_count  = data.get('media_count', 1)
        self.cmt_count    = data.get('cmt_count', 3)
        self.delay_min    = data.get('delay_min', 30)
        self.delay_max    = data.get('delay_max', 60)

        self.log_callback     = log_callback
        self.success_callback = success_callback
        self.fail_callback    = fail_callback

        self.success_count = 0
        self.fail_count    = 0

    # ─────────────────────────────────────────────────────────────
    #  LOGGING
    # ─────────────────────────────────────────────────────────────

    def _log(self, msg):
        """In log thông tin"""
        print(msg, flush=True)
        if self.log_callback:
            self.log_callback(msg)

    def _ts(self):
        """Lấy timestamp"""
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
        """Spin nội dung từ template | và {}"""
        normalized = re.sub(r'\s*\|\s*', ' | ', text)
        segments = self._split_by_pipe(normalized)

        if len(segments) > 1:
            chosen = random.choice(segments).strip()
            try:
                seg_num = segments.index(chosen) + 1
            except ValueError:
                seg_num = "?"
            self._log(f"[SPIN] 🎲 Chọn đoạn #{seg_num} / {len(segments)}")
        else:
            chosen = normalized.strip()

        def replacer(m):
            choices = m.group(1).split('|')
            return random.choice(choices).strip()

        return re.sub(r'\{([^}]+)\}', replacer, chosen)

    def _split_by_pipe(self, text: str) -> list:
        """Split text by | nhưng không split trong {}"""
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
                depth -= 1
                buf.append(c)
            elif depth == 0 and text[i:i+3] == ' | ':
                segments.append(''.join(buf))
                buf = []
                i += 2
            else:
                buf.append(c)
            i += 1
        segments.append(''.join(buf))
        return [s for s in segments if s.strip()]

    # ─────────────────────────────────────────────────────────────
    #  UPLOAD HELPERS
    # ─────────────────────────────────────────────────────────────

    def _wait_upload_complete(self, timeout=60):
        """Chờ upload ảnh hoàn tất"""
        self._log("[INFO] ⏳ Đang chờ upload hoàn tất...")
        time.sleep(2)
        start = time.time()
        while time.time() - start < timeout:
            try:
                count = self.driver.execute_script("""
                    const cmtBox = document.querySelector('div[role="complementary"] div[data-pagelet="CommentsCOMWrapper"]')
                        || document.querySelector('div[contenteditable="true"]')?.closest('div[role="region"]');
                    if (!cmtBox) return 0;
                    const imgs = cmtBox.querySelectorAll(
                        'img[src*="blob:"], img[src*="scontent"], [data-visualcompletion="media-vc-image"]'
                    );
                    return imgs.length;
                """)
                if count > 0:
                    self._log(f"[INFO] ✅ Upload thành công, tìm thấy {count} ảnh")
                    return True
            except Exception:
                pass
            time.sleep(1.5)
        self._log("[WARN] ⚠ Timeout chờ upload")
        return False

    def _show_file_inputs(self):
        """Hiện tất cả input[type=file] ẩn trong trang"""
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

    def _close_post_dialog(self):
        """Đóng dialog tạo bài viết nếu đang mở"""
        try:
            closed = self.driver.execute_script("""
                const dialogs = document.querySelectorAll('div[role="dialog"]');
                let closedCount = 0;
                dialogs.forEach(d => {
                    const closeBtn = d.querySelector(
                        'div[aria-label="Đóng"], div[aria-label="Close"], ' +
                        'div[aria-label*="óng"], div[aria-label*="lose"]'
                    );
                    if (closeBtn) {
                        closeBtn.click();
                        closedCount++;
                    }
                });
                return closedCount;
            """)
            if closed:
                self._log(f"[INFO] Đã đóng {closed} dialog")
                time.sleep(0.8)
        except Exception:
            pass

    def _click_photo_btn_in_comment(self) -> bool:
        """
        Click nút đính kèm ảnh TRONG comment section.
        Đây là bước quan trọng để Facebook tạo đúng file input cho comment,
        tránh upload nhầm vào dialog 'Tạo bài viết'.
        """
        self._log("[INFO] 🖼️ Tìm nút ảnh trong comment section...")

        clicked = self.driver.execute_script("""
            // Xác định comment box đang active
            const allBoxes = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
            let cmtBox = null;

            // Ưu tiên pagelet Comment
            const cmtPagelets = document.querySelectorAll(
                '[data-pagelet*="Comment"], [data-pagelet*="comment"]'
            );
            for (let p of cmtPagelets) {
                const box = p.querySelector('div[contenteditable="true"]');
                if (box) { cmtBox = box; break; }
            }

            // Tìm theo placeholder
            if (!cmtBox) {
                for (let box of allBoxes) {
                    const ph   = (box.getAttribute('data-placeholder') || '').toLowerCase();
                    const aria = (box.getAttribute('aria-label') || '').toLowerCase();
                    if (ph.includes('nghĩ gì') || ph.includes('what') ||
                        aria.includes('tạo bài') || aria.includes('create post')) continue;
                    if (ph.includes('bình luận') || ph.includes('comment') ||
                        aria.includes('bình luận') || aria.includes('comment') ||
                        ph.includes('trả lời')) {
                        cmtBox = box;
                        break;
                    }
                }
            }

            // Fallback: lấy cái cuối cùng
            if (!cmtBox && allBoxes.length >= 2) {
                cmtBox = allBoxes[allBoxes.length - 1];
            }
            if (!cmtBox) return {found: false, reason: 'no_cmt_box'};

            // Leo lên cây DOM từ comment box để tìm nút ảnh
            let container = cmtBox.parentElement;
            for (let level = 0; level < 10; level++) {
                if (!container) break;

                const btns = container.querySelectorAll(
                    'div[role="button"], button, span[role="button"]'
                );
                for (let btn of btns) {
                    // Bỏ qua nút nằm trong dialog tạo bài viết
                    if (btn.closest('div[role="dialog"]')) continue;

                    const aria = (btn.getAttribute('aria-label') || '').toLowerCase();

                    // Match theo aria-label rõ ràng
                    if (aria.includes('ảnh') || aria.includes('photo') ||
                        aria.includes('hình') || aria.includes('image') ||
                        aria.includes('attach')) {
                        // Loại trừ emoji, sticker, gif
                        if (aria.includes('emoji') || aria.includes('sticker') ||
                            aria.includes('gif') || aria.includes('cảm xúc') ||
                            aria.includes('biểu tượng')) continue;

                        btn.click();
                        return {found: true, via: 'aria_label', aria: aria, level: level};
                    }
                }

                container = container.parentElement;
            }

            return {found: false, reason: 'no_photo_btn'};
        """)

        if clicked and clicked.get('found'):
            self._log(f"[OK] Đã click nút ảnh trong comment: via={clicked.get('via')} aria='{clicked.get('aria','')}' level={clicked.get('level')}")
            time.sleep(1.5)
            return True

        self._log(f"[WARN] Không tìm nút ảnh comment: {clicked}")
        return False

    def _get_best_file_input(self):
        """
        Lấy file input KHÔNG nằm trong dialog tạo bài viết.
        Phải gọi _click_photo_btn_in_comment() trước để Facebook
        kích hoạt đúng file input cho comment section.
        """
        self._show_file_inputs()

        inp = self.driver.execute_script("""
            const allInputs = Array.from(document.querySelectorAll('input[type="file"]'));

            // Ưu tiên 1: input trong comment pagelet
            const cmtPagelets = document.querySelectorAll(
                '[data-pagelet*="Comment"], [data-pagelet*="comment"]'
            );
            for (let p of cmtPagelets) {
                const inputs = p.querySelectorAll('input[type="file"]');
                for (let inp of inputs) {
                    inp.style.cssText = 'display:block!important;visibility:visible!important;' +
                        'opacity:1!important;position:fixed!important;top:0;left:0;' +
                        'width:1px;height:1px;z-index:99999;';
                    return inp;
                }
            }

            // Ưu tiên 2: input KHÔNG nằm trong role=dialog
            for (let inp of allInputs) {
                if (inp.closest('div[role="dialog"]')) continue;
                const accept = (inp.getAttribute('accept') || '').toLowerCase();
                if (!accept || accept.includes('image') || !accept.includes('video')) {
                    inp.style.cssText = 'display:block!important;visibility:visible!important;' +
                        'opacity:1!important;position:fixed!important;top:0;left:0;' +
                        'width:1px;height:1px;z-index:99999;';
                    return inp;
                }
            }

            return null;
        """)

        if inp is None:
            self._log("[WARN] Không tìm được file input ngoài dialog")
        else:
            self._log("[OK] Tìm được file input ngoài dialog")
        return inp

    def _upload_files(self, valid_paths: list) -> bool:
        """
        Upload ảnh vào comment theo đúng flow:
        1. Đóng dialog tạo bài viết nếu có
        2. Click nút ảnh TRONG comment section
        3. Lấy file input vừa được kích hoạt (không phải của dialog)
        4. Send keys path file
        """
        if not valid_paths:
            return True

        valid_paths = valid_paths[:self.media_count]
        self._log(f"[INFO] 📸 Upload {len(valid_paths)} ảnh vào comment...")

        # BƯỚC 1: Đóng dialog tạo bài viết nếu đang mở
        self._close_post_dialog()

        # BƯỚC 2: Click nút ảnh TRONG comment section
        # (để Facebook tạo/kích hoạt đúng file input cho comment)
        clicked = self._click_photo_btn_in_comment()
        if not clicked:
            self._log("[WARN] Không click được nút ảnh comment, thử tìm file input trực tiếp...")

        time.sleep(1)

        # BƯỚC 3: Lấy file input (bây giờ phải là của comment, không phải dialog)
        inp = self._get_best_file_input()
        if inp is None:
            self._log("[ERROR] Không tìm thấy file input phù hợp")
            return False

        # BƯỚC 4: Bật multiple nếu upload nhiều ảnh
        if len(valid_paths) > 1:
            try:
                self.driver.execute_script("arguments[0].setAttribute('multiple', '');", inp)
            except Exception:
                pass

        # BƯỚC 5: Send keys file paths
        try:
            inp.send_keys('\n'.join(valid_paths))
            self._log(f"[OK] Gửi {len(valid_paths)} file")
            self._wait_upload_complete(timeout=90)
            return True
        except Exception as e:
            self._log(f"[ERROR] Upload lỗi: {e}")
            return False

    # ─────────────────────────────────────────────────────────────
    #  COMMENT OPERATIONS
    # ─────────────────────────────────────────────────────────────

    def _get_post_links(self, group_url: str, max_scroll=5) -> list:
        """Lấy danh sách link bài viết trong nhóm bằng JS + XPath"""
        self.driver.get(group_url)
        time.sleep(2)

        self._log("[INFO] 📜 Đang scroll để lấy bài viết...")
        post_links = set()

        for scroll_i in range(max_scroll):
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1.5)

            # ── CÁCH 1: JavaScript ──
            links_from_js = self.driver.execute_script("""
                const links = new Set();

                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && href.includes('/groups/') && href.includes('/posts/')) {
                        const clean = href.split('?')[0].split('#')[0];
                        if (clean && !clean.includes('comment_id')) {
                            links.add(clean);
                        }
                    }
                });

                document.querySelectorAll('[data-pagelet*="Feed"], [role="article"]').forEach(container => {
                    const link = container.querySelector('a[href*="/posts/"]');
                    if (link) {
                        let href = link.getAttribute('href');
                        if (href) {
                            const clean = href.split('?')[0].split('#')[0];
                            if (clean && !clean.includes('comment_id')) {
                                links.add(clean);
                            }
                        }
                    }
                });

                return Array.from(links);
            """)

            if links_from_js:
                self._log(f"[DEBUG] JS tìm thấy {len(links_from_js)} links ở lần scroll {scroll_i + 1}")
                for link in links_from_js:
                    post_links.add(link)

            # ── CÁCH 2: XPath fallback ──
            try:
                xpath_links = self.driver.find_elements(By.XPATH,
                    '//a[contains(@href, "/groups/") and contains(@href, "/posts/")]')
                self._log(f"[DEBUG] XPath tìm thấy {len(xpath_links)} a tags")

                for link in xpath_links:
                    try:
                        href = link.get_attribute("href")
                        if href and "/posts/" in href and "comment_id" not in href:
                            clean = re.sub(r'\?.*', '', href)
                            post_links.add(clean)
                    except Exception:
                        pass
            except Exception as e:
                self._log(f"[DEBUG] XPath error: {e}")

        result = list(post_links)[:self.cmt_count]

        if len(result) == 0:
            self._log(f"[WARN] ⚠️  Không tìm được bài viết từ {len(post_links)} links")
            if post_links:
                self._log(f"[DEBUG] Tất cả links tìm được: {list(post_links)[:3]}")
        else:
            self._log(f"[INFO] ✅ Tìm thấy {len(result)} bài viết từ {len(post_links)} links")

        return result

    def _find_comment_box(self) -> bool:
        """Tìm và click vào comment box - KHÔNG nhầm với ô tạo bài viết"""
        self._log("[INFO] 🔍 Tìm comment box...")

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1.5)

        found = self.driver.execute_script("""
            // Ưu tiên tìm trong data-pagelet chứa "Comment"
            const cmtPagelets = document.querySelectorAll(
                '[data-pagelet*="Comment"], [data-pagelet*="comment"]'
            );
            for (let pagelet of cmtPagelets) {
                const box = pagelet.querySelector('div[contenteditable="true"]');
                if (box) {
                    box.scrollIntoView({behavior: 'smooth', block: 'center'});
                    box.click();
                    return {type: 'pagelet_comment', found: true};
                }
            }

            // Tìm theo aria-label hoặc placeholder rõ ràng là comment
            const allEditable = document.querySelectorAll('div[contenteditable="true"]');
            for (let box of allEditable) {
                const ph = (box.getAttribute('data-placeholder') || '').toLowerCase();
                const ariaLabel = (box.getAttribute('aria-label') || '').toLowerCase();

                if (ph.includes('nghĩ gì') || ph.includes('what') ||
                    ariaLabel.includes('tạo bài') || ariaLabel.includes('create post')) {
                    continue;
                }

                if (ph.includes('bình luận') || ph.includes('comment') ||
                    ph.includes('viết bình') || ph.includes('trả lời') ||
                    ariaLabel.includes('bình luận') || ariaLabel.includes('comment')) {
                    box.scrollIntoView({behavior: 'smooth', block: 'center'});
                    box.click();
                    return {type: 'placeholder_match', found: true, ph: ph};
                }
            }

            // Fallback: lấy editable CUỐI CÙNG (comment thường ở dưới)
            const boxes = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
            if (boxes.length >= 2) {
                const target = boxes[boxes.length - 1];
                target.scrollIntoView({behavior: 'smooth', block: 'center'});
                target.click();
                return {type: 'last_editable', found: true, total: boxes.length};
            } else if (boxes.length === 1) {
                boxes[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                boxes[0].click();
                return {type: 'only_one', found: true};
            }

            return {type: 'not_found', found: false};
        """)

        if found and found.get('found'):
            self._log(f"[OK] Tìm thấy comment box: {found['type']} | ph='{found.get('ph','')}'")
            time.sleep(1)
            return True

        self._log("[WARN] Không tìm được comment box")
        return False

    def _input_comment(self, text: str, media_paths: list) -> bool:
        """Nhập text và upload ảnh vào comment - tránh nhầm ô tạo bài viết"""
        try:
            target_box = self.driver.execute_script("""
                // Ưu tiên tìm trong pagelet Comment
                const cmtPagelets = document.querySelectorAll(
                    '[data-pagelet*="Comment"], [data-pagelet*="comment"]'
                );
                for (let pagelet of cmtPagelets) {
                    const box = pagelet.querySelector('div[contenteditable="true"]');
                    if (box) return box;
                }

                // Lọc theo placeholder
                const allBoxes = document.querySelectorAll('div[contenteditable="true"]');
                for (let box of allBoxes) {
                    const ph = (box.getAttribute('data-placeholder') || '').toLowerCase();
                    const aria = (box.getAttribute('aria-label') || '').toLowerCase();
                    if (ph.includes('nghĩ gì') || ph.includes('what') ||
                        aria.includes('tạo bài') || aria.includes('create post')) {
                        continue;
                    }
                    if (ph.includes('bình luận') || ph.includes('comment') ||
                        aria.includes('bình luận') || aria.includes('comment')) {
                        return box;
                    }
                }

                // Fallback: lấy cái cuối cùng
                const boxes = Array.from(allBoxes);
                return boxes.length >= 2 ? boxes[boxes.length - 1] : (boxes[0] || null);
            """)

            if not target_box:
                self._log("[ERROR] Không tìm thấy comment box để nhập")
                return False

            target_box.click()
            time.sleep(0.5)
            target_box.send_keys(text)
            self._log(f"[OK] Đã nhập: {text[:50]}...")

            # Upload ảnh nếu có
            if media_paths:
                time.sleep(1)
                if not self._upload_files(media_paths):
                    self._log("[WARN] Upload ảnh thất bại, vẫn tiếp tục gửi comment")

            return True

        except Exception as e:
            self._log(f"[ERROR] Nhập comment lỗi: {e}")
            return False

    def _post_comment(self) -> bool:
        """Click nút gửi comment bằng JS"""
        self._log("[INFO] 📤 Click gửi comment...")

        try:
            posted = self.driver.execute_script("""
                // Tìm comment box đúng (không phải ô tạo bài)
                let cmtBox = null;
                const cmtPagelets = document.querySelectorAll(
                    '[data-pagelet*="Comment"], [data-pagelet*="comment"]'
                );
                for (let p of cmtPagelets) {
                    const box = p.querySelector('div[contenteditable="true"]');
                    if (box) { cmtBox = box; break; }
                }
                if (!cmtBox) {
                    const allBoxes = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
                    cmtBox = allBoxes.length >= 2
                        ? allBoxes[allBoxes.length - 1]
                        : (allBoxes[0] || null);
                }
                if (!cmtBox) return {type: 'no_box', found: false};

                // Tìm parent form/container
                let form = cmtBox.closest('form');
                if (!form) form = cmtBox.closest('div[role="region"]');
                if (!form) form = cmtBox.parentElement?.parentElement?.parentElement;
                if (!form) return {type: 'no_form', found: false};

                // Tìm nút gửi
                const buttons = form.querySelectorAll('button, div[role="button"]');
                for (let btn of buttons) {
                    const text = (btn.innerText || '').toLowerCase();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();

                    if (text.includes('post') || text.includes('reply') || text.includes('comment') ||
                        text.includes('gửi') || text.includes('trả lời') ||
                        ariaLabel.includes('post') || ariaLabel.includes('reply') ||
                        ariaLabel.includes('gửi') || ariaLabel.includes('bình luận')) {

                        const isEnabled = !btn.disabled && !btn.classList.contains('disabled');
                        if (isEnabled) {
                            btn.click();
                            return {type: 'button', found: true, text: text.slice(0, 20)};
                        }
                    }
                }

                return {type: 'not_found', found: false};
            """)

            if posted and posted.get('found'):
                self._log(f"[OK] 📬 Gửi comment thành công: {posted['type']}")
                time.sleep(3)
                return True

            self._log(f"[WARN] Không tìm được nút gửi: {posted}")
            return False

        except Exception as e:
            self._log(f"[ERROR] Click gửi comment lỗi: {e}")
            return False

    def _comment_to_post(self, post_url: str) -> bool:
        """Bình luận một bài viết"""
        try:
            self.driver.get(post_url)
            time.sleep(2)

            # Chọn media
            if self.random_media:
                count = min(self.media_count, len(self.media))
                selected_media = random.sample(self.media, count) if count > 0 else []
                media_names = [os.path.basename(self._get_media_path(m)) for m in selected_media]
                self._log(f"[INFO] 🎲 Random {count}/{len(self.media)} ảnh: {media_names}")
            else:
                count = min(self.media_count, len(self.media))
                selected_media = self.media[:count]
                media_names = [os.path.basename(self._get_media_path(m)) for m in selected_media]
                self._log(f"[INFO] 📎 Tuần tự {count} ảnh: {media_names}")

            media_paths = [self._get_media_path(m) for m in selected_media] if selected_media else []

            # Spin content
            spin_text = self._spin_content(self.content)

            # Tìm comment box
            if not self._find_comment_box():
                return False

            # Nhập và upload
            if not self._input_comment(spin_text, media_paths):
                return False

            # Gửi
            if not self._post_comment():
                return False

            self._log(f"[SUCCESS] ✅ Bình luận thành công: {post_url}")
            return True

        except Exception as e:
            self._log(f"[ERROR] Bình luận lỗi: {e}")
            return False

    # ─────────────────────────────────────────────────────────────
    #  MAIN EXECUTION
    # ─────────────────────────────────────────────────────────────

    def main_comment(self):
        """Thực thi bình luận tất cả nhóm"""
        ts = self._ts()
        self._log(
            f"\n[{ts}] 🚀 Bắt đầu comment {len(self.groups)} nhóm | "
            f"{self.cmt_count} bài/nhóm | Delay: {self.delay_min}~{self.delay_max}s"
        )

        for idx, group in enumerate(self.groups, 1):
            group_name = group.get('name', group.get('url', '?'))
            group_url = group.get('url', '')

            if not group_url:
                self._log(f"[SKIP] [{idx}/{len(self.groups)}] Nhóm không có URL")
                continue

            try:
                self._log(f"\n[{self._ts()}] 📌 Nhóm {idx}/{len(self.groups)}: {group_name}")

                post_links = self._get_post_links(group_url, max_scroll=3)
                if not post_links:
                    self._log("[SKIP] Không tìm được bài viết")
                    self.fail_count += 1
                    continue

                for post_idx, post_url in enumerate(post_links, 1):
                    self._log(f"\n  [{post_idx}/{len(post_links)}] Bài: {post_url}")

                    if self._comment_to_post(post_url):
                        self.success_count += 1
                    else:
                        self.fail_count += 1

                    if post_idx < len(post_links):
                        delay = random.randint(self.delay_min, self.delay_max)
                        self._log(f"⏰ Chờ {delay}s trước bài tiếp theo...")
                        time.sleep(delay)

            except Exception as e:
                self._log(f"[ERROR] Lỗi nhóm {group_name}: {e}")
                self.fail_count += 1
                continue

            if idx < len(self.groups):
                delay = random.randint(self.delay_min * 2, self.delay_max * 2)
                self._log(f"⏰ Chờ {delay}s trước nhóm tiếp theo...")
                time.sleep(delay)

        ts_end = self._ts()
        self._log(
            f"\n[{ts_end}] ✅ Thành công: {self.success_count} | "
            f"❌ Lỗi: {self.fail_count} / {len(self.groups) * self.cmt_count}"
        )

    def execute(self):
        """Entry point - in bước khởi đầu và thực thi comment"""
        ts = self._ts()
        print(f"\n\n{'='*70}", flush=True)
        print(f"[{ts}] ✨ BẮT ĐẦU COMMENT GROUPS", flush=True)
        print(f"{'='*70}\n", flush=True)

        print_data = {
            'profile': self.profile,
            'groups': len(self.groups),
            'cmt_count_per_group': self.cmt_count,
            'content': self.content[:80] + '...' if len(self.content) > 80 else self.content,
            'media_count': len(self.media),
            'random_media': self.random_media,
            'media_count_per_post': self.media_count,
            'delay_min': self.delay_min,
            'delay_max': self.delay_max,
        }
        print(json.dumps(print_data, ensure_ascii=False, indent=2), flush=True)

        print(f"\n{'='*70}", flush=True)
        print(f"[{ts}] 📋 Danh sách nhóm:", flush=True)
        print(f"{'='*70}", flush=True)
        for i, g in enumerate(self.groups, 1):
            print(f"{i}. {g.get('name', 'N/A')} - {g.get('url', 'N/A')}", flush=True)

        print(f"\n{'='*70}\n", flush=True)

        self.main_comment()