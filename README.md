# Hn38videoAItool

Windows desktop tool theo cấu trúc repo:

- `.github/` — GitHub Actions
- `assets/` — extension/assets
- `data/` — config mẫu
- `desktop/` — app chính
- `requirements` — Python dependencies
- `Hn38videoAItool.spec` — PyInstaller

## Chạy local

```bat
python -m pip install -r requirements
python desktop\main.py
```

## Build EXE

```bat
python -m pip install -r requirements
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm Hn38videoAItool.spec
```

Kết quả: `dist\Hn38videoAItool.exe`

## GitHub Actions

`.github/workflows/main.yml` tự:
1. checkout
2. cài Python 3.11
3. kiểm tra cấu trúc
4. compile-check
5. build PyInstaller
6. kiểm tra EXE
7. upload artifact

Tool mặc định chạy Demo Mode nên có thể mở và test ngay, không cần API.

Khi có API/endpoint được phép sử dụng, vào **Cài đặt API** để chuyển sang API mode.

Tool không đọc cookie, không lấy session token và không vượt CAPTCHA.
