# 🎨 Focal Studio Designer

> **Visual UI Designer, Interactive Canvas & C Code Synthesizer (LVGL v8 / ESP-IDF) for Focal CNC Laser Touch Displays.**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg)](LICENSE)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38bdf8.svg)](https://tailwindcss.com/)
[![Electron](https://img.shields.io/badge/Electron-34-47848F.svg)](https://www.electronjs.org/)
[![Target: LVGL](https://img.shields.io/badge/Target-LVGL_v8.3-orange.svg)](https://lvgl.io/)
[![Author: Jhoel Ospino](https://img.shields.io/badge/Author-Jhoel_Ospino-purple.svg)](https://github.com/Jhoel-ospino)

---

## 📖 Overview

**Focal Studio Designer** is a dedicated visual IDE and native code compiler created for the **Focal CNC Laser Cutter** ecosystem. It bridges modern web-based UI engineering with low-level embedded systems:

- Design touchscreens directly on a pixel-perfect **480×320 canvas** matching the physical 3.5" TFT display (ILI9488 + XPT2046).
- Export clean, high-performance, MISRA-compliant **C code (`ui_screens.c`)** for LVGL v8 running on ESP32-S3 or the desktop simulator.
- Implement an **Apple-inspired industrial design philosophy** (*Focal Design System*): pastel color palettes, generous border radii (12–16px), monochromatic vector iconography, and large tactile hitboxes (≥ 44×44 px per ISO 9241-9).

---

## 🏛️ Architecture & Synthesis Pipeline

```
                     screens_layout.schema.json (JSON Schema Draft-07)
                                    │
                                    ▼
screens_layout.json  ──▶  scripts/codegen_c.py  ──▶  ui_screens.c
 (Declarative Spec)        (Python AST Generator)    ├── Firmware (ESP32-S3)
                                                     └── Simulator (SDL2)
```

1. **`screens_layout.json`**: Declarative state tree modeling 7 screens, 60+ buttons, cards, DRO displays, modal sheets, and dynamic waveforms.
2. **`screens_layout.schema.json`**: Formal schema enforcing geometry, styles, colors, user-data, and callback bindings.
3. **`scripts/codegen_c.py`**: Python synthesis engine that compiles the JSON specification into optimized C code with zero runtime parsing overhead.
4. **`src/`**: Full React 19 + Tailwind v4 interactive desktop app with live canvas drag-and-drop, theme tokens, and component property inspector.

---

## 🚀 Quick Start

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python 3.10+](https://www.python.org/)

### 1. Installation
```bash
git clone https://github.com/Jhoel-ospino/focal-studio.git
cd focal-studio
npm install
```

### 2. Run Web Development Server
```bash
npm run dev
# Opens at http://localhost:5173
```

### 3. Run as Native Desktop App (Electron)
```bash
npm run electron:dev
```

### 4. Compile C Code from Layout Spec
```bash
python3 scripts/codegen_c.py
# Generates production-ready ui_screens.c
```

---

## 📱 Screens Built with Focal Studio

1. **Launcher**: 3×2 card grid for direct access to Control, Files, Live Monitor, Geometry Calibration, Quick Cut, and Settings.
2. **Jogging & Machine Control**: XY directional jog pad, continuous/discrete stepping, laser test fire, coordinate DRO, and framing tools.
3. **File Browser**: Local MicroSD and Flash storage navigator with file details, size formatting, and instantaneous G-code loading.
4. **Cut Monitor**: Real-time laser job supervisor with dynamic liquid wave progress, elapsed/remaining ETA, and override sliders.
5. **Geometry Calibration**: Fine-tuning steps/mm, lead screw pitch backlash compensation, and travel boundaries.
6. **Quick Cut & Materials**: Preset database (MDF, Acrylic, Leather, Cardboard) with power/speed one-tap execution.
7. **Settings & Wi-Fi**: Machine parameters, network station configuration, laser frequency, and persistent NVS settings.

---

## ⚖️ License & Intellectual Property

**Copyright (c) 2026 Jhoel Ospino. All rights reserved.**

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**.

- **Non-Commercial Only**: Commercial exploitation, distribution, or inclusion in paid products/hardware without prior written permission from the copyright owner (Jhoel Ospino) is strictly prohibited.
- **Community & Education**: You are free to study, modify, and build upon this project for open community and non-commercial educational purposes.
- **Attribution**: Credit to **Jhoel Ospino** must remain intact in all derivative works.
