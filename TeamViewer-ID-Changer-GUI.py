#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# TeamViewer ID Changer for macOS — v7.0
# Double-click .app to run. Uses macOS native dialogs.
#
# Approach: Xoá sạch + cài lại từ .dmg + patch binary + codesign
# Patch IOPlatformExpert + IOPlatformSerialNumber để thay hardware fingerprint
# Cần RESTART máy sau khi chạy để macOS cập nhật code signature
#
# Flow:
#   1. Kill processes + unload services
#   2. Xoá sạch 100% TeamViewer (app + config + cache + helper + daemon)
#   3. Cài lại từ .dmg
#   4. Patch binaries (thay hardware fingerprint)
#   5. Codesign ad-hoc
#   6. Restart máy → TeamViewer nhận ID mới
#
# An toàn: không kết nối mạng, không download, chỉ thao tác local.
#

import os
import platform
import glob
import subprocess
import sys
import time

# ── Constants ──────────────────────────────────────────────────

APP_VERSION = "7.0"
TV_APP = "/Applications/TeamViewer.app"

LAUNCH_PLISTS = [
    "/Library/LaunchDaemons/com.teamviewer.teamviewer_service.plist",
    "/Library/LaunchDaemons/com.teamviewer.Helper.plist",
    "/Library/LaunchAgents/com.teamviewer.teamviewer.plist",
    "/Library/LaunchAgents/com.teamviewer.teamviewer_desktop.plist",
]

PROCESS_NAMES = [
    "TeamViewer",
    "TeamViewer_Service",
    "TeamViewer_Desktop",
    "TeamViewer_Desktop_Proxy",
    "TeamViewer_Assignment",
    "Restarter",
    "com.teamviewer.Helper",
]


# ── Discovery ─────────────────────────────────────────────────

def read_current_id():
    """Read current TeamViewer ClientID from plist files."""
    # TeamViewer stores ClientID in the Machine preferences domain
    domains = [
        "com.teamviewer.teamviewer.preferences.Machine",
        "com.teamviewer.TeamViewer",
        "com.teamviewer.teamviewer.preferences",
        "com.teamviewer.teamviewer_service",
    ]
    keys = ["ClientID", "ClientID_64"]
    for domain in domains:
        for key in keys:
            try:
                result = subprocess.run(
                    ["defaults", "read", domain, key],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cid = result.stdout.strip()
                    if cid and cid != "0":
                        return cid
            except Exception:
                pass
    return None

def find_dmg():
    """Auto-find TeamViewer .dmg in Desktop, Downloads, or current dir."""
    home = os.path.expanduser("~")
    search_dirs = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "Downloads"),
        os.getcwd(),
        # Also check where the app bundle lives
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    ]
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        try:
            for f in os.listdir(d):
                if f.lower().startswith("teamviewer") and f.lower().endswith(".dmg"):
                    return os.path.join(d, f)
        except OSError:
            pass
    return None




def find_all_tv_files(username):
    """Find ALL TeamViewer traces on the system."""
    home = f"/Users/{username}"
    patterns = [
        # Preferences
        f"{home}/Library/Preferences/com.teamviewer.*.plist",
        f"{home}/Library/Preferences/com.TeamViewer*.plist",
        "/Library/Preferences/com.teamviewer.*.plist",
        "/Library/Preferences/com.TeamViewer*.plist",
        # Application Support
        f"{home}/Library/Application Support/TeamViewer",
        f"{home}/Library/Application Support/TeamViewer*",
        "/Library/Application Support/TeamViewer",
        "/Library/Application Support/TeamViewer*",
        # Caches
        f"{home}/Library/Caches/com.teamviewer.*",
        f"{home}/Library/Caches/com.TeamViewer*",
        # Logs
        f"{home}/Library/Logs/TeamViewer",
        f"{home}/Library/Logs/TeamViewer*",
        # Containers
        f"{home}/Library/Containers/com.teamviewer.*",
        # Group Containers
        f"{home}/Library/Group Containers/*teamviewer*",
        f"{home}/Library/Group Containers/*TeamViewer*",
        # Saved Application State
        f"{home}/Library/Saved Application State/com.teamviewer.*",
        # PrivilegedHelperTools (XPC helpers)
        "/Library/PrivilegedHelperTools/com.teamviewer.*",
        # LaunchDaemons & LaunchAgents
        "/Library/LaunchDaemons/com.teamviewer.*",
        "/Library/LaunchAgents/com.teamviewer.*",
        # Receipts (installer records)
        "/var/db/receipts/com.teamviewer.*",
    ]
    found = set()
    for pattern in patterns:
        found.update(glob.glob(pattern))
    return sorted(found)


