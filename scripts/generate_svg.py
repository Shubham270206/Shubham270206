import requests, math

USERNAME = "Shubham270206"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
data = requests.get(url).json()
days_flat = data["contributions"]
weeks = [days_flat[i:i+7] for i in range(0, len(days_flat), 7)]

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

total_width = x_offset + 30
active_blocks = [(bx,by,c,n) for (bx,by,c,n) in block_grid if n > 0]
total_active  = len(active_blocks)

# Timing constants
TRAVEL_SPEED = 0.015   # seconds per pixel when walking fast
MINE_DUR     = 0.9     # seconds to mine each block (crack phase)
BREAK_DUR    = 0.3     # seconds for shatter

# Build timeline: for each active block, compute EXACT time Steve arrives
# Steve starts at x=16, walks to each block's x position
timeline = []   # (bx, by, color, t_arrive, t_break, t_done)

current_x = 16
current_t = 0.0

for (bx, by, color, count) in active_blocks:
    dist      = abs(bx + 5 - current_x)
    travel_t  = dist * TRAVEL_SPEED
    t_arrive  = current_t + travel_t
    t_break   = t_arrive + MINE_DUR
    t_done    = t_break + BREAK_DUR
    timeline.append((bx, by, color, t_arrive, t_break, t_done))
    current_x = bx + 5
    current_t = t_done

# Final walk to end
dist_end    = abs(total_width - 20 - current_x)
total_anim  = current_t + dist_end * TRAVEL_SPEED + 1.0  # +1s pause

D = total_anim  # full cycle duration

def kf(*pairs):
    """(time, value) → keyTimes and values strings, times normalized to D"""
    times  = ";".join(f"{min(p[0]/D,1):.5f}" for p in pairs)
    values = ";".join(str(p[1]) for p in pairs)
    return times, values

# ── Static dark grid ──
svg_static = ""
for (bx,by,color,count) in block_grid:
    svg_static += f'  <rect x="{bx}" y="{by}" width="10" height="10" fill="{color}" rx="1"/>\n'

# ── Per-block mining animations ──
CRACK_PATHS = [
    "M2,5 L8,5 M5,2 L5,8",
    "M1,4 L5,2 L9,5 M2,7 L6,9 L8,6 M4,1 L4,4 M7,7 L7,10",
    "M0,3 L4,1 L8,4 L10,7 M1,6 L3,9 L7,10 M5,0 L5,4 M3,5 L0,7 M8,3 L10,2 M6,6 L9,8",
]

svg_mine = ""

