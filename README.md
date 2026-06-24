# YMusic

Cross-platform music app with HTML/CSS/JS frontend and Go backend.

Supports **Windows**, **Linux** (desktop via Wails v2), and **Android** (WebView + gomobile).

## Build

```bash
# Desktop (Windows/Linux)
python build.py -Desktop

# Android APK
python build.py -Android
```

The Android toolchain (JDK 17, Android SDK + NDK) must be placed in `for_android/`.  
See `for_android/README.md` for setup details.

## Structure

- `main.go` / `app.go` — Wails desktop entrypoint
- `core/core.go` — shared Go logic
- `mobile/mobile.go` — gomobile bind entry
- `frontend/` — shared HTML/CSS/JS UI
- `for_android/` — Android build project
- `build.py` — single build script

## License

MIT