# ── Native macOS Dialogs ──────────────────────────────────────

def _get_app_icon():
    """Get path to app icon for use in dialogs."""
    bundle_icon = os.path.join(os.path.dirname(__file__), "..", "Resources", "AppIcon.icns")
    if os.path.isfile(bundle_icon):
        return os.path.realpath(bundle_icon)
    src_icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AppIcon.icns")
    if os.path.isfile(src_icon):
        return src_icon
    return None


def show_dialog(title, message, buttons=None, icon="note", default=None):
    if buttons is None:
        buttons = ["OK"]
    btn_str = ", ".join(f'"{b}"' for b in buttons)
    default_btn = f'"{default or buttons[-1]}"'
    app_icon = _get_app_icon()
    if app_icon and icon in ("note", "app"):
        icon_part = f'with icon POSIX file "{app_icon}"'
    else:
        icon_part = f"with icon {icon}"
    parts = message.split("\n")
    msg_expr = " & return & ".join(f'"{_esc(p)}"' for p in parts)
    result = subprocess.run([
        "osascript",
        "-e", f'set msg to {msg_expr}',
        "-e", (
            f'display dialog msg '
            f'with title "{_esc(title)}" '
            f'buttons {{{btn_str}}} default button {default_btn} '
            f'{icon_part}'
        ),
    ], capture_output=True, text=True)
    return result.stdout.strip(), result.returncode == 0


def show_alert(title, message):
    parts = message.split("\n")
    msg_expr = " & return & ".join(f'"{_esc(p)}"' for p in parts)
    subprocess.run([
        "osascript",
        "-e", f'set msg to {msg_expr}',
        "-e", f'display alert "{_esc(title)}" message msg as critical',
    ], capture_output=True, text=True)