for (bx, by, color, t_arrive, t_break, t_done) in timeline:
    eps = 0.001

    # Green block: appears when cycle starts, disappears on break
    op_kt, op_v = kf(
        (0,           1),
        (t_break,     1),
        (t_break+eps, 0),
        (D,           0),
    )
    fl_kt, fl_v = kf(
        (0,                  color),
        (t_break - 0.08,     color),
        (t_break - 0.04,     "#ffffff"),
        (t_break,            "#ffffff"),
    )
    svg_mine += f'''  <rect x="{bx}" y="{by}" width="10" height="10" fill="{color}" rx="1">
    <animate attributeName="opacity" values="{op_v}" keyTimes="{op_kt}" dur="{D:.3f}s" repeatCount="indefinite"/>
    <animate attributeName="fill"    values="{fl_v}" keyTimes="{fl_kt}" dur="{D:.3f}s" repeatCount="indefinite"/>
  </rect>\n'''

    # Crack overlays — 3 stages evenly across MINE_DUR
    stage = MINE_DUR / 3
    for si, crack_d in enumerate(CRACK_PATHS):
        cs = t_arrive + si * stage
        ce = t_arrive + (si + 1) * stage
        c_kt, c_v = kf(
            (0,       0),
            (cs-eps,  0),
            (cs,      1),
            (ce,      1),
            (ce+eps,  0),
            (t_break, 0),
            (D,       0),
        )
        svg_mine += f'''  <path transform="translate({bx},{by})" d="{crack_d}"
        stroke="#000000" stroke-width="0.9" fill="none" stroke-linecap="round" opacity="0">
    <animate attributeName="opacity" values="{c_v}" keyTimes="{c_kt}" dur="{D:.3f}s" repeatCount="indefinite"/>
  </path>\n'''

    # Shatter: 8 fragments burst outward at t_break
    for fi in range(8):
        angle  = fi * 45
        rad    = math.radians(angle)
        fx0    = bx + 3 + (fi % 3)
        fy0    = by + 3 + (fi // 3)
        fx1    = bx + 5 + math.cos(rad) * 16
        fy1    = by + 5 + math.sin(rad) * 16
        sz     = 3 if fi % 2 == 0 else 2
        fcolor = color if fi % 3 != 2 else "#ffffff"

        f_op_kt, f_op_v = kf(
            (0,                  0),
            (t_break - eps,      0),
            (t_break,            1),
            (t_break+BREAK_DUR*0.6, 1),
            (t_done,             0),
            (D,                  0),
        )
        f_x_kt, f_x_v = kf(
            (0,      fx0),
            (t_break,fx0),
            (t_done, fx1),
            (D,      fx1),
        )
        f_y_kt, f_y_v = kf(
            (0,      fy0),
            (t_break,fy0),
            (t_done, fy1),
            (D,      fy1),
        )
        svg_mine += f'''  <rect x="{fx0:.1f}" y="{fy0:.1f}" width="{sz}" height="{sz}" fill="{fcolor}" opacity="0">
    <animate attributeName="opacity" values="{f_op_v}" keyTimes="{f_op_kt}" dur="{D:.3f}s" repeatCount="indefinite"/>
    <animate attributeName="x"       values="{f_x_v}"  keyTimes="{f_x_kt}"  dur="{D:.3f}s" repeatCount="indefinite"/>
    <animate attributeName="y"       values="{f_y_v}"  keyTimes="{f_y_kt}"  dur="{D:.3f}s" repeatCount="indefinite"/>
  </rect>\n'''

# ── Player path with variable speed ──
# Build path keyPoints + keyTimes for animateMotion
# Total path length = sum of all segments
path_points = [(16, 90)]
for (bx,by,color,t_arrive,t_break,t_done) in timeline:
    path_points.append((bx+5, 90))   # arrive
    path_points.append((bx+5, 90))   # stay while mining
path_points.append((total_width-20, 90))

# Build SVG path string
path_d = f"M {path_points[0][0]} {path_points[0][1]}"
for (px,py) in path_points[1:]:
    path_d += f" L {px} {py}"

# Compute keyTimes for animateMotion (must match cumulative path length ratio)
# Use actual pixel distances for keyPoints, time-based for keyTimes
total_path_len = sum(
    abs(path_points[i+1][0]-path_points[i][0])
    for i in range(len(path_points)-1)
)

# Build parallel keyTimes + keyPoints for animateMotion
motion_times  = [0.0]
motion_kp     = [0.0]
cum_len = 0.0
cum_time = 0.0

pt_idx = 0
current_x = 16
current_t  = 0.0

for (bx,by,color,t_arrive,t_break,t_done) in timeline:
    # walk to block
    dist = abs(bx+5 - current_x)
    cum_len  += dist
    cum_time  = t_arrive
    motion_times.append(cum_time / D)
    motion_kp.append(cum_len / total_path_len)

    # stay at block (mining)
    motion_times.append(t_done / D)
    motion_kp.append(cum_len / total_path_len)  # same position

    current_x  = bx+5
    current_t  = t_done

# walk to end
dist = abs(total_width-20 - current_x)
cum_len  += dist
motion_times.append(1.0)
motion_kp.append(1.0)

# Clamp all values to [0,1]
motion_times = [min(max(v,0),1) for v in motion_times]
motion_kp    = [min(max(v,0),1) for v in motion_kp]

kt_str = ";".join(f"{v:.5f}" for v in motion_times)
kp_str = ";".join(f"{v:.5f}" for v in motion_kp)

def steve(attrs, extra=""):
    return f'''  <rect {attrs}>
    <animateMotion dur="{D:.3f}s" repeatCount="indefinite" calcMode="linear"
        keyTimes="{kt_str}" keyPoints="{kp_str}">
      <mpath href="#pp"/>
    </animateMotion>
    {extra}
  </rect>'''

xp_fill = min(total_commits,500)/500*300
level   = min(total_commits//50+1,99)

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
    <stop offset="0%" stop-color="#1a3a5c"/>
    <stop offset="100%" stop-color="#0d1117"/>
  </linearGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="xpGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#57ff57"/>
    <stop offset="100%" stop-color="#00c800"/>
  </linearGradient>
</defs>

<rect width="100%" height="100%" fill="url(#sky)"/>
<circle cx="80"  cy="6"  r="1"   fill="white" opacity="0.6"/>
<circle cx="200" cy="4"  r="1"   fill="white" opacity="0.4"/>
<circle cx="340" cy="8"  r="1.2" fill="white" opacity="0.7"/>
<circle cx="470" cy="3"  r="1"   fill="white" opacity="0.5"/>
<circle cx="590" cy="7"  r="1"   fill="white" opacity="0.6"/>

{svg_static}
{svg_mine}

<rect x="0" y="104" width="{total_width}" height="18" fill="url(#dirt)"/>
<rect x="0" y="100" width="{total_width}" height="5"  fill="#4a7c3f"/>
<rect x="0" y="99"  width="{total_width}" height="2"  fill="#5a9e4f"/>

<g filter="url(#glow)">
  {steve('width="10" height="8" fill="#c68642" y="-4" rx="1"')}
  {steve('width="2"  height="2" fill="#3d2b1f" x="2" y="-3"')}
  {steve('width="2"  height="2" fill="#3d2b1f" x="6" y="-3"')}
  {steve('width="10" height="6" fill="#3d5eff" y="4"')}
  {steve('width="4"  height="5" fill="#4a3728" y="10"')}
  {steve('width="4"  height="5" fill="#3d2b1f" x="6" y="10"')}
  {steve('width="2"  height="14" fill="#7c5c3c" x="11" y="-2"',
    '<animateTransform attributeName="transform" type="rotate" values="0 12 5;-40 12 5;0 12 5" dur="0.25s" repeatCount="indefinite"/>')}
  {steve('width="8"  height="3"  fill="#aaaaaa" x="10" y="-3"',
    '<animateTransform attributeName="transform" type="rotate" values="0 12 5;-40 12 5;0 12 5" dur="0.25s" repeatCount="indefinite"/>')}
</g>

<path id="pp" d="{path_d}" fill="none"/>

<rect x="0" y="178" width="{total_width}" height="42" fill="#0d1117" opacity="0.95"/>
<rect x="0" y="178" width="{total_width}" height="1"  fill="#30363d"/>
<text x="20" y="196" fill="#39d353" font-size="9" font-family="'Courier New', monospace" font-weight="bold">&#x26CF; MINING COMMITS...</text>
<text x="20" y="212" fill="#8b949e" font-size="8" font-family="'Courier New', monospace">BLOCKS MINED: {total_commits:,}  |  SHUBHAM270206  |  LVL {level}</text>
<text x="{total_width-340}" y="193" fill="#57ff57" font-size="8" font-family="'Courier New', monospace" font-weight="bold">XP</text>
<rect x="{total_width-318}" y="183" width="304" height="12" fill="#1f2937" rx="2"/>
<rect x="{total_width-318}" y="183" width="304" height="12" fill="none" stroke="#30363d" stroke-width="1" rx="2"/>
<rect x="{total_width-318}" y="183" width="{xp_fill:.1f}" height="12" fill="url(#xpGrad)" rx="2"/>
</svg>"""

with open("assets/minecraft-commits.svg", "w") as f:
    f.write(svg)

print(f"✅ Done! Commits: {total_commits} | Active: {total_active} | Cycle: {D:.1f}s")