# TeamViewer ID Changer for macOS

[English](#english) | [Tiếng Việt](#tiếng-việt)

---

## English

A tool to change TeamViewer ID on macOS by completely removing old configurations, reinstalling from `.dmg`, patching binaries to change hardware fingerprint, and re-signing the app.

### Features

- Completely removes 100% of TeamViewer traces (app, config, cache, helpers, daemons, receipts)
- Auto-reinstalls TeamViewer from `.dmg` file
- Binary patching: replaces `IOPlatformExpert` and `IOPlatformSerialNumber` with random values
- Ad-hoc codesigning after patching
- Native macOS GUI (dialog boxes) — no extra dependencies
- CLI version included for terminal usage

### Requirements

- macOS 12.0 or later
- Python 3.x (pre-installed on macOS)
- Admin privileges (sudo)
- `TeamViewer.dmg` file (for auto-reinstall)

### Usage

#### Option 1: GUI App (recommended)

1. Download `TeamViewer.ID.Changer.app.zip` from [Releases](../../releases/latest)
2. Unzip and double-click `TeamViewer ID Changer.app`
3. If blocked by Gatekeeper: right-click → Open → Open
4. Place `TeamViewer.dmg` in Desktop or Downloads (auto-detected)
5. Follow on-screen instructions
6. **Restart your Mac** after completion

#### Option 2: CLI (terminal)

```bash
sudo python3 TeamViewer-15-id-changer-for-mac.py
```

#### Option 3: Build from source

```bash
# Generate icon (optional)
bash generate-icon.sh

# Build .app
bash build-app.sh
```

### How It Works

```
1. Kill processes + unload TeamViewer services
2. Remove TeamViewer.app
3. Delete all config files, caches, logs, helpers, daemons, receipts
4. Reinstall TeamViewer from .dmg
5. Patch binaries — replace IOPlatformExpert & IOPlatformSerialNumber with random values
6. Ad-hoc codesign (codesign -f -s - --deep)
7. Register app with LaunchServices
8. Reload services
9. Restart Mac → TeamViewer gets a new ID
```

### Important Notes

- ⚠️ **You must restart your Mac** after running for macOS to update the code signature
- The tool works completely offline — no network connections
- All previous TeamViewer settings will be lost (contacts, configurations...)
- Debug log saved at `~/Desktop/tv-changer-debug.log`
- Compatible with TeamViewer 15.x on macOS 12+

---

## Tiếng Việt

Công cụ thay đổi TeamViewer ID trên macOS bằng cách xoá sạch cấu hình cũ, cài lại từ file `.dmg`, patch binary để thay đổi hardware fingerprint, và codesign lại app.

### Tính năng

- Xoá sạch 100% TeamViewer (app, config, cache, helper, daemon, receipts)
- Tự động cài lại TeamViewer từ file `.dmg`
- Patch binary: thay thế `IOPlatformExpert` và `IOPlatformSerialNumber` bằng giá trị ngẫu nhiên
- Codesign ad-hoc sau khi patch
- Giao diện GUI native macOS (dialog boxes) — không cần cài thêm gì
- Phiên bản CLI cho terminal

### Yêu cầu

- macOS 12.0 trở lên
- Python 3.x (có sẵn trên macOS)
- Quyền Admin (sudo)
- File `TeamViewer.dmg` (nếu muốn cài lại tự động)

### Cách sử dụng

#### Cách 1: Dùng app GUI (khuyến nghị)

1. Tải file `TeamViewer.ID.Changer.app.zip` từ [Releases](../../releases/latest)
2. Giải nén và double-click `TeamViewer ID Changer.app`
3. Nếu macOS chặn (Gatekeeper): chuột phải → Open → Open
4. Đặt file `TeamViewer.dmg` ở Desktop hoặc Downloads (app sẽ tự tìm)
5. Làm theo hướng dẫn trên màn hình
6. **Restart máy** sau khi hoàn tất

#### Cách 2: Dùng CLI (terminal)

```bash
sudo python3 TeamViewer-15-id-changer-for-mac.py
```

#### Cách 3: Build app từ source

```bash
# Tạo icon (tuỳ chọn)
bash generate-icon.sh

# Build .app
bash build-app.sh
```

### Cách hoạt động

```
1. Kill processes + unload services TeamViewer
2. Xoá sạch TeamViewer.app
3. Xoá toàn bộ file cấu hình, cache, logs, helpers, daemons, receipts
4. Cài lại TeamViewer từ file .dmg
5. Patch binaries — thay IOPlatformExpert và IOPlatformSerialNumber bằng giá trị random
6. Codesign ad-hoc (codesign -f -s - --deep)
7. Đăng ký app với LaunchServices
8. Reload services
9. Restart máy → TeamViewer nhận ID mới
```

### Lưu ý quan trọng

- ⚠️ **Bắt buộc restart máy** sau khi chạy để macOS cập nhật code signature
- Tool hoạt động hoàn toàn offline, không kết nối mạng
- Mọi cài đặt TeamViewer cũ sẽ bị xoá (danh bạ, cấu hình...)
- File log debug được lưu tại `~/Desktop/tv-changer-debug.log`
- Tương thích với TeamViewer 15.x trên macOS 12+

---

## Project Structure

```
├── TeamViewer-ID-Changer-GUI.py         # Main GUI app (native macOS dialogs)
├── TeamViewer-15-id-changer-for-mac.py  # CLI version
├── build-app.sh                          # Build .app bundle script
├── generate-icon.sh                      # Generate .icns icon script
├── AppIcon.icns                          # App icon
└── TeamViewer ID Changer.app/            # Pre-built app bundle
```

---

## Support / Ủng hộ tác giả

If you find this project useful, consider supporting the author.

Nếu thấy project hữu ích, bạn có thể ủng hộ tác giả.

### Bank Transfer / Chuyển khoản

| Method | Account | Name |
|--------|---------|------|
| MB Bank | `0360126996868` | LE VAN AN |
| Momo | `0976896621` | LE VAN AN |

### Other ways to support

- ⭐ Star the repo on GitHub
- 📢 Share with friends and colleagues
- 🐛 Report bugs or suggest features via [Issues](../../issues)

---

## Author

Le Van An (Vietnam IT)

## License

MIT License
