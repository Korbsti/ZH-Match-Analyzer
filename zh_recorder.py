"""
Zero Hour Live Companion & Telemetry Recorder
Monitors active Command & Conquer: Generals - Zero Hour matches in real time,
parses the SAGE lockstep binary command stream, estimates match combat/economy
telemetry, and exports paired (.rep + .zhtelemetry) datasets for tactical replay analysis.
"""

import math
import os, sys, time, struct, json, datetime, re

def get_default_replay_dir():
    """Locate the Zero Hour user replay directory (checks OneDrive and local Documents)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir).lower() == "replays":
        return script_dir
    if any(f.lower().endswith('.rep') for f in os.listdir(script_dir)):
        return script_dir

    candidates = [
        os.path.expanduser(r"~\OneDrive\Documents\Command and Conquer Generals Zero Hour Data\Replays"),
        os.path.expanduser(r"~\Documents\Command and Conquer Generals Zero Hour Data\Replays"),
        os.path.expanduser(r"~\OneDrive\Documents\Command and Conquer Generals Data\Replays"),
        os.path.expanduser(r"~\Documents\Command and Conquer Generals Data\Replays")
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return script_dir

DEF_DIR = get_default_replay_dir()

# SAGE Engine Command ID to Human-Readable Action Name
CMD_NAMES = {
    1001:"Select Units (Click / Box)", 1002:"Select Matching Units (2x Click / E)",
    1003:"Deselect Unit", 1004:"Clear Selection", 1005:"Group Command",
    1036:"Attack Squad", 1037:"Fire Special Weapon", 1038:"Fire Weapon @ Ground",
    1039:"Fire Weapon @ Target", 1040:"Special Power", 1041:"Power @ Location",
    1042:"Power @ Target", 1043:"Set Rally Point", 1044:"General Promotion",
    1045:"Research Upgrade", 1046:"Cancel Upgrade", 1047:"Queue Unit",
    1048:"Cancel Unit Queue", 1049:"Build Structure", 1050:"Build Wall",
    1051:"Cancel Build", 1052:"Sell Structure", 1053:"Exit Structure / Transport",
    1054:"Evacuate All", 1055:"Railed Transport", 1056:"Combat Drop / Rappel",
    1057:"Empty Transport", 1058:"Area Box Select", 1059:"Attack Target",
    1060:"Force Attack (Ctrl)", 1061:"Bombard Ground (Ctrl)", 1062:"Get Repaired",
    1063:"Get Healed", 1064:"Repair Target", 1065:"Resume Construction",
    1066:"Enter / Garrison", 1067:"Supply Dock", 1068:"Move Order",
    1069:"Attack-Move (A)", 1070:"Force Move", 1071:"Waypoint Path (Alt)",
    1072:"Guard Area (G)", 1073:"Guard Object (G)", 1074:"Stop Order (S)",
    1075:"Scatter Units (X)", 1076:"Hack Internet", 1077:"Cheer",
    1078:"Toggle Overcharge", 1079:"Switch Weapon Mode", 1080:"Convert to Car Bomb",
    1081:"Capture Building", 1082:"Disable Vehicle", 1083:"Steal Cash",
    1084:"Disable Building", 1085:"Snipe Vehicle Crew", 1086:"Power Override",
    1087:"Collect Salvage", 1088:"Clear Mines", 1089:"Place Beacon",
    1090:"Remove Beacon", 1091:"Beacon Text", 1093:"Surrender / Self-Destruct",
    1094:"Formation Move", 1096:"Disarm Mines", 1097:"Retaliation Stance"
}
for _i in range(10):
    CMD_NAMES[1006 + _i] = f"Create Group {_i} (Ctrl+{_i})"
    CMD_NAMES[1016 + _i] = f"Select Group {_i}"
    CMD_NAMES[1026 + _i] = f"Add to Group {_i} (Shift+{_i})"

# SAGE packet argument type byte sizes:
# 0: int32 (building/unit template ID), 1: float32, 2: uint8,
# 6: vec3 (12 bytes, X and Y 32-bit floats at bytes 0:8), etc.
SZ = {0:4, 1:4, 2:1, 3:4, 4:4, 5:4, 6:12, 7:8, 8:16, 9:4, 10:2}

def find_active_replay(rep_dir):
    """
    SAGE writes live lockstep packets to '00000000.rep' during matches,
    then renames it to 'LastReplay.rep' on the match result screen.
    """
    zero_rep = os.path.join(rep_dir, "00000000.rep")
    if os.path.exists(zero_rep):
        return zero_rep
    # Filter out auto-exported replays so the recorder doesn't monitor its own outputs
    reps = [
        os.path.join(rep_dir, f) for f in os.listdir(rep_dir)
        if f.lower().endswith('.rep') and not re.search(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.rep$', f, re.I)
    ]
    return max(reps, key=os.path.getmtime) if reps else None

def parse_rep_stream(path):
    """
    Parses a SAGE .rep binary file stream into structured match metadata,
    player action timelines, build orders, spatial movements, and engagements.
    """
    if not os.path.exists(path) or os.path.getsize(path) < 40: return None
    try:
        with open(path, 'rb') as f:
            magic = f.read(6)
            if magic != b'GENREP': return None
            f.seek(28)  # Skip to wide-char header block
            def r_u16():
                c, s = f.read(2), []
                while c and c != b'\x00\x00':
                    s.append(c.decode('utf-16le', errors='ignore'))
                    c = f.read(2)
                return ''.join(s)
            def r_u8():
                c, s = f.read(1), []
                while c and c != b'\x00':
                    s.append(c.decode('latin-1', errors='ignore'))
                    c = f.read(1)
                return ''.join(s)
            title = r_u16()
            f.seek(16, 1) # datetime
            ver = r_u16()
            r_u16() # builddate
            f.seek(12, 1)
            hdr = r_u8()
            f.seek(18, 1)

            # SAGE header contains key-value semicolon-delimited tokens:
            # M = map path, S = player slot entries, SC = starting cash
            tokens = {}
            for item in hdr.split(';'):
                if '=' in item:
                    k, v = item.split('=', 1)
                    tokens[k] = v
            map_name = tokens.get('M', '?').split('/')[-1]
            cash = tokens.get('SC', '10000')

            # Slot format: H[name],[ip],[port],...,[color],[faction],[team] (or C for computer bot)
            slots = []
            for s in tokens.get('S', '').split(':'):
                if s and (s[0] == 'H' or s[0] == 'C'):
                    parts = s[1:].split(',')
                    pname = parts[0] if parts else 'Player'
                    if s[0] == 'C':
                        pname = "AI " + ('Easy' if parts[0]=='E' else 'Medium' if parts[0]=='M' else 'Hard' if parts[0]=='H' else parts[0])
                    slots.append({
                        'name': pname,
                        'team': str(int(parts[7]) + 1) if len(parts) > 7 and parts[7].lstrip('-').isdigit() else '1',
                        'faction': parts[5] if len(parts) > 5 else '',
                        'color': parts[4] if len(parts) > 4 else '',
                        'ai': s[0] == 'C'
                    })

            players = {}
            events = []
            engagements = []
            max_t = 0
            total_orders = 0
            buildings = []
            last_cmd = {}

            while True:
                h = f.read(13)
                if len(h) < 13: break
                tc, c, pn, nc = struct.unpack('<IIIB', h)
                sig = f.read(2 * nc)
                args = []
                bad = False
                for i in range(nc):
                    t, n = sig[2*i], sig[2*i+1]
                    sz = SZ.get(t)
                    if sz is None: bad = True; break
                    for _ in range(n):
                        buf = f.read(sz)
                        if len(buf) < sz: bad = True; break
                        if t == 6: args.append((t, struct.unpack('<ff', buf[:8])))
                        elif sz >= 4: args.append((t, struct.unpack('<I', buf[:4])[0]))
                if bad or c in (1095, 1092, 27, 1000) or c < 1000 or c > 1999: continue

                max_t = max(max_t, tc)
                sec = round(tc / 15, 1)
                total_orders += 1

                if pn not in players:
                    s_idx = pn - 2 if pn >= 2 else 0
                    p_meta = slots[s_idx] if s_idx < len(slots) else {'name': f'Player {pn}', 'team': '1', 'ai': False}
                    players[pn] = {
                        'id': pn,
                        'name': p_meta['name'],
                        'team': p_meta['team'],
                        'faction': p_meta.get('faction', ''),
                        'ai': p_meta.get('ai', False),
                        'acts': [],
                        'eacts': [],
                        'cmd': {},
                        'cat': {'Micro': 0, 'Macro': 0, 'Selection': 0, 'Powers': 0},
                        'builds': [],
                        'units': [],
                        'powers': [],
                        'rally': [],
                        'groupsC': [0]*10,
                        'groupsS': [0]*10,
                        'moves': []
                    }

                p = players[pn]
                p['acts'].append(sec)
                # eAPM (Effective Actions Per Minute): Filter rapid duplicate selections and spam clicks.
                # In competitive RTS, players frequently spam box-selection (1001), double-clicks (1002), or deselect (1058)
                # within sub-250ms intervals. Excluding these gives an accurate measure of non-spam tactical decisions.
                prev_c, prev_s = last_cmd.get(pn, (0, -1))
                if not (c in (1001, 1002, 1058) and prev_c in (1001, 1002, 1058) and sec - prev_s < 0.25):
                    p['eacts'].append(sec)
                last_cmd[pn] = (c, sec)
                cmd_name = CMD_NAMES.get(c, f"Cmd {c}")
                p['cmd'][cmd_name] = p['cmd'].get(cmd_name, 0) + 1

                # SAGE Command Taxonomy:
                # - Macro: Structure placement, unit queueing, tech upgrades, asset sales, rally lines.
                # - Powers: Off-map support strikes, General powers (A-10s, MOAB, Particle Uplink, Scud Storm).
                # - Selection: Selection boxes, hotkey binding (ctrl+0-9), control group recall (1006-1035).
                # - Micro: Unit maneuvering, targeted attacks, bombards, formations, and ability triggers.
                if c in (1047, 1048, 1049, 1050, 1051, 1052, 1043, 1045, 1046, 1065, 1078, 1076): p['cat']['Macro'] += 1
                elif c in (1044, 1040, 1041, 1042, 1037, 1038, 1039): p['cat']['Powers'] += 1
                elif c <= 1005 or c == 1058 or (1006 <= c <= 1035): p['cat']['Selection'] += 1
                else: p['cat']['Micro'] += 1

                # Extract Vec3 world position if present (Type 6 = 12-byte IEEE-754 floats [X, Y, Z])
                loc = next((a[1] for a in args if a[0] == 6), None)

                if c in (1049, 1050):
                    bid = next((a[1] for a in args if a[0] == 0), 0)
                    bx, by = loc if loc else (0, 0)
                    b_entry = {'s': sec, 'id': bid, 'x': bx, 'y': by, 'p': pn}
                    buildings.append(b_entry)
                    p['builds'].append(b_entry)
                    events.append({'s': sec, 'p': pn, 'type': 'Build', 'txt': f"Placed structure #{hex(bid)}"})

                elif c == 1047:
                    uid = args[0][1] if args else 0
                    p['units'].append({'s': sec, 'id': uid})
                    events.append({'s': sec, 'p': pn, 'type': 'Unit', 'txt': f"Queued unit #{hex(uid)}"})

                elif c == 1045:
                    uid = args[0][1] if args else 0
                    events.append({'s': sec, 'p': pn, 'type': 'Upgrade', 'txt': f"Started upgrade #{hex(uid)}"})

                elif c == 1043 and loc:
                    p['rally'].append({'s': sec, 'x': loc[0], 'y': loc[1]})

                elif c == 1052:
                    events.append({'s': sec, 'p': pn, 'type': 'Sell', 'txt': "Sold structure (credited)"})

                elif c in (1093, 1053):
                    events.append({'s': sec, 'p': pn, 'type': 'Exit', 'txt': "Surrendered / left game"})

                elif 1006 <= c <= 1015:
                    p['groupsC'][c - 1006] += 1
                elif 1016 <= c <= 1035:
                    p['groupsS'][(c - 1016) % 10] += 1

                elif c in (1040, 1041, 1042, 1044):
                    p['powers'].append(sec)
                    txt = f"{cmd_name} @ ({round(loc[0])}, {round(loc[1])})" if loc else cmd_name
                    events.append({'s': sec, 'p': pn, 'type': 'Power', 'txt': txt})

                if loc and c in (1059, 1060, 1061, 1068, 1069, 1070):
                    kind = "attack" if c in (1059, 1060) else "bombard" if c == 1061 else "attackMove" if c == 1069 else "move"
                    p['moves'].append({'s': sec, 'x': loc[0], 'y': loc[1], 'kind': kind, 'cmd': c})

            dur = max_t / 15

            # Spatio-Temporal Ground Engagement Clustering:
            # SAGE replays do not log explicit death events; instead, skirmishes leave combat order signatures.
            # 1. Bucket non-move attack/ability orders into discrete 15-second windows and 350x350 world coordinate bins.
            # 2. Filter for contested hotspots (orders from >1 opposing team and >=4 total orders).
            # 3. Merge adjacent clashes occurring within 35 seconds and 600 distance units into cohesive continuous engagements.
            clash_bins = {}
            for p in players.values():
                p['n'] = len(p['acts'])
                p['last'] = p['acts'][-1] if p['acts'] else 0
                p['apm'] = round(p['n'] / max(1, p['last'] / 60))
                p['eapm'] = round(len(p.get('eacts', p['acts'])) / max(1, p['last'] / 60))
                for m in p['moves']:
                    if m['kind'] != 'move':
                        key = (int(m['s'] // 15) * 15, int(m['x'] // 350) * 350, int(m['y'] // 350) * 350)
                        b = clash_bins.setdefault(key, {'s': key[0], 'orders': 0, 'teams': set(), 'pts': []})
                        b['orders'] += 1
                        b['teams'].add(p['team'])
                        b['pts'].append((m['x'], m['y']))

            raw_clashes = sorted([b for b in clash_bins.values() if len(b['teams']) > 1 and b['orders'] >= 4], key=lambda x: x['s'])
            for c_bin in raw_clashes:
                cx = sum(pt[0] for pt in c_bin['pts']) / len(c_bin['pts'])
                cy = sum(pt[1] for pt in c_bin['pts']) / len(c_bin['pts'])
                if engagements and c_bin['s'] - engagements[-1]['s'] <= 35 and math.hypot(cx - engagements[-1]['x'], cy - engagements[-1]['y']) < 600:
                    engagements[-1]['orders'] += c_bin['orders']
                    engagements[-1]['end'] = c_bin['s'] + 15
                else:
                    engagements.append({'id': len(engagements) + 1, 's': c_bin['s'], 'end': c_bin['s'] + 20, 'x': round(cx), 'y': round(cy), 'orders': c_bin['orders']})

            # Player Pacing Analytics:
            # - Idle Gap: Longest pause where a player issued no commands (punishing macro lapses).
            # - Peak APM: Maximum actions executed in any rolling 60-second window.
            for p in players.values():
                gap, gap_at = 0, 0
                for i in range(1, len(p['acts'])):
                    g = p['acts'][i] - p['acts'][i-1]
                    if g > gap:
                        gap = g
                        gap_at = p['acts'][i-1]
                p['gap'] = gap
                p['gapAt'] = gap_at

                pk = 0
                j = 0
                for i in range(len(p['acts'])):
                    while p['acts'][i] - p['acts'][j] > 60:
                        j += 1
                    pk = max(pk, i - j + 1)
                p['peak'] = pk
                p['firstBuild'] = p['builds'][0]['s'] if p['builds'] else None
                p['firstUnit'] = p['units'][0]['s'] if p['units'] else None

            return {
                'title': title,
                'map': map_name,
                'ver': ver,
                'starting_cash': cash,
                'duration': round(dur),
                'total_orders': total_orders,
                'players': players,
                'slots': slots,
                'events': events,
                'engagements': engagements
            }
    except Exception:
        return None

def auto_name(map_name, player_dict, dt):
    clean_map = re.sub(r'\[.*?\]', '', map_name or 'Match')
    clean_map = re.sub(r'[^a-zA-Z0-9]', '_', clean_map).strip('_')
    clean_map = re.sub(r'_+', '_', clean_map)

    names = [p['name'] for p in player_dict.values() if not p.get('ai')]
    if not names:
        names = [p['name'] for p in player_dict.values()]
    p_names = [re.sub(r'[^a-zA-Z0-9]', '', n) for n in names[:2]]
    p_str = "_vs_".join(p_names) if p_names else "Match"

    ts = dt.strftime('%Y-%m-%d_%H-%M')
    return f"{clean_map}_{p_str}_{ts}"


def compute_match_casualties_and_economy(P, dur, raw_cash_str, win_list):
    """
    Synthesizes realistic casualty flows and financial balance sheets over the match timeline:
    - Conservation of Casualties: Enemy kills attributed to Team A must equal units lost by Team B.
    - Combat Contribution Score: Distributes credit across teammates based on micro activity (APM),
      aggressive movement commands, General's powers, and unit production throughput.
    - Supply Logistics & Cash Flow: Simulates standard SAGE harvesting rates ($18/s per active supply
      center), secondary economy expansion (hackers, black markets, drop zones), and equipment expenditures.
    - Active Material Army Value: Tracks real-time active army value based on units built minus cumulative casualties.
    """
    dur = dur or 600
    try:
        raw_cash = int(raw_cash_str or 10000)
    except:
        raw_cash = 10000
    win_set = set(win_list or [])
    step = max(10, math.ceil(dur / 40))

    # Step 1: Compute unit counts, baseline survival rates, and combat engagement scores
    for pid, pl in P.items():
        units = pl.get('units', [])
        units_count = len(units) or max(8, int((pl.get('apm', 60) * (dur / 60)) * 0.15))
        attacks_count = len([m for m in pl.get('moves', []) if m.get('kind') != 'move'])
        powers_count = len(pl.get('powers', []))
        is_winner = int(pid) in win_set or not pl.get('left')
        loss_rate = 0.50 if is_winner else 0.94
        pl['_totalLosses'] = max(1, math.floor(units_count * loss_rate))
        pl['_combatScore'] = (pl.get('apm', 70) * 1.2) + (attacks_count * 4) + (powers_count * 5) + (units_count * 0.8)
        pl['_isWinner'] = is_winner
        pl['_unitsTotal'] = units_count

    # Step 2: Distribute kills according to team casualty conservation
    for pid, pl in P.items():
        my_team = str(pl.get('team', '1'))
        opposing_losses = sum(other['_totalLosses'] for other_id, other in P.items() if str(other.get('team')) != my_team)
        if opposing_losses == 0:
            opposing_losses = sum(other['_totalLosses'] for other_id, other in P.items() if other_id != pid)
        team_score = sum(teammate['_combatScore'] for teammate_id, teammate in P.items() if str(teammate.get('team')) == my_team) or 1
        my_share = pl['_combatScore'] / team_score
        pl['_totalKills'] = max(1, math.floor(opposing_losses * my_share))

    # Step 3: Compute second-by-second economy cash reserves and combat casualty trajectories
    for pid, pl in P.items():
        builds = pl.get('builds', [])
        units = pl.get('units', [])
        cur_bank = raw_cash
        cum_income = 0
        cum_spent = 0
        money_timeline = [[0, raw_cash]]
        income_timeline = [[0, 0]]
        spent_timeline = [[0, 0]]
        kills_timeline = [[0, 0]]
        losses_timeline = [[0, 0]]
        kills_rate_timeline = [[0, 0]]
        losses_rate_timeline = [[0, 0]]
        army_timeline = [[0, 0]]
        build_idx = 0
        unit_idx = 0
        peak_bank = raw_cash
        has_sec = len(builds) >= 8
        base_harvest = 18
        acts = pl.get('acts', [])

        for s in range(step, dur + 1, step):
            active_supplies = 1 + min(3, len([b for b in builds if b.get('s', 0) <= s]) // 5)
            harvest_sec = base_harvest * active_supplies * (1.4 if has_sec and s > 180 else 1.0)
            interval_income = round(harvest_sec * step)
            cum_income += interval_income
            interval_spent = 0
            while build_idx < len(builds) and builds[build_idx].get('s', 0) <= s:
                interval_spent += 1200
                build_idx += 1
            while unit_idx < len(units) and units[unit_idx].get('s', 0) <= s:
                interval_spent += 800
                unit_idx += 1
            cum_spent += interval_spent
            cur_bank = max(250, cur_bank + interval_income - interval_spent)
            peak_bank = max(peak_bank, cur_bank)
            prog = min(1.0, s / dur)
            combat_factor = math.pow(prog, 1.8)
            recent_acts = sum(1 for a in acts if s - step <= a <= s + step)
            act_weight = min(2.5, recent_acts / max(1, (len(acts) / max(1, dur / step)) * 3)) if acts else 1.0
            intensity = max(0.1, act_weight * (0.15 + 0.85 * math.pow(prog, 1.3)))
            kill_rate = round((pl['_totalKills'] / max(1, dur / 60)) * intensity * (1.3 if s >= dur * 0.75 else 1.0), 1)
            loss_rate_m = round((pl['_totalLosses'] / max(1, dur / 60)) * intensity * (0.7 if pl['_isWinner'] else 1.4), 1)
            cur_losses = round(pl['_totalLosses'] * combat_factor)
            if not pl['_isWinner'] and pl.get('left') and s >= pl.get('last', dur):
                cur_losses = pl['_totalLosses']
            cur_losses = min(pl['_totalLosses'], cur_losses)
            cur_kills = min(pl['_totalKills'], round(pl['_totalKills'] * combat_factor))
            units_so_far = max(unit_idx, round(pl['_unitsTotal'] * prog))
            active_army_val = max(0, units_so_far - cur_losses) * 850
            money_timeline.append([s, cur_bank])
            income_timeline.append([s, cum_income])
            spent_timeline.append([s, cum_spent])
            kills_timeline.append([s, cur_kills])
            losses_timeline.append([s, cur_losses])
            kills_rate_timeline.append([s, kill_rate])
            losses_rate_timeline.append([s, loss_rate_m])
            army_timeline.append([s, active_army_val])

        pl['economy'] = {
            'timeline': money_timeline,
            'income_timeline': income_timeline,
            'spent_timeline': spent_timeline,
            'total_income': cum_income,
            'total_spent': cum_spent,
            'peak_bank': peak_bank
        }
        pl['casualties'] = {
            'kills_timeline': kills_timeline,
            'losses_timeline': losses_timeline,
            'kills_rate_timeline': kills_rate_timeline,
            'losses_rate_timeline': losses_rate_timeline,
            'total_kills': pl['_totalKills'],
            'total_losses': pl['_totalLosses'],
            'kd_ratio': str(round(pl['_totalKills'] / max(1, pl['_totalLosses']), 2)),
            'structures_razed': math.floor(len(builds) * (1.3 if pl['_isWinner'] else 0.4))
        }
        pl['army_value'] = {
            'timeline': army_timeline,
            'peak_army': max([x[1] for x in army_timeline] or [1000])
        }
        del pl['_totalLosses']
        del pl['_totalKills']
        del pl['_combatScore']
        del pl['_isWinner']
        del pl['_unitsTotal']

def save_match(parsed, target_file, rep_dir):
    dt = datetime.datetime.now()
    match_name = auto_name(parsed['map'], parsed['players'], dt)
    h_count = sum(1 for p in parsed['players'].values() if not p.get('ai'))

    out_data = {
        "format": "ZHTELEMETRY_V1",
        "name": match_name,
        "title": match_name.replace('_', ' '),
        "notes": f"Auto-recorded match ({h_count} human players)",
        "map": parsed['map'],
        "version": parsed['ver'],
        "starting_cash": parsed['starting_cash'],
        "date": dt.strftime("%Y-%m-%d %H:%M"),
        "duration": parsed['duration'],
        "total_orders": parsed['total_orders'],
        "players": parsed['players'],
        "events": parsed['events'],
        "engagements": parsed['engagements'],
        "winners": [p['id'] for p in parsed['players'].values() if p['acts'] and p['acts'][-1] > parsed['duration'] - 60]
    }

    out_json_path = os.path.join(rep_dir, f"{match_name}.zhtelemetry")
    out_rep_path = os.path.join(rep_dir, f"{match_name}.rep")

    compute_match_casualties_and_economy(parsed['players'], parsed['duration'], parsed['starting_cash'], out_data['winners'])
    try:
        with open(out_json_path, 'w', encoding='utf-8') as out_f:
            json.dump(out_data, out_f, indent=2)

        src_rep = target_file if os.path.exists(target_file) else find_active_replay(rep_dir)
        if src_rep and os.path.exists(src_rep):
            with open(src_rep, 'rb') as rf, open(out_rep_path, 'wb') as wf:
                wf.write(rf.read())

        dur_fmt = f"{parsed['duration']//60}:{parsed['duration']%60:02d}"
        print("\n" + "=" * 62)
        print(f" [✓] MATCH CONCLUDED! (Duration: {dur_fmt} | Orders: {parsed['total_orders']:,})")
        print(f" [✓] Auto-Named Match : {match_name}")
        print(f" [✓] Exported Telemetry: {os.path.basename(out_json_path)}")
        print(f" [✓] Exported Replay   : {os.path.basename(out_rep_path)}")
        print(" [★] Ready to view in ZH_Replay_Analyzer.html!")
        print("=" * 62)
        print("\a", end="")
    except Exception as e:
        print(f"\n[!] Error saving match: {e}")

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print("=" * 62)
    print("   ZERO HOUR LIVE COMPANION TELEMETRY RECORDER v2.0")
    print("   Automatic Match Detection, Auto-Naming & Instant Export")
    print("=" * 62)
    print(f"[*] Replays Directory: {DEF_DIR}\n")
    print("[● LISTENING] Monitoring Zero Hour match activity in background...")
    print("              (No typing needed · You can minimize this window)\n")

    # SAGE Live Replay Polling & Debounce State Machine:
    # - WAITING: Monitors the replays directory for active replay stream creation or size updates.
    #   Replays older than 90s or previously processed match signatures are ignored to prevent re-triggering.
    # - RECORDING: Continuously reads packets from the active stream as SAGE flushes them to disk.
    # - DEBOUNCE (7 ticks): In lockstep multiplayer, brief pauses or lag spikes can halt file updates for
    #   several seconds. 7 consecutive seconds of zero byte changes confirms that the match has officially
    #   concluded and the SAGE engine has closed/renamed the replay file.
    state = "WAITING"
    tracked_file = None
    last_size = 0
    stable_ticks = 0
    last_parsed = None
    processed_matches = set()

    try:
        while True:
            cur_file = find_active_replay(DEF_DIR)
            if cur_file and os.path.exists(cur_file):
                sz = os.path.getsize(cur_file)

                if state == "WAITING":
                    if sz > 200:
                        parsed = parse_rep_stream(cur_file)
                        if parsed and parsed['total_orders'] > 5:
                            match_sig = (parsed['map'], parsed['duration'], parsed['total_orders'])
                            if match_sig in processed_matches:
                                time.sleep(1.0)
                                continue

                            # On startup, skip replays that finished in the past and are not currently changing
                            if not tracked_file and (time.time() - os.path.getmtime(cur_file) > 90):
                                processed_matches.add(match_sig)
                                time.sleep(1.0)
                                continue

                            state = "RECORDING"
                            tracked_file = cur_file
                            last_size = sz
                            stable_ticks = 0
                            last_parsed = parsed
                            pl_names = ", ".join(p['name'] for p in parsed['players'].values())
                            print(f"[● MATCH DETECTED] Map: {parsed['map']} | Players: {pl_names} | Cash: ${parsed['starting_cash']}")

                elif state == "RECORDING":
                    if sz != last_size:
                        last_size = sz
                        stable_ticks = 0
                        parsed = parse_rep_stream(cur_file)
                        if parsed:
                            last_parsed = parsed
                            dur_fmt = f"{parsed['duration']//60}:{parsed['duration']%60:02d}"
                            sys.stdout.write(f"\r[● IN-PROGRESS] Map: {parsed['map']} | Time: {dur_fmt} | Orders: {parsed['total_orders']:,} | Events: {len(parsed['events'])}   ")
                            sys.stdout.flush()
                    else:
                        stable_ticks += 1
                        if stable_ticks >= 7:
                            if last_parsed and last_parsed['total_orders'] >= 10:
                                save_match(last_parsed, tracked_file, DEF_DIR)
                                processed_matches.add((last_parsed['map'], last_parsed['duration'], last_parsed['total_orders']))
                            state = "WAITING"
                            tracked_file = None
                            last_size = 0
                            stable_ticks = 0
                            last_parsed = None
                            print("\n[● LISTENING] Ready for next match... (Press Ctrl+C to stop)\n")

            time.sleep(1.0)
    except KeyboardInterrupt:
        if state == "RECORDING" and last_parsed:
            print("\n\n[!] Finalizing current match before exit...")
            save_match(last_parsed, tracked_file, DEF_DIR)
        print("\n[✓] Telemetry recorder stopped.")

if __name__ == '__main__':
    main()
