import math
import os, sys, time, struct, json, datetime, re

def get_default_replay_dir():
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

CMD_NAMES = {
    1040:"Special power", 1041:"Power @ location", 1042:"Power @ target",
    1043:"Rally point", 1044:"General promotion", 1045:"Upgrade",
    1047:"Queue unit", 1049:"Build structure", 1050:"Build wall",
    1052:"Sell", 1059:"Attack target", 1060:"Force attack",
    1061:"Bombard ground", 1068:"Move order", 1069:"Attack-move",
    1093:"Surrender / Left"
}
SZ = {0:4, 1:4, 2:1, 3:4, 4:4, 5:4, 6:12, 7:8, 8:16, 9:4, 10:2}

def find_active_replay(rep_dir):
    zero_rep = os.path.join(rep_dir, "00000000.rep")
    if os.path.exists(zero_rep):
        return zero_rep
    reps = [os.path.join(rep_dir, f) for f in os.listdir(rep_dir) if f.lower().endswith('.rep')]
    return max(reps, key=os.path.getmtime) if reps else None

def parse_rep_stream(path):
    if not os.path.exists(path) or os.path.getsize(path) < 40: return None
    try:
        with open(path, 'rb') as f:
            magic = f.read(6)
            if magic != b'GENREP': return None
            f.seek(28)
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

            tokens = {}
            for item in hdr.split(';'):
                if '=' in item:
                    k, v = item.split('=', 1)
                    tokens[k] = v
            map_name = tokens.get('M', '?').split('/')[-1]
            cash = tokens.get('SC', '10000')

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
                        'ai': s[0] == 'C'
                    })

            players = {}
            events = []
            engagements = []
            max_t = 0
            total_orders = 0
            buildings = []

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
                    if sz is None: {bad := True}; break
                    for _ in range(n):
                        buf = f.read(sz)
                        if len(buf) < sz: {bad := True}; break
                        if t == 6: args.append((t, struct.unpack('<ff', buf[:8])))
                        elif sz >= 4: args.append((t, struct.unpack('<I', buf[:4])[0]))
                if bad or c == 1095 or c < 1000 or c > 1999: continue

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
                        'ai': p_meta.get('ai', False),
                        'acts': [],
                        'cmd': {},
                        'cat': {'Micro': 0, 'Macro': 0, 'Selection': 0, 'Powers': 0},
                        'builds': [],
                        'units': [],
                        'powers': [],
                        'rally': [],
                        'moves': []
                    }

                p = players[pn]
                p['acts'].append(sec)
                cmd_name = CMD_NAMES.get(c, f"Cmd {c}")
                p['cmd'][cmd_name] = p['cmd'].get(cmd_name, 0) + 1

                if c in (1047, 1049, 1050, 1052, 1043, 1045, 1046): p['cat']['Macro'] += 1
                elif c in (1044, 1040, 1041, 1042): p['cat']['Powers'] += 1
                elif c <= 1005 or c == 1058 or (1006 <= c <= 1035): p['cat']['Selection'] += 1
                else: p['cat']['Micro'] += 1

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

                elif c == 1052:
                    events.append({'s': sec, 'p': pn, 'type': 'Sell', 'txt': "Sold structure (credited)"})

                elif c in (1040, 1041, 1042, 1044):
                    p['powers'].append(sec)
                    txt = f"{cmd_name} @ ({round(loc[0])}, {round(loc[1])})" if loc else cmd_name
                    events.append({'s': sec, 'p': pn, 'type': 'Power', 'txt': txt})

                elif loc and c in (1059, 1060, 1061, 1068, 1069, 1070):
                    kind = "attack" if c in (1059, 1060) else "bombard" if c == 1061 else "attackMove" if c == 1069 else "move"
                    p['moves'].append({'s': sec, 'x': loc[0], 'y': loc[1], 'kind': kind, 'cmd': c})

            dur = max_t / 15
            for p in players.values():
                p['n'] = len(p['acts'])
                p['last'] = p['acts'][-1] if p['acts'] else 0
                p['apm'] = round(p['n'] / max(1, p['last'] / 60))

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
    dur = dur or 600
    try:
        raw_cash = int(raw_cash_str or 10000)
    except:
        raw_cash = 10000
    win_set = set(win_list or [])
    step = max(10, math.ceil(dur / 40))

    # Step 1: Losses & Combat Scores
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

    # Step 2: Kills
    for pid, pl in P.items():
        my_team = str(pl.get('team', '1'))
        opposing_losses = sum(other['_totalLosses'] for other_id, other in P.items() if str(other.get('team')) != my_team)
        if opposing_losses == 0:
            opposing_losses = sum(other['_totalLosses'] for other_id, other in P.items() if other_id != pid)
        team_score = sum(teammate['_combatScore'] for teammate_id, teammate in P.items() if str(teammate.get('team')) == my_team) or 1
        my_share = pl['_combatScore'] / team_score
        pl['_totalKills'] = max(1, math.floor(opposing_losses * my_share))

    # Step 3: Timelines
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
        army_timeline = [[0, 0]]
        build_idx = 0
        unit_idx = 0
        peak_bank = raw_cash
        has_sec = len(builds) >= 8
        base_harvest = 18

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

        with open(target_file, 'rb') as rf, open(out_rep_path, 'wb') as wf:
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
    print("=" * 62)
    print("   ZERO HOUR LIVE COMPANION TELEMETRY RECORDER v2.0")
    print("   Automatic Match Detection, Auto-Naming & Instant Export")
    print("=" * 62)
    print(f"[*] Replays Directory: {DEF_DIR}\n")
    print("[● LISTENING] Monitoring Zero Hour match activity in background...")
    print("              (No typing needed · You can minimize this window)\n")

    state = "WAITING"
    tracked_file = None
    last_size = 0
    stable_ticks = 0
    last_parsed = None

    try:
        while True:
            cur_file = find_active_replay(DEF_DIR)
            if cur_file and os.path.exists(cur_file):
                sz = os.path.getsize(cur_file)

                if state == "WAITING":
                    if sz > 200:
                        parsed = parse_rep_stream(cur_file)
                        if parsed and parsed['total_orders'] > 5:
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
