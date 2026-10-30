=======================================================
     ZERO HOUR MATCH STATISTICS ENHANCER & RECORDER
                   Created by Korbsti
=======================================================

Welcome to the Zero Hour Match Statistics Enhancer!

This tool lets you analyze Command & Conquer: Generals - Zero Hour
replays, inspect player APM, view tactical radar movement paths,
inspect real-time combat casualty spikes & economy cash flow,
and enjoy candid player performance breakdowns.

-------------------------------------------------------
PROJECT STATUS: EXPERIMENTAL
-------------------------------------------------------
NOTE: This software suite is currently EXPERIMENTAL and in
active development. While core replay parsing, tactical radar map
playback, and live companion telemetry work across standard
multiplayer matches, you will most likely need some extra edits
and tweaks to the code as you test different mod packs, custom map
boundaries, or unusual netcode conditions.

-------------------------------------------------------
IMPORTANT COMPATIBILITY NOTICE:
-------------------------------------------------------
HUMAN PLAYERS ONLY: This tool does NOT support AI opponents
or computer skirmish bot replays. In the SAGE game engine,
AI decisions and logic run locally on CPU and are not logged
to replay command packets (.rep). Replays must be from
human-vs-human matches (Multiplayer / LAN).

-------------------------------------------------------
HOW TO USE:
-------------------------------------------------------

OPTION 1: Pure Browser Replay Viewer (No Setup Required)
  1. Double-click "ZH_Replay_Analyzer.html" directly in any browser
     (Chrome, Edge, Firefox, Safari).
  2. 11 sample matches and 18 map textures are preloaded!
  3. Drag and drop any .rep or .zhtelemetry file from your
     Replays folder onto the window, or click "Scan Replays Folder".
  4. Works 100% offline.

OPTION 2: Live Match Recording & Full Telemetry
  1. Double-click "Record_Match.bat" before or during your match.
  2. Play your match in Zero Hour normally.
  3. When your match ends, the companion recorder automatically
     captures full live telemetry (Units Destroyed, Combat Spikes,
     Money Curves, Casualties).
  4. The match opens in the dashboard automatically!

-------------------------------------------------------
KEY FEATURES:
-------------------------------------------------------
- Dynamic Combat Spikes (Units Eliminated / Min) & Cumulative Total
- Economy Cash Flow & Unspent Bank Reserves Curves
- 7 Languages: English, Arabic (RTL), Russian, Chinese, German, Spanish, French
- Folder Memory: Remembers your Replays and Maps folders automatically
- Draggable Border Slider with pointer tracking
- Instant Sidebar Collapse / Fullscreen View
- Tactical Radar Map with real aerial terrain backdrops
- Accurate SAGE World Bounds mapping (Keep of the Beach, Armored Fury, etc.)
- Maneuver paths, attack vectors, and combat density hotspots
- Automatic base cleanup when a player is eliminated
- Tactical MVP & Ineffective Player breakdown
- Full Mod Compatibility: ROTR, ShockWave, Contra, Vanilla Zero Hour

-------------------------------------------------------
FILES IN THIS PACKAGE:
-------------------------------------------------------
- ZH_Replay_Analyzer.html : Standalone interactive visualizer dashboard
- Record_Match.bat        : One-click launcher for live recorder
- zh_recorder.py          : Live match telemetry companion
- README.txt              : This quick guide
- README.md               : Formatted markdown guide

Created for the C&C Zero Hour community by Korbsti.
Distributed under the MIT License.


v5.0 highlights: unique player colours, new chart engine, Match Pulse ribbon, Tactical Radar, map PNG export, keyboard shortcuts (press ? in the app).

v6.0: mod themes (ROTR, ShockWave, Contra, Firestorm, Custom, auto-detect), custom wallpaper mode, zh_launcher.py + Build_EXE.bat (EXE with Desktop shortcut that opens the app).