def choose_file(prompt, file_types=None):
    """Open native file chooser dialog. Returns path or None."""
    type_filter = ""
    if file_types:
        types = ", ".join(f'"{t}"' for t in file_types)
        type_filter = f' of type {{{types}}}'
    script = (
        f'set f to choose file with prompt "{_esc(prompt)}"{type_filter}\n'
        f'return POSIX path of f'
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ── Helpers ────────────────────────────────────────────────────

def get_username():
    return os.environ.get("USER") or os.getlogin()


def run_in_terminal(script_path):
    """Open Terminal.app and run script with sudo, user sees output live."""
    result_file = "/tmp/tv_changer_result.txt"
    wrapper_path = "/tmp/tv_changer_wrapper.sh"

    for f in [result_file, wrapper_path]:
        try:
            os.remove(f)
        except OSError:
            pass

    wrapper_lines = [
        "#!/bin/bash",
        "clear",
        'echo "══════════════════════════════════════════"',
        f'echo "  TeamViewer ID Changer v{APP_VERSION}"',
        'echo "══════════════════════════════════════════"',
        'echo ""',
        f'sudo bash "{script_path}"',
        'EXIT_CODE=$?',
        'echo ""',
        f'echo "$EXIT_CODE" > "{result_file}"',
        'if [ "$EXIT_CODE" -eq 0 ]; then',
        '  echo "══════════════════════════════════════════"',
        '  echo "  ✅ Hoàn tất! Cửa sổ này sẽ tự đóng..."',
        '  echo "══════════════════════════════════════════"',
        '  sleep 3',
        'else',
        '  echo "══════════════════════════════════════════"',
        '  echo "  ❌ Có lỗi xảy ra (exit code: $EXIT_CODE)"',
        '  echo "  Nhấn Enter để đóng..."',
        '  echo "══════════════════════════════════════════"',
        '  read',
        'fi',
        'exit',
    ]
    with open(wrapper_path, "w") as f:
        f.write("\n".join(wrapper_lines) + "\n")
    os.chmod(wrapper_path, 0o755)

    apple_script = (
        f'tell application "Terminal"\n'
        f'  activate\n'
        f'  do script "bash \\"{wrapper_path}\\""\n'
        f'end tell'
    )
    subprocess.run(["osascript", "-e", apple_script], capture_output=True)

    for _ in range(600):  # max 5 minutes
        if os.path.exists(result_file):
            time.sleep(0.5)
            try:
                with open(result_file, "r") as f:
                    code = f.read().strip()
                os.remove(result_file)
                return code == "0", f"exit code: {code}"
            except Exception:
                pass
        time.sleep(0.5)

    return False, "Timeout waiting for script"


# ── Build admin script ─────────────────────────────────────────

def build_admin_script(tv_files, username, dmg_path=None, rand_platform=None, rand_serial=None):
    """Shell script: xoá sạch TeamViewer + cài lại + patch binary."""
    lines = ["#!/bin/bash", ""]
    total = 9 if dmg_path else 6

    def step(msg):
        lines.append(f'echo "  {msg}"')

    # 1. Unload services
    step(f"[1/{total}] Tắt services...")
    for plist in LAUNCH_PLISTS:
        lines.append(f'launchctl unload "{plist}" 2>/dev/null || true')
    lines.append('launchctl remove com.teamviewer.teamviewer_service 2>/dev/null || true')
    lines.append('launchctl remove com.teamviewer.Helper 2>/dev/null || true')
    lines.append('launchctl remove com.teamviewer.teamviewer 2>/dev/null || true')
    lines.append('launchctl remove com.teamviewer.teamviewer_desktop 2>/dev/null || true')
    step(f"[1/{total}] ✓ Services đã tắt")
    lines.append("")

    # 2. Kill ALL processes
    step(f"[2/{total}] Kill processes...")
    for proc in PROCESS_NAMES:
        lines.append(f'killall -9 "{proc}" 2>/dev/null || true')
    lines.append("sleep 1")
    lines.append("for p in $(pgrep -f TeamViewer 2>/dev/null || true); do")
    lines.append('  CMD=$(ps -p "$p" -o args= 2>/dev/null || true)')
    lines.append('  case "$CMD" in *"ID Changer"*|*pgrep*|*pkill*) continue ;; esac')
    lines.append('  kill -9 "$p" 2>/dev/null || true')
    lines.append("done")
    lines.append("sleep 1")
    step(f"[2/{total}] ✓ Processes đã tắt")
    lines.append("")

    # 3. Xoá TeamViewer.app
    step(f"[3/{total}] Xoá TeamViewer.app...")
    lines.append(f'rm -rf "{TV_APP}"')
    step(f"[3/{total}] ✓ App đã xoá")
    lines.append("")

    # 4. Xoá sạch 100% mọi trace
    step(f"[4/{total}] Xoá sạch {len(tv_files)} files/folders...")
    for f in tv_files:
        lines.append(f'rm -rf "{f}"')
    lines.append(f'su "{username}" -c "defaults delete com.teamviewer.TeamViewer 2>/dev/null" || true')
    lines.append(f'su "{username}" -c "defaults delete com.teamviewer.teamviewer.preferences 2>/dev/null" || true')
    lines.append(f'su "{username}" -c "defaults delete com.teamviewer.teamviewer.preferences.Machine 2>/dev/null" || true')
    lines.append('defaults delete com.teamviewer.teamviewer_service 2>/dev/null || true')
    lines.append(f'su "{username}" -c "killall cfprefsd 2>/dev/null" || true')
    lines.append('killall cfprefsd 2>/dev/null || true')
    lines.append(f'rm -f "/Users/{username}/Library/Preferences/com.teamviewer."* 2>/dev/null || true')
    lines.append(f'rm -f "/Users/{username}/Library/Preferences/com.TeamViewer"* 2>/dev/null || true')
    lines.append('rm -f /Library/Preferences/com.teamviewer.* 2>/dev/null || true')
    lines.append('rm -f /Library/Preferences/com.TeamViewer* 2>/dev/null || true')
    step(f"[4/{total}] ✓ Đã xoá sạch")
    lines.append("")

    # 5. Cài lại từ .dmg
    if dmg_path:
        step(f"[5/{total}] Cài lại TeamViewer từ .dmg...")
        lines.append(f'hdiutil attach "{dmg_path}" -nobrowse -noverify -mountpoint /tmp/tv_dmg_mount 2>&1 || true')
        lines.append('MOUNT_POINT=""')
        lines.append('if [ -d /tmp/tv_dmg_mount ]; then')
        lines.append('  MOUNT_POINT=/tmp/tv_dmg_mount')
        lines.append('else')
        lines.append('  MOUNT_POINT=$(ls -d /Volumes/TeamViewer* 2>/dev/null | head -1)')
        lines.append('fi')
        lines.append('if [ -z "$MOUNT_POINT" ] || [ ! -d "$MOUNT_POINT" ]; then')
        lines.append('  echo "  ✗ Không mount được .dmg"')
        lines.append('  exit 1')
        lines.append('fi')
        lines.append('echo "  Mount: $MOUNT_POINT"')
        lines.append('PKG=$(find "$MOUNT_POINT" -name "*.pkg" 2>/dev/null | head -1)')
        lines.append('if [ -n "$PKG" ]; then')
        lines.append('  echo "  Cài từ: $PKG"')
        lines.append('  installer -pkg "$PKG" -target /')
        lines.append('elif [ -d "$MOUNT_POINT/TeamViewer.app" ]; then')
        lines.append('  echo "  Copy TeamViewer.app..."')
        lines.append(f'  cp -a "$MOUNT_POINT/TeamViewer.app" "{TV_APP}"')
        lines.append('else')
        lines.append('  echo "  ✗ Không tìm thấy .pkg hoặc .app trong .dmg"')
        lines.append('  hdiutil detach "$MOUNT_POINT" 2>/dev/null || true')
        lines.append('  exit 1')
        lines.append('fi')
        lines.append('hdiutil detach "$MOUNT_POINT" 2>/dev/null || true')
        step(f"[5/{total}] ✓ Đã cài lại TeamViewer")
        lines.append("")

        # 6. Patch binaries (thay đổi hardware fingerprint)
        step(f"[6/{total}] Patch binaries...")
        # Find all TeamViewer binaries in the fresh install
        lines.append(f'for BIN in "{TV_APP}/Contents/MacOS/TeamViewer" \\')
        lines.append(f'           "{TV_APP}/Contents/MacOS/TeamViewer_Service" \\')
        lines.append(f'           "{TV_APP}/Contents/MacOS/TeamViewer_Desktop_Proxy" \\')
        lines.append(f'           "{TV_APP}/Contents/Helpers/TeamViewer_Desktop" \\')
        lines.append(f'           "{TV_APP}/Contents/Helpers/TeamViewer_Assignment" \\')
        lines.append(f'           "{TV_APP}/Contents/Helpers/Restarter"; do')
        lines.append('  if [ -f "$BIN" ]; then')
        lines.append(f"    perl -pi -e 's/IOPlatformExpert.{{6}}/{rand_platform}/g' \"$BIN\"")
        lines.append(f"    perl -pi -e 's/IOPlatformSerialNumber\\x00[0-9a-zA-Z]{{8}}\\x00/IOPlatformSerialNumber\\x00{rand_serial}\\x00/g' \"$BIN\"")
        lines.append('    echo "    ✓ $(basename $BIN)"')
        lines.append('  fi')
        lines.append('done')
        step(f"[6/{total}] ✓ Binaries patched")
        lines.append("")

        # 7. Codesign (ad-hoc, like original scripts)
        step(f"[7/{total}] Codesign...")
        lines.append(f'xattr -cr "{TV_APP}" 2>/dev/null || true')
        lines.append(f'codesign -f -s - --deep "{TV_APP}" 2>&1 || true')
        step(f"[7/{total}] ✓ Codesign xong")
        lines.append("")

        # 8. Register with LaunchServices
        step(f"[8/{total}] Đăng ký app...")
        lines.append('LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"')
        lines.append(f'"$LSREGISTER" -f "{TV_APP}" 2>/dev/null || true')
        lines.append(f'spctl --add --label "TeamViewer" "{TV_APP}" 2>/dev/null || true')
        step(f"[8/{total}] ✓ OK")
        lines.append("")

        # 9. Reload services
        step(f"[9/{total}] Reload services...")
        for plist in LAUNCH_PLISTS:
            lines.append(f'[ -f "{plist}" ] && launchctl load "{plist}" 2>/dev/null || true')
        lines.append("sleep 1")
        step(f"[9/{total}] ✓ Services đã khởi động")

        lines.append("")
        lines.append('echo ""')
        lines.append(f'echo "  Serial:   {rand_serial}"')
        lines.append(f'echo "  Platform: {rand_platform}"')
        lines.append('echo ""')
        lines.append('echo "  ⚠️  QUAN TRỌNG: Cần RESTART máy trước khi mở TeamViewer!"')
    else:
        step(f"[5/{total}] ⏭ Bỏ qua cài lại (không có .dmg)")
        step(f"[6/{total}] ⏭ Bỏ qua")
        lines.append("")
        lines.append('echo ""')
        lines.append('echo "  → Tải và cài lại TeamViewer để nhận ID mới."')

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────

def main():
    # ── Step 1: Kiểm tra ──
    if platform.system() != "Darwin":
        show_alert("Lỗi", "Chỉ chạy trên macOS.")
        sys.exit(1)

    username = get_username()
    tv_installed = os.path.isdir(TV_APP)
    tv_files = find_all_tv_files(username)
    old_id = read_current_id()

    # Cho phép chạy ngay cả khi TeamViewer chưa cài
    # (user có thể muốn xoá sạch trace cũ + cài lại từ .dmg)

    # ── Step 2: Scan results ──
    status_app = "Có" if tv_installed else "Chưa cài"
    id_display = old_id if old_id else "Không đọc được"
    scan_msg = (
        f"TV ID Changer v{APP_VERSION}\n"
        f"\n"
        f"TeamViewer app:  {status_app}\n"
        f"ID hiện tại:  {id_display}\n"
        f"Files cần xoá:  {len(tv_files)} mục\n"
        f"\n"
        f"Cách hoạt động:\n"
        f"  1. Xoá sạch 100% TeamViewer\n"
        f"  2. Cài lại từ file .dmg\n"
        f"  3. Patch binary (thay hardware fingerprint)\n"
        f"  4. Codesign + Restart máy\n"
        f"  5. TeamViewer nhận ID mới\n"
        f"\n"
        f"⚠️ Cần RESTART máy sau khi chạy\n"
        f"\n"
        f"Tiếp tục?"
    )
    response, ok = show_dialog(
        "Quét hệ thống",
        scan_msg,
        buttons=["Thoát", "Tiếp tục"],
        icon="app",
        default="Tiếp tục"
    )
    if not ok or "Thoát" in response:
        sys.exit(0)

    # ── Step 3: Tìm file .dmg ──
    dmg_path = find_dmg()
    if dmg_path:
        # Tìm thấy tự động — xác nhận với user
        dmg_name = os.path.basename(dmg_path)
        dmg_dir = os.path.dirname(dmg_path)
        response, ok = show_dialog(
            "Tìm thấy .dmg",
            f"Tìm thấy file cài đặt:\n\n    {dmg_name}\n    ({dmg_dir})\n\nDùng file này?",
            buttons=["Chọn file khác", "Chỉ xoá", "Dùng file này"],
            icon="app",
            default="Dùng file này"
        )
        if not ok:
            sys.exit(0)
        if "Chọn file khác" in response:
            dmg_path = choose_file("Chọn file TeamViewer .dmg hoặc .pkg")
            if dmg_path and not (dmg_path.endswith(".dmg") or dmg_path.endswith(".pkg")):
                show_alert("Lỗi", "File phải là .dmg hoặc .pkg")
                sys.exit(1)
        elif "Chỉ xoá" in response:
            dmg_path = None
    else:
        # Không tìm thấy — hỏi user
        response, ok = show_dialog(
            "Không tìm thấy .dmg",
            "Không tìm thấy TeamViewer.dmg\ntrong Desktop hoặc Downloads.\n\nChọn file thủ công hoặc chỉ xoá sạch.",
            buttons=["Chỉ xoá", "Chọn .dmg"],
            icon="app",
            default="Chọn .dmg"
        )
        if ok and "dmg" in response.lower():
            dmg_path = choose_file("Chọn file TeamViewer .dmg hoặc .pkg")
            if dmg_path and not (dmg_path.endswith(".dmg") or dmg_path.endswith(".pkg")):
                show_alert("Lỗi", "File phải là .dmg hoặc .pkg")
                sys.exit(1)

    # ── Step 4: Cảnh báo cuối ──
    action_desc = "Xoá sạch + Cài lại" if dmg_path else "Chỉ xoá sạch"
    warn_msg = (
        f"Thao tác không thể hoàn tác:\n"
        f"\n"
        f"▸ Xoá TeamViewer.app\n"
        f"▸ Xoá {len(tv_files)} file cấu hình/cache\n"
        f"▸ Xoá helpers, daemons, receipts\n"
        f"▸ Cài lại + patch binary + codesign\n"
        f"▸ Mất toàn bộ cài đặt TeamViewer\n"
        f"\n"
        f"Chế độ: {action_desc}\n"
        f"⚠️ Cần RESTART máy sau khi hoàn tất\n"
        f"macOS sẽ hỏi mật khẩu Admin."
    )
    response, ok = show_dialog(
        "Xác nhận lần cuối",
        warn_msg,
        buttons=["Quay lại", "Xoá + Đổi ID"],
        icon="caution",
        default="Quay lại"
    )
    if not ok or "Quay lại" in response:
        sys.exit(0)

    # ── Step 5: Thực thi ──
    from uuid import uuid4
    rand_serial = uuid4().hex[:8].upper()
    rand_platform = "IOPlatformExpert" + uuid4().hex[:6].upper()

    actual_dmg = dmg_path
    if dmg_path and dmg_path.endswith(".pkg"):
        actual_dmg = None

    script = build_admin_script(tv_files, username, actual_dmg, rand_platform, rand_serial)

    script_path = "/tmp/tv_changer_script.sh"
    with open(script_path, "w") as f:
        f.write(script)

    # Debug log
    log_path = os.path.join(os.path.expanduser("~"), "Desktop", "tv-changer-debug.log")
    with open(log_path, "w") as f:
        f.write(f"=== OLD ID: {old_id or 'N/A'} ===\n")
        f.write(f"=== SERIAL: {rand_serial} | PLATFORM: {rand_platform} ===\n")
        f.write("=== ADMIN SCRIPT ===\n")
        f.write(script)
        f.write("\n\n")

    success, output = run_in_terminal(script_path)

    # Clean up
    for tmp in [script_path, "/tmp/tv_changer_wrapper.sh"]:
        try:
            os.remove(tmp)
        except OSError:
            pass

    with open(log_path, "a") as f:
        f.write(f"=== RESULT ===\n")
        f.write(f"success: {success}\n")
        f.write(f"output: {output}\n")

    if not success:
        if "cancel" in output.lower() or "user canceled" in output.lower():
            sys.exit(0)
        safe_output = output[:400].replace('"', "'").replace("\\", "/")
        show_alert("Lỗi", f"Đã xảy ra lỗi:\n{safe_output}")
        sys.exit(1)

    # ── Step 6: Đọc ID mới ──
    old_str = old_id if old_id else "Không rõ"
    new_id = None

    if dmg_path and os.path.isdir(TV_APP):
        # Mở TeamViewer ngắn để nó tạo ID mới, rồi đọc
        subprocess.run(["open", TV_APP], capture_output=True)
        # Đợi TeamViewer tạo ID (thử đọc nhiều lần)
        for i in range(20):  # max 20 giây
            time.sleep(1)
            new_id = read_current_id()
            if new_id and new_id != old_id:
                break
        # Kill TeamViewer sau khi đọc xong
        for proc in PROCESS_NAMES:
            subprocess.run(["killall", proc], capture_output=True)

    # ── Step 7: Kết quả ──
    new_str_display = new_id if new_id else "Chưa có (cần restart)"
    id_changed = new_id and new_id != old_id

    with open(log_path, "a") as f:
        f.write(f"=== OLD ID: {old_str} ===\n")
        f.write(f"=== NEW ID: {new_str_display} ===\n")
        f.write(f"=== CHANGED: {id_changed} ===\n")
        if dmg_path:
            f.write(f"=== PATCHED: serial={rand_serial} platform={rand_platform} ===\n")

    if dmg_path:
        if id_changed:
            result_title = "Đổi ID thành công!"
            result_msg = (
                f"══════════════════════════\n"
                f"  ID CŨ:   {old_str}\n"
                f"  ID MỚI:  {new_id}\n"
                f"══════════════════════════\n"
                f"\n"
                f"✓ Đã xoá sạch TeamViewer cũ\n"
                f"✓ Đã cài lại + patch binary\n"
                f"✓ ID đã thay đổi thành công\n"
                f"\n"
                f"Nên RESTART máy để ổn định."
            )
        else:
            result_title = "Hoàn tất — Cần Restart"
            result_msg = (
                f"══════════════════════════\n"
                f"  ID CŨ:   {old_str}\n"
                f"  ID MỚI:  {new_str_display}\n"
                f"══════════════════════════\n"
                f"\n"
                f"✓ Đã xoá sạch + cài lại + patch\n"
                f"\n"
                f"⚠️ Cần RESTART máy để TeamViewer\n"
                f"nhận hardware fingerprint mới.\n"
                f"Sau restart, mở TeamViewer để xem ID mới."
            )

        response, ok = show_dialog(
            result_title,
            result_msg,
            buttons=["Đóng", "Restart ngay"],
            icon="app",
            default="Restart ngay"
        )
        if ok and "Restart" in response:
            confirm, ok2 = show_dialog(
                "Restart máy?",
                "Máy sẽ restart ngay bây giờ.\nLưu hết công việc trước khi tiếp tục.",
                buttons=["Huỷ", "Restart"],
                icon="caution",
                default="Huỷ"
            )
            if ok2 and "Restart" in confirm:
                subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to restart'
                ], capture_output=True)
    else:
        result_msg = (
            f"Đã xoá sạch TeamViewer!\n"
            f"\n"
            f"ID cũ:  {old_str}\n"
            f"✓ Xoá {len(tv_files)} files/folders\n"
            f"\n"
            f"Bước tiếp theo:\n"
            f"  1. Tải TeamViewer từ teamviewer.com\n"
            f"  2. Cài đặt bình thường\n"
            f"  3. Mở TeamViewer → ID mới"
        )
        show_dialog("Hoàn tất", result_msg, buttons=["OK"], icon="app")


if __name__ == "__main__":
    import traceback
    log_path = os.path.join(os.path.expanduser("~"), "Desktop", "tv-changer-debug.log")
    try:
        main()
    except Exception as e:
        with open(log_path, "w") as f:
            f.write(f"CRASH: {e}\n\n")
            traceback.print_exc(file=f)
        show_alert("Crash", f"Lỗi: {e}\n\nXem log: ~/Desktop/tv-changer-debug.log")
        sys.exit(1)
