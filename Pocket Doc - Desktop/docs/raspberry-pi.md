# Raspberry Pi Deployment Notes

Target hardware:

- Raspberry Pi 5, 16 GB RAM
- Raspberry Pi AI HAT+ 26 TOPS
- Waveshare 4.3inch HDMI LCD (B), 800x480

## Display

Waveshare documents this display as HDMI video plus USB capacitive touch. For Raspberry Pi config, use the vendor-provided 800x480 HDMI mode.

Typical `/boot/config.txt` style entries:

```text
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt 800 480 60 6 0 0 0
disable_splash=1
```

Exact path may differ on newer Raspberry Pi OS versions.

## Kiosk Command

```bash
chromium-browser \
  --kiosk \
  --disable-infobars \
  --noerrdialogs \
  --disable-session-crashed-bubble \
  http://localhost:8765
```

## Services

Recommended startup shape:

- `pocketdoc-backend.service`: starts Uvicorn
- desktop autostart or systemd user service: starts Chromium kiosk
- optional hardware watchdog/restart policy

## Cameras

Support plan:

- Pi Camera: primary capture path through `libcamera`
- USB camera: fallback through V4L2/OpenCV
- File upload: always available for imported images

## Inference

Recommended order:

1. Validate UI and mock imaging on Pi.
2. Run small `.onnx` or `.pt` model with CPU/GPU fallback.
3. Convert selected high-value models for Hailo AI HAT+.
4. Add hybrid remote inference for heavy models.

Do not load all models at once. Keep only the active model in memory, with a very small cache.
