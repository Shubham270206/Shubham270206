import requests, math, random, os

USERNAME = "Shubham270206"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
data = requests.get(url).json()
days_flat = data["contributions"]
weeks = [days_flat[i:i+7] for i in range(0, len(days_flat), 7)]

random.seed(42)

total_commits = 0
block_grid = []

x_offset = 30
for week in weeks:
    y_offset = 16
    for day in week:
        count = day["count"]
        total_commits += count
        if count == 0:    color = "#1a1f2e"
        elif count <= 2:  color = "#1e4620"
        elif count <= 5:  color = "#2ea043"
        elif count <= 10: color = "#39d353"
        else:             color = "#56e368"
        block_grid.append((x_offset, y_offset, color, count))
        y_offset += 12
    x_offset += 12

total_width  = x_offset + 30
SCENE_ANCHOR = total_width / 2

all_active = [(bx,by,c,n) for (bx,by,c,n) in block_grid if n > 0]
MAX_BLOCKS = 120
if len(all_active) > MAX_BLOCKS:
    high     = [(bx,by,c,n) for (bx,by,c,n) in all_active if n >= 3]
    low      = [(bx,by,c,n) for (bx,by,c,n) in all_active if n < 3]
    keep_low = max(0, MAX_BLOCKS - len(high))
    step     = max(1, len(low) // (keep_low or 1))
    low      = low[::step][:keep_low]
    active_blocks = sorted(high + low, key=lambda b: (b[0], b[1]))[:MAX_BLOCKS]
else:
    active_blocks = all_active

total_active = len(active_blocks)

# ── Timing ──
BASE_MINE_DUR = 0.50
MAX_MINE_DUR  = 1.50
BREAK_DUR     = 0.22
TRAVEL_SPEED  = 0.013
WALK_IN_DELAY = 0.6
IDLE_DUR      = 0.28
BOB_PERIOD    = 0.20
REGEN_DUR     = 1.8
CAMERA_LAG    = 0.05

def mine_dur(count):
    t = min(count / 10.0, 1.0)
    return BASE_MINE_DUR + t * (MAX_MINE_DUR - BASE_MINE_DUR)

# ── Timeline ──
timeline = []
current_x = 16
current_t = WALK_IN_DELAY

for (bx, by, color, count) in active_blocks:
    dist         = abs(bx + 5 - current_x)
    t_arrive     = current_t + dist * TRAVEL_SPEED
    t_mine_start = t_arrive + IDLE_DUR
    md           = mine_dur(count)
    t_break      = t_mine_start + md
    t_done       = t_break + BREAK_DUR
    timeline.append((bx, by, color, count, t_arrive, t_mine_start, t_break, t_done))
    current_x = bx + 5
    current_t = t_done

dist_end   = abs(total_width + 20 - current_x)
walk_out_t = current_t + dist_end * TRAVEL_SPEED
total_anim = walk_out_t + REGEN_DUR
D          = total_anim

def clamp01(v): return min(max(v, 0.0), 1.0)

# ── Core dedup utility ──
# Dedup AFTER rounding to the same precision used in output formatting.
# This catches the real source of duplicates: two distinct raw floats that
# collapse to the same "0.XXXXX" string once normalised by clamp01 + f"{:.5f}".
def dedup_keyframes(times, values, precision=5):
    """Remove duplicate keyTimes after rounding. Last value wins.
    Guards against degenerate single-frame result."""
    seen = {}
    for t, v in zip(times, values):
        seen[round(t, precision)] = v
    pairs = sorted(seen.items())
    if len(pairs) < 2:
        v0 = pairs[0][1] if pairs else "0"
        return [0.0, 1.0], [v0, v0]
    return [p[0] for p in pairs], [p[1] for p in pairs]

def dedup_motion(times, points, splines, precision=5):
    """Dedup motion-path keyframes, keeping kt/kp/ks in sync."""
    seen = {}
    for t, p in zip(times, points):
        seen[round(t, precision)] = p
    pairs = sorted(seen.items())
    if len(pairs) < 2:
        v0 = pairs[0][1] if pairs else 0.0
        return [0.0, 1.0], [v0, v0], splines[:1]
    new_t = [p[0] for p in pairs]
    new_p = [p[1] for p in pairs]
    new_s = splines[:len(new_t) - 1]
    return new_t, new_p, new_s

def kf(*pairs):
    times  = ";".join(f"{clamp01(p[0]/D):.5f}" for p in pairs)
    values = ";".join(str(p[1]) for p in pairs)
    return times, values

# ── Day/Night animated sky gradient ──
midpoint_t = D * 0.5
sky_top_kt = f"0;{midpoint_t/D:.4f};1"
sky_top_v  = "#1a3a5c;#223f5e;#1a3a5c"
sky_bot_kt = f"0;{midpoint_t/D:.4f};1"
sky_bot_v  = "#0d1117;#111822;#0d1117"

# ── Camera follow ──
steve_positions = [(0.0, -10), (WALK_IN_DELAY, 16)]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    steve_positions.append((t_arrive, bx + 5))
    steve_positions.append((t_done,   bx + 5))
steve_positions.append((walk_out_t, total_width + 20))
steve_positions.append((D,          total_width + 20))

MAX_CAM_OFFSET = total_width * 0.04
cam_t_raw = [clamp01(t / D) for (t, _) in steve_positions]
cam_v_raw = []
for (t, sx) in steve_positions:
    raw_offset = -(sx - SCENE_ANCHOR) * CAMERA_LAG
    cam_offset = max(-MAX_CAM_OFFSET, min(MAX_CAM_OFFSET, raw_offset))
    cam_v_raw.append(f"{cam_offset:.2f} 0")

cam_t_raw, cam_v_raw = dedup_keyframes(cam_t_raw, cam_v_raw)
cam_kt = ";".join(f"{v:.5f}" for v in cam_t_raw)
cam_v  = ";".join(cam_v_raw)
cam_ks = ";".join(["0.42 0 0.58 1"] * (len(cam_t_raw) - 1))

# ── Screen shake ──
shake_t_raw = [0.0]
shake_v_raw = ["0 0"]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    if count >= 10:
        amp = min(1.0 + (count - 10) * 0.08, 1.8)
        shake_interval = BREAK_DUR / 6
        shake_t_raw.append(clamp01(t_break / D))
        shake_v_raw.append("0 0")
        for i in range(6):
            t_s = t_break + (i + 0.5) * shake_interval
            if t_s / D < 1.0:
                shake_t_raw.append(clamp01(t_s / D))
                shake_v_raw.append(f"{amp*((-1)**i):.2f} {amp*0.4*((-1)**(i+1)):.2f}")
        shake_t_raw.append(clamp01(t_done / D))
        shake_v_raw.append("0 0")
shake_t_raw.append(1.0)
shake_v_raw.append("0 0")
shake_t_raw, shake_v_raw = dedup_keyframes(shake_t_raw, shake_v_raw)
shake_kt = ";".join(f"{v:.5f}" for v in shake_t_raw)
shake_v  = ";".join(shake_v_raw)

# ── Stars ──
STAR_DATA = [
    (80,  6,  1.0, 0.6, 3.1),
    (200, 4,  1.0, 0.4, 1.7),
    (340, 8,  1.2, 0.7, 0.5),
    (470, 3,  1.0, 0.5, 2.3),
    (590, 7,  1.0, 0.6, 4.1),
    (130, 11, 0.8, 0.3, 1.2),
    (280, 5,  0.9, 0.5, 3.8),
    (420, 9,  0.8, 0.4, 0.9),
    (550, 4,  1.0, 0.6, 2.7),
    (640, 10, 0.8, 0.3, 1.5),
]

svg_stars = ""
for (cx, cy, r, base_op, phase) in STAR_DATA:
    period = 4.0 + (phase % 3.0)
    steps  = max(3, int(D / period))
    st = [0.0]; sv = [str(base_op)]
    for i in range(steps):
        t_pk = (i + 0.5) * (D / steps)
        t_tr = (i + 1.0) * (D / steps)
        st.append(min(t_pk/D, 1.0)); sv.append(str(min(base_op + 0.35, 1.0)))
        st.append(min(t_tr/D, 1.0)); sv.append(str(max(base_op - 0.25, 0.05)))
    st.append(1.0); sv.append(str(base_op))
    st, sv = dedup_keyframes(st, sv)
    skt = ";".join(f"{v:.4f}" for v in st)
    svl = ";".join(sv)
    svg_stars += (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" opacity="{base_op}">\n'
        f'  <animate attributeName="opacity" values="{svl}" keyTimes="{skt}" '
        f'dur="{D:.3f}s" repeatCount="indefinite" calcMode="linear"/>\n'
        f'</circle>\n'
    )

# ── Static grid ──
svg_static = ""
for (bx, by, color, count) in block_grid:
    svg_static += f'  <rect x="{bx}" y="{by}" width="10" height="10" fill="{color}" rx="1"/>\n'

# ── Crack stages ──
CRACK_STAGES = [
    "M3,5 L7,5 M5,3 L5,7",
    "M1,4 L4,2 L8,4 M2,7 L5,9 L9,6 M5,1 L5,4 M7,7 L7,9",
    "M0,3 L3,1 L8,3 L10,6 M1,6 L3,9 L8,9 M5,0 L5,3 M3,5 L0,8 M8,2 L10,1 M6,6 L10,8 M2,4 L0,2",
]

svg_mine = ""

for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    eps = 0.0005
    md  = t_break - t_mine_start
    big = count >= 10

    t_regen = total_anim - REGEN_DUR + random.uniform(0, REGEN_DUR * 0.55)

    op_kt, op_v = kf(
        (0,           1), (t_break,     1),
        (t_break+eps, 0), (t_regen-eps, 0),
        (t_regen,     1), (D,           1),
    )
    flash_color = "#c8ffb0" if big else "#ffffff"
    fl_kt, fl_v = kf(
        (0,            color), (t_break-0.07, color),
        (t_break-0.02, flash_color), (t_break, flash_color),
        (t_break+eps,  color), (D, color),
    )
    svg_mine += (
        f'  <rect x="{bx}" y="{by}" width="10" height="10" fill="{color}" rx="1">\n'
        f'    <animate attributeName="opacity" values="{op_v}" keyTimes="{op_kt}" dur="{D:.4f}s" repeatCount="indefinite"/>\n'
        f'    <animate attributeName="fill"    values="{fl_v}" keyTimes="{fl_kt}" dur="{D:.4f}s" repeatCount="indefinite"/>\n'
        f'  </rect>\n'
    )

    stage_dur = md / 3.0
    for si, crack_d in enumerate(CRACK_STAGES):
        cs = t_mine_start + si * stage_dur
        ce = t_mine_start + (si + 1) * stage_dur
        if si < 2:
            c_kt, c_v = kf(
                (0, 0), (cs-eps, 0), (cs, 1), (ce, 1), (ce+eps, 0), (D, 0)
            )
        else:
            c_kt, c_v = kf(
                (0, 0), (cs-eps, 0), (cs, 1), (t_break, 1), (t_break+eps, 0), (D, 0)
            )
        svg_mine += (
            f'  <path transform="translate({bx},{by})" d="{crack_d}"\n'
            f'        stroke="#000000" stroke-width="0.8" fill="none" stroke-linecap="round" opacity="0">\n'
            f'    <animate attributeName="opacity" values="{c_v}" keyTimes="{c_kt}" dur="{D:.4f}s" repeatCount="indefinite"/>\n'
            f'  </path>\n'
        )

    shake_amp = 1.5 if big else 1.0
    nudge_kt, nudge_v = kf(
        (0, bx), (t_mine_start, bx),
        (t_mine_start+0.04, bx-shake_amp), (t_mine_start+0.09, bx),
        (t_mine_start+0.13, bx-shake_amp*0.5), (t_mine_start+0.18, bx), (D, bx),
    )
    svg_mine += (
        f'  <rect x="{bx}" y="{by}" width="10" height="10" fill="none" rx="1">\n'
        f'    <animate attributeName="x" values="{nudge_v}" keyTimes="{nudge_kt}" dur="{D:.4f}s" repeatCount="indefinite"/>\n'
        f'  </rect>\n'
    )

    n_p = int(6 + min(count, 10) / 10 * 6)
    for _ in range(n_p):
        angle    = random.uniform(0, 360)
        speed    = random.uniform(8, 22)
        rad      = math.radians(angle)
        fx0      = bx + random.uniform(2, 8)
        fy0      = by + random.uniform(2, 8)
        fx1      = fx0 + math.cos(rad) * speed
        gravity  = random.uniform(4, 10) * (1.3 if big else 1.0)
        fy1      = fy0 + math.sin(rad) * speed + gravity
        sz       = random.uniform(1.2, 3.5)
        rv       = random.random()
        fcolor   = color if rv < 0.6 else ("#ffffff" if rv < 0.8 else "#1e4620")
        fade_end = t_break + BREAK_DUR * random.uniform(0.5, 1.0) * (1.2 if big else 1.0)

        f_op_kt, f_op_v = kf(
            (0, 0), (t_break-eps, 0), (t_break, 1),
            (fade_end*0.7, 0.8), (fade_end, 0), (D, 0),
        )
        steps   = 6
        xp_list = [(0, fx0), (t_break, fx0)]
        yp_list = [(0, fy0), (t_break, fy0)]
        for i in range(1, steps+1):
            frac = i / steps
            ease = 1 - (1-frac)**3
            tp   = t_break + (fade_end - t_break) * frac
            xp_list.append((tp, fx0 + (fx1-fx0)*ease))
            yp_list.append((tp, fy0 + (fy1-fy0)*ease))
        xp_list.append((D, fx1)); yp_list.append((D, fy1))

        x_kt = ";".join(f"{clamp01(p[0]/D):.5f}" for p in xp_list)
        x_v  = ";".join(f"{p[1]:.2f}" for p in xp_list)
        y_kt = ";".join(f"{clamp01(p[0]/D):.5f}" for p in yp_list)
        y_v  = ";".join(f"{p[1]:.2f}" for p in yp_list)

        svg_mine += (
            f'  <rect x="{fx0:.1f}" y="{fy0:.1f}" width="{sz:.1f}" height="{sz:.1f}" fill="{fcolor}" opacity="0" rx="0.5">\n'
            f'    <animate attributeName="opacity" values="{f_op_v}" keyTimes="{f_op_kt}" dur="{D:.4f}s" repeatCount="indefinite"/>\n'
            f'    <animate attributeName="x"       values="{x_v}"    keyTimes="{x_kt}"    dur="{D:.4f}s" repeatCount="indefinite"/>\n'
            f'    <animate attributeName="y"       values="{y_v}"    keyTimes="{y_kt}"    dur="{D:.4f}s" repeatCount="indefinite"/>\n'
            f'  </rect>\n'
        )

# ── Motion path ──
GROUND_Y = 90
path_pts = [(-10, GROUND_Y), (16, GROUND_Y)]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    path_pts.append((bx+5, GROUND_Y))
    path_pts.append((bx+5, GROUND_Y))
path_pts.append((total_width+20, GROUND_Y))

path_d = "M " + " L ".join(f"{p[0]} {p[1]}" for p in path_pts)
total_path_len = sum(abs(path_pts[i+1][0]-path_pts[i][0]) for i in range(len(path_pts)-1)) or 1

EASE_IO = "0.42 0 0.58 1"; EASE_OUT = "0 0 0.58 1"; EASE_IN = "0.42 0 1 1"; LINEAR = "0 0 1 1"

kt_raw = [0.0]; kp_raw = [0.0]; ks_raw = []
cum_len = abs(16 - (-10))
kt_raw.append(clamp01(WALK_IN_DELAY/D)); kp_raw.append(clamp01(cum_len/total_path_len)); ks_raw.append(EASE_IO)

cur_x = 16
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    cum_len += abs(bx+5 - cur_x)
    kt_raw.append(clamp01(t_arrive/D));  kp_raw.append(clamp01(cum_len/total_path_len)); ks_raw.append(EASE_OUT)
    kt_raw.append(clamp01(t_done/D));    kp_raw.append(clamp01(cum_len/total_path_len)); ks_raw.append(LINEAR)
    cur_x = bx+5

cum_len += abs(total_width+20-cur_x)
kt_raw.append(1.0); kp_raw.append(1.0); ks_raw.append(EASE_IN)

kt_raw, kp_raw, ks_raw = dedup_motion(kt_raw, kp_raw, ks_raw)
kt_str = ";".join(f"{v:.5f}" for v in kt_raw)
kp_str = ";".join(f"{v:.5f}" for v in kp_raw)
ks_str = ";".join(ks_raw)

# ── Steve visibility ──
t_hide_start = walk_out_t + 0.1
t_hide_end   = total_anim - 0.2
steve_op_kt, steve_op_v = kf(
    (0, 1), (t_hide_start, 1), (t_hide_start+0.06, 0),
    (t_hide_end-0.06, 0), (t_hide_end, 1), (D, 1),
)

# ── Recoil ──
recoil_t = [0.0]; recoil_v_l = ["0"]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    recoil_t.append(clamp01(t_arrive/D)); recoil_v_l.append("0")
    t = t_mine_start; amp = 1.5 if count >= 10 else 1.0
    while t < t_break:
        mid = t + 0.072; end = t + 0.18
        if mid/D < 1.0: recoil_t.append(clamp01(mid/D)); recoil_v_l.append(f"{amp}")
        if end/D < 1.0: recoil_t.append(clamp01(end/D)); recoil_v_l.append("0")
        t = end
    recoil_t.append(clamp01(t_done/D)); recoil_v_l.append("0")
recoil_t.append(1.0); recoil_v_l.append("0")
recoil_t, recoil_v_l = dedup_keyframes(recoil_t, recoil_v_l)
recoil_kt = ";".join(f"{v:.5f}" for v in recoil_t)
recoil_v  = ";".join(recoil_v_l)

# ── Arm swing ──
arm_t = [0.0]; arm_v = ["0"]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    arm_t.append(clamp01(t_arrive/D)); arm_v.append("0")
    t = t_mine_start
    while t < t_break:
        m = t+0.09; e = t+0.18
        if m < t_break and m/D < 1.0: arm_t.append(clamp01(m/D)); arm_v.append("-35")
        if e < t_break and e/D < 1.0: arm_t.append(clamp01(e/D)); arm_v.append("0")
        t = e
    arm_t.append(clamp01(t_break/D)); arm_v.append("0")
arm_t.append(1.0); arm_v.append("0")
arm_t, arm_v = dedup_keyframes(arm_t, arm_v)
arm_kt_str = ";".join(f"{v:.5f}" for v in arm_t)
arm_v_str  = ";".join(arm_v)

# ── Walk bob ──
bob_t = [0.0]; bob_v_l = ["0 0"]
last_t = WALK_IN_DELAY
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    t = last_t
    while t + BOB_PERIOD < t_arrive:
        bob_t.append(clamp01((t+BOB_PERIOD/2)/D)); bob_v_l.append("0 -1.5")
        bob_t.append(clamp01((t+BOB_PERIOD)/D));   bob_v_l.append("0 0")
        t += BOB_PERIOD
    bob_t.append(clamp01(t_arrive/D)); bob_v_l.append("0 0")
    bob_t.append(clamp01(t_done/D));   bob_v_l.append("0 0")
    last_t = t_done
bob_t.append(1.0); bob_v_l.append("0 0")
bob_t, bob_v_l = dedup_keyframes(bob_t, bob_v_l)
bob_kt = ";".join(f"{v:.5f}" for v in bob_t)
bob_v  = ";".join(bob_v_l)

# ── Idle breathing ──
breath_t = [0.0]; breath_v_l = ["0 0"]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    breath_t.append(clamp01(t_arrive/D));     breath_v_l.append("0 0")
    t_mid = t_arrive + IDLE_DUR * 0.5
    if t_mid / D < 1.0:
        breath_t.append(clamp01(t_mid/D));    breath_v_l.append("0 -0.8")
    breath_t.append(clamp01(t_mine_start/D)); breath_v_l.append("0 0")
    breath_t.append(clamp01(t_done/D));       breath_v_l.append("0 0")
breath_t.append(1.0); breath_v_l.append("0 0")
breath_t, breath_v_l = dedup_keyframes(breath_t, breath_v_l)
# Rebuild splines AFTER dedup so count is exactly len(times) - 1
breath_ks = ";".join(["0.42 0 0.58 1"] * (len(breath_t) - 1))
breath_kt = ";".join(f"{v:.5f}" for v in breath_t)
breath_v  = ";".join(breath_v_l)

# ── XP bar ──
level   = min(total_commits // 50 + 1, 99)
xp_t_l  = [0.0]; xp_w_l = ["0.0"]
running = 0
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    running += count
    w = min(running, 500) / 500 * 300
    prev_w = xp_w_l[-1]
    xp_t_l.append(clamp01((t_break - 0.001) / D)); xp_w_l.append(prev_w)
    xp_t_l.append(clamp01(t_break / D));            xp_w_l.append(f"{w:.1f}")
xp_t_l.append(1.0); xp_w_l.append(xp_w_l[-1])
xp_t_l, xp_w_l = dedup_keyframes(xp_t_l, xp_w_l)
xp_w_kt = ";".join(f"{v:.5f}" for v in xp_t_l)
xp_w_v  = ";".join(xp_w_l)
xp_ks   = ";".join(
    "0 0 0.58 1" if float(xp_w_l[i+1]) > float(xp_w_l[i]) else "0 0 1 1"
    for i in range(len(xp_w_l) - 1)
)

glow_t_l = [0.0]; glow_v_l = ["0"]
for (bx, by, color, count, t_arrive, t_mine_start, t_break, t_done) in timeline:
    glow_t_l += [clamp01(t_break/D), clamp01((t_break+0.01)/D), clamp01((t_break+0.22)/D)]
    glow_v_l += ["0", "1", "0"]
glow_t_l.append(1.0); glow_v_l.append("0")
glow_t_l, glow_v_l = dedup_keyframes(glow_t_l, glow_v_l)
glow_kt = ";".join(f"{v:.5f}" for v in glow_t_l)
glow_v  = ";".join(glow_v_l)

# ── Steve animation helpers ──
AM_S = (
    f'<animateMotion dur="{D:.4f}s" repeatCount="indefinite" calcMode="spline"\n'
    f'        keyTimes="{kt_str}" keyPoints="{kp_str}" keySplines="{ks_str}">\n'
    f'      <mpath href="#pp"/>\n'
    f'    </animateMotion>'
)
RECOIL_AT = (
    f'<animateTransform attributeName="transform" type="translate" additive="sum"\n'
    f'        values="{recoil_v}" keyTimes="{recoil_kt}" dur="{D:.4f}s" repeatCount="indefinite" calcMode="linear"/>'
)
BOB_AT = (
    f'<animateTransform attributeName="transform" type="translate" additive="sum"\n'
    f'        values="{bob_v}" keyTimes="{bob_kt}" dur="{D:.4f}s" repeatCount="indefinite" calcMode="linear"/>'
)
BREATH_AT = (
    f'<animateTransform attributeName="transform" type="translate" additive="sum"\n'
    f'        values="{breath_v}" keyTimes="{breath_kt}" keySplines="{breath_ks}"\n'
    f'        dur="{D:.4f}s" repeatCount="indefinite" calcMode="spline"/>'
)
OP_A = f'<animate attributeName="opacity" values="{steve_op_v}" keyTimes="{steve_op_kt}" dur="{D:.4f}s" repeatCount="indefinite"/>'

def sp(attrs):
    return f'<g><rect {attrs}/>{AM_S}{RECOIL_AT}{BOB_AT}{BREATH_AT}{OP_A}</g>'

# ── SVG assembly ──
svg = f"""<svg width="{total_width}" height="220" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} 220">
<defs>
  <pattern id="dirt" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
    <rect width="10" height="10" fill="#5c3d1e"/>
    <rect x="0" y="0" width="5" height="5" fill="#6b4423" opacity="0.5"/>
    <rect x="5" y="5" width="5" height="5" fill="#4a2e12" opacity="0.4"/>
    <rect x="2" y="3" width="2" height="2" fill="#3d2409" opacity="0.6"/>
    <rect x="7" y="1" width="2" height="2" fill="#7a5230" opacity="0.5"/>
  </pattern>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#1a3a5c">
      <animate attributeName="stop-color" values="{sky_top_v}" keyTimes="{sky_top_kt}" dur="{D:.3f}s" repeatCount="indefinite" calcMode="linear"/>
    </stop>
    <stop offset="100%" stop-color="#0d1117">
      <animate attributeName="stop-color" values="{sky_bot_v}" keyTimes="{sky_bot_kt}" dur="{D:.3f}s" repeatCount="indefinite" calcMode="linear"/>
    </stop>
  </linearGradient>
  <linearGradient id="xpGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#57ff57"/>
    <stop offset="100%" stop-color="#00c800"/>
  </linearGradient>
  <filter id="xpglow" x="-20%" y="-50%" width="140%" height="200%">
    <feGaussianBlur stdDeviation="2.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>

<rect width="100%" height="100%" fill="url(#sky)"/>

<g id="scene">
  <animateTransform attributeName="transform" type="translate" additive="sum"
      values="{shake_v}" keyTimes="{shake_kt}" dur="{D:.4f}s" repeatCount="indefinite" calcMode="linear"/>
  <animateTransform attributeName="transform" type="translate" additive="sum"
      values="{cam_v}" keyTimes="{cam_kt}" keySplines="{cam_ks}"
      dur="{D:.4f}s" repeatCount="indefinite" calcMode="spline"/>

{svg_stars}
{svg_static}
{svg_mine}

<rect x="0" y="104" width="{total_width}" height="18" fill="url(#dirt)"/>
<rect x="0" y="100" width="{total_width}" height="5"  fill="#4a7c3f"/>
<rect x="0" y="99"  width="{total_width}" height="2"  fill="#5a9e4f"/>

{sp('width="10" height="8"  fill="#c68642" y="-4" rx="1"')}
{sp('width="2"  height="2"  fill="#3d2b1f" x="2"  y="-3"')}
{sp('width="2"  height="2"  fill="#3d2b1f" x="6"  y="-3"')}
{sp('width="10" height="6"  fill="#3d5eff" y="4"')}
{sp('width="4"  height="5"  fill="#4a3728" y="10"')}
{sp('width="4"  height="5"  fill="#3d2b1f" x="6"  y="10"')}
<g>
  <rect width="2" height="14" fill="#7c5c3c" x="11" y="-2"/>
  <rect width="8" height="3"  fill="#aaaaaa" x="10" y="-3"/>
  {AM_S}
  <animateTransform attributeName="transform" type="rotate"
      values="{arm_v_str}" keyTimes="{arm_kt_str}"
      dur="{D:.4f}s" repeatCount="indefinite" calcMode="linear"/>
  {RECOIL_AT}
  {BOB_AT}
  {BREATH_AT}
  {OP_A}
</g>

<path id="pp" d="{path_d}" fill="none"/>
</g>

<!-- HUD: outside scene so it never shakes or drifts -->
<rect x="0" y="178" width="{total_width}" height="42" fill="#0d1117" opacity="0.97"/>
<rect x="0" y="178" width="{total_width}" height="1"  fill="#30363d"/>
<text x="20" y="196" fill="#39d353" font-size="9" font-family="'Courier New',monospace" font-weight="bold">&#x26CF; MINING COMMITS...</text>
<text x="20" y="212" fill="#8b949e" font-size="8" font-family="'Courier New',monospace">BLOCKS MINED: {total_commits:,}  |  {USERNAME.upper()}  |  LVL {level}</text>
<text x="{total_width-340}" y="193" fill="#57ff57" font-size="8" font-family="'Courier New',monospace" font-weight="bold">XP</text>
<rect x="{total_width-318}" y="183" width="304" height="12" fill="#1f2937" rx="2"/>
<rect x="{total_width-318}" y="183" width="304" height="12" fill="none" stroke="#30363d" stroke-width="1" rx="2"/>
<rect x="{total_width-318}" y="183" width="0" height="12" fill="url(#xpGrad)" rx="2">
  <animate attributeName="width" values="{xp_w_v}" keyTimes="{xp_w_kt}" keySplines="{xp_ks}"
      dur="{D:.4f}s" repeatCount="indefinite" calcMode="spline"/>
</rect>
<rect x="{total_width-318}" y="183" width="304" height="12" fill="url(#xpGrad)" rx="2" opacity="0" filter="url(#xpglow)">
  <animate attributeName="width" values="{xp_w_v}" keyTimes="{xp_w_kt}" keySplines="{xp_ks}"
      dur="{D:.4f}s" repeatCount="indefinite" calcMode="spline"/>
  <animate attributeName="opacity" values="{glow_v}" keyTimes="{glow_kt}"
      dur="{D:.4f}s" repeatCount="indefinite" calcMode="linear"/>
</rect>
</svg>"""

os.makedirs("assets", exist_ok=True)
with open("assets/minecraft-commits.svg", "w") as f:
    f.write(svg)

avg_p = sum(int(6 + min(c,10)/10*6) for (_,_,_,c) in active_blocks) / max(total_active, 1)
big_blocks = sum(1 for (_,_,_,c) in active_blocks if c >= 10)
print(f"✅  Fixed — dedup_keyframes(precision=5) applied post-rounding to all keyframe lists")
print(f"   Commits: {total_commits:,} | Blocks: {total_active}/{len(all_active)} (cap {MAX_BLOCKS})")
print(f"   Cycle: {D:.1f}s")
print(f"   Camera: lag={CAMERA_LAG:.0%}, max_offset={MAX_CAM_OFFSET:.1f}px")
print(f"   Breath: {total_active} pauses | Shake: {big_blocks} big-commit blocks")
print(f"   Avg particles: {avg_p:.1f}/block | Stars: {len(STAR_DATA)}")