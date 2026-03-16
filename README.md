# TeamViewer ID Changer for macOS

Công cụ thay đổi TeamViewer ID trên macOS bằng cách xoá sạch cấu hình cũ, cài lại từ file `.dmg`, patch binary để thay đổi hardware fingerprint, và codesign lại app.

## Tính năng

- Xoá sạch 100% TeamViewer (app, config, cache, helper, daemon, receipts)
- Tự động cài lại TeamViewer từ file `.dmg`
- Patch binary: thay thế `IOPlatformExpert` và `IOPlatformSerialNumber` bằng giá trị ngẫu nhiên
- Codesign ad-hoc sau khi patch
- Giao diện GUI native macOS (dialog boxes) — không cần cài thêm gì
- Phiên bản CLI cho terminal

## Yêu cầu

- macOS 12.0 trở lên
- Python 3.x (có sẵn trên macOS)
- Quyền Admin (sudo)
- File `TeamViewer.dmg` (nếu muốn cài lại tự động)

## Cách sử dụng

### Cách 1: Dùng app GUI (khuyến nghị)

1. Tải file `TeamViewer.ID.Changer.app.zip` từ [Releases](../../releases/latest)
2. Giải nén và double-click `TeamViewer ID Changer.app`
3. Nếu macOS chặn (Gatekeeper): chuột phải → Open → Open
4. Đặt file `TeamViewer.dmg` ở Desktop hoặc Downloads (app sẽ tự tìm)
5. Làm theo hướng dẫn trên màn hình
6. **Restart máy** sau khi hoàn tất

### Cách 2: Dùng CLI (terminal)

```bash
sudo python3 TeamViewer-15-id-changer-for-mac.py
```

### Cách 3: Build app từ source

```bash
# Tạo icon (tuỳ chọn)
bash generate-icon.sh

# Build .app
bash build-app.sh
```

## Cách hoạt động

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

## Cấu trúc project

```
├── TeamViewer-ID-Changer-GUI.py      # App GUI chính (native macOS dialogs)
├── TeamViewer-15-id-changer-for-mac.py  # Phiên bản CLI
├── build-app.sh                       # Script build .app bundle
├── generate-icon.sh                   # Script tạo icon .icns
├── AppIcon.icns                       # Icon app
└── TeamViewer ID Changer.app/         # App bundle đã build sẵn
```

## Lưu ý quan trọng

- ⚠️ **Bắt buộc restart máy** sau khi chạy để macOS cập nhật code signature
- Tool hoạt động hoàn toàn offline, không kết nối mạng
- Mọi cài đặt TeamViewer cũ sẽ bị xoá (danh bạ, cấu hình...)
- File log debug được lưu tại `~/Desktop/tv-changer-debug.log`
- Tương thích với TeamViewer 15.x trên macOS 12+

## Screenshots

App sử dụng native macOS dialogs:

1. Quét hệ thống → hiển thị ID hiện tại và số file cần xoá
2. Tự động tìm file `.dmg` hoặc cho phép chọn thủ công
3. Xác nhận trước khi thực hiện
4. Hiển thị kết quả với ID cũ/mới
5. Tuỳ chọn restart máy ngay

## License

MIT License
