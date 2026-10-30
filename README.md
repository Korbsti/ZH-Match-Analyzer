# ZH Match Analyzer & Live Companion Suite
> **Made by Korbsti** · High-performance analytics, interactive tactical radar, and telemetry companion for *Command & Conquer: Generals – Zero Hour* & mods.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Zero Hour](https://img.shields.io/badge/Game-C%26C%20Generals%20Zero%20Hour-orange.svg)](#)
[![Mod Compatible](https://img.shields.io/badge/Compatibility-Mod%20Compatible%20(ROTR%2C%20ShockWave%2C%20Contra)-green.svg)](#)
[![Languages](https://img.shields.io/badge/Languages-7%20Supported%20(including%20Arabic%20RTL)-purple.svg)](#)

---

## Experimental Status & Compatibility Notice

> [!WARNING]
> **Active Development / Experimental**: This project is currently **experimental**. While core replay parsing, tactical radar map scrubbing, and live companion recording work across standard multiplayer matches, edge cases (such as exotic mod pack command IDs, uncalibrated map boundaries, or unusual game connection drops) will most likely need some extra edits and tweaks to the code.

**Human Players Only (AI Opponents NOT Supported)**: This analyzer and companion suite does **NOT** support AI / Computer bot skirmish matches. In the Command & Conquer Generals Zero Hour SAGE engine, AI decisions, scripts, and build queues run purely in local memory on your CPU and are never logged into replay command packets (`.rep`). Replays must be from human-vs-human matches (Multiplayer, LAN, GameRanger, CnCNet, Radmin, etc.).

---

## What's New in v6.0

### 🎨 Mod themes – the whole app looks like your mod
Open **Theme** (or press `T`). Pick a mod and the entire interface re-skins: colours, headline fonts, background artwork, buttons, badges, even the tactical-map grid.

| Theme | Look |
|---|---|
| **Zero Hour Classic** | Steel blue + indigo, tactical grid |
| **Rise of the Reds** | Crimson & gold, ☭ badge, star pattern, Oswald headings |
| **ShockWave** | Electric cyan & violet, hex grid, Orbitron headings |
| **Contra** | Olive & khaki, camo stripes, Black Ops headings |
| **Operation Firestorm** | Ember orange & yellow, glowing embers |
| **Custom** | Pick your own two colours |

**Auto-detect** (default) reads the replay's version / name / map and switches theme when you click a replay from a different mod. Prefer one look? Choose it manually.

### 🖼 Custom wallpaper mode
- Choose any image (or paste an image URL, or drop an image onto the Theme panel).
- Sliders for **dim**, **blur** and **panel opacity** so cards turn glassy and your wallpaper shows through.
- Images are resized automatically and remembered between sessions. Switch back to *Mod artwork* or *Plain* any time.

### 🚀 Launcher / EXE with Desktop shortcut
`zh_launcher.py` (or the built `ZH_Match_Analyzer.exe`) starts a tiny local web server on `127.0.0.1` (never exposed to your network), opens the analyzer in your browser, **auto-loads your replay folder**, and creates a **Desktop shortcut** the first time it runs.

**Get the EXE (pick one):**
1. **Windows PC with Python:** double-click `Build_EXE.bat` → produces `ZH_Match_Analyzer.exe` and launches it.
2. **GitHub:** push the repo, open *Actions → Build Windows EXE → Run workflow*, download the artifact (tagging a release `v6.0` attaches it automatically).
3. **No build at all:** double-click `Launch_App.bat` (needs Python).

Launcher options: `--port N`, `--replays "D:\\Replays"`, `--no-browser`, `--shortcut`, `--no-shortcut`, `--record` (also runs the live recorder).
The replay folder is auto-detected (Documents / OneDrive); `--replays` remembers a custom one.

Also fixed: recorder `.zhtelemetry` files are now loaded properly when scanning a folder, and a match is no longer listed twice (telemetry + its `.rep` copy).

---

## What's New in v5.0

- **Colour overhaul** – every player now gets a unique hue, and none of them clash with the built-in meanings (red = combat, amber = attack-move, orange = powers, slate = selection). Action-category bars no longer reuse player colours.
- **New chart engine** – crisp HiDPI canvases, "nice" axis scales, `k` abbreviations, gradient fills, crosshair hover with per-player markers and a sorted tooltip.
- **Match Pulse ribbon** (Overview) – powers, eliminations and clashes plotted across the whole match.
- **Tactical Radar** (Compare) – seven normalised metrics per player on one chart.
- **Save map as PNG** (📸 button or `P`) straight from the Tactical Map.
- **Keyboard shortcuts** – press `?` in the app. `1-9` tabs, `J/K` replays, `/` search, `Space` play/pause, `←/→` seek, `+/-/0` zoom, `[` sidebar.
- **Refreshed UI** – glass cards, gradient tabs, soft entrance animations, toasts, focus rings, reduced-motion support.
- **Reliability** – Tailwind now loads from the official CDN with the previous host as automatic fallback; the recorder launcher runs unbuffered on every Python path.

---

## Overview

**ZH Match Analyzer** is an advanced, client-side tactical replay analyzer and live telemetry system designed for competitive and casual *Zero Hour* players. Built to analyze standard SAGE `.rep` files as well as comprehensive live companion logs (`.zhtelemetry`), it brings modern esports-grade telemetry, casualty breakdowns, second-by-second economy tracking, and high-resolution spatial radar visualization directly to your browser.

Works out of the box with **Vanilla Zero Hour**, **The First Decade**, **Steam & EA App versions**, and popular mods such as **Rise of the Reds (ROTR)**, **ShockWave**, **Contra**, and **Operation Firestorm**.

---

## Key Features

### 1. Interactive Tactical Radar Map
- **Full 60 FPS Replay Scrubbing**: Fast-forward, rewind, and variable playback speed (1x to 60x).
- **High-Precision SAGE World Bounds Alignment**: Pre-calibrated terrain boundaries (`[0, 3050]`, `[0, 3200]`, `[0, 3500]`, `[0, 4000]`) ensuring structures, rally lines, and move orders align with terrain satellite textures by default.
- **Toggleable Visualization Layers**:
  - **Real Terrain**: Satellite aerial imagery with adjustable opacity slider.
  - **Structures**: Base buildings, tech centers, and defensive lines.
  - **Destination Points & Reticles**: Real-time order destinations.
  - **Maneuver Paths**: Sequential click-to-click unit motion chains.
  - **Attack Vectors**: Attack-move arrows and direct target locks.
  - **Combat Heatmap**: High-density engagement hotspots.
  - **Special Strikes**: Particle cannons, SCUD storms, MOABs, and general powers.
  - **Base Perimeters**: Dynamic territorial influence boundaries.
  - **Battle Hotspots**: Multi-team engagement markers.
  - **Live Casualties**: Flashing casualty markers, casualty feeds, and floating unit drop notifications.
- **Built-in Map Calibration Tool**: Fine-tune map coordinate offsets and stretch percentages with one click.

### 2. Analytical Views
1. **Overview**: Key match vitals, MVP badge, player strengths, tactical vulnerabilities, opening builds, and shareable match summaries.
2. **Tactical Map**: Live interactive spatial radar canvas with time scrubbing.
3. **APM Curve**: Second-by-second and cumulative Actions Per Minute benchmarking.
4. **Combat & Economy (Comprehensive)**:
   - Total enemy units destroyed vs friendly casualties.
   - Cumulative harvested income vs unspent cash reserves curve.
   - Active combat army material power index over time.
   - Detailed per-player K/D ratios and structures razed breakdown.
5. **Actions Breakdown**: Order classification (Micro, Macro, Selection, Powers).
6. **Production**: Chronological build openers and unit queue timelines.
7. **Timeline**: Searchable and filterable chronological event feed.
8. **Hotkeys**: Control group assignments (0 through 9) and selection frequency.
9. **Compare**: Head-to-head tactical matrix comparing key metrics across all players.

### 3. Internationalization (7 Languages)
Switch languages seamlessly with one click from the top-left menu:
- English
- Arabic (Full Right-to-Left RTL layout support)
- Russian
- Simplified Chinese
- German
- Spanish
- French

### 4. Directory Persistence & Drag-and-Drop
- Built-in **IndexedDB directory handle memory**: Remembers your Replays and Maps folders across browser restarts without re-uploading.
- Drag and drop `.rep`, `.zhtelemetry`, or `.tga` files directly into the window.

---

## Quick Start

### Option A: Use the Web Dashboard (No Installation Required)
1. Double-click `ZH_Replay_Analyzer.html` in your browser (Google Chrome, Microsoft Edge, Firefox, or Safari).
2. Click **Scan Replays Folder** or drag any `.rep` file into the window.
3. Explore the 9 tactical tabs and enjoy instant playback.

### Option B: Record Comprehensive Live Telemetry
To unlock the **Combat & Economy** tab, live unit destruction curves, and casualty markers:
1. Double-click `Record_Match.bat` before or during your match.
2. Play your *Zero Hour* game normally.
3. The companion recorder (`zh_recorder.py`) will automatically capture live lockstep memory events and generate a `.zhtelemetry` file.
4. The file automatically opens in the Analyzer.

---

## Replay Requirements & Caveats

- **Human Players Only**: Replays containing AI / Computer players are not supported.
- **Supported Formats**: SAGE Lockstep replay files (`.rep`) and companion live telemetry files (`.zhtelemetry`).
- **Network / Match Types**: 1v1, 2v2, 3v3, 4v4, and Free-For-All human matches (Multiplayer, LAN, Direct Connect).

---

## Mod Compatibility
Compatible with all SAGE-engine C&C Generals Zero Hour releases:
- Vanilla Zero Hour (v1.04)
- Rise of the Reds (ROTR)
- ShockWave & ShockWave Chaos
- Contra (007, 008, 009)
- Operation Firestorm
- Reborn & NProject Mod

---

## License & Credits

Created by **Korbsti**. Distributed under the **MIT License**.
Special thanks to the Command & Conquer Generals Zero Hour community.
