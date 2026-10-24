# ZH Match Analyzer & Live Companion Suite
> **Made by Korbsti** · High-performance analytics, interactive tactical radar, and telemetry companion for *Command & Conquer: Generals – Zero Hour* & mods.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Zero Hour](https://img.shields.io/badge/Game-C%26C%20Generals%20Zero%20Hour-orange.svg)](#)
[![Mod Compatible](https://img.shields.io/badge/Compatibility-Mod%20Compatible%20(ROTR%2C%20ShockWave%2C%20Contra)-green.svg)](#)
[![Languages](https://img.shields.io/badge/Languages-7%20Supported%20(including%20Arabic%20RTL)-purple.svg)](#)

---

## Important Compatibility Notice

**Human Players Only (AI Opponents NOT Supported)**: This analyzer and companion suite does **NOT** support AI / Computer bot skirmish matches. In the Command & Conquer Generals Zero Hour SAGE engine, AI decisions, scripts, and build queues run purely in local memory on your CPU and are never logged into replay command packets (`.rep`). Replays must be from human-vs-human matches (Multiplayer, LAN, GameRanger, CnCNet, Radmin, etc.).

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
