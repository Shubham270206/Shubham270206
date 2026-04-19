import requests

USERNAME = "Shubham270206"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
data = requests.get(url).json()
days_flat = data["contributions"]
weeks = [days_flat[i:i+7] for i in range(0, len(days_flat), 7)]

total_commits = 0
block_grid = []   # (x, y, color, count)

x_offset = 30
for week in weeks:
    y_offset = 16
    for day in week:
        count = day["count"]
        total_commits += count
        if count == 0:   color = "#1a1f2e"
        elif count <= 2: color = "#1e4620"
        elif count <= 5: color = "#2ea043"
        elif count <= 10:color = "#39d353"
        else:            color = "#56e368"
        block_grid.append((x_offset, y_offset, color, count))
        y_offset += 12
    x_offset += 12

total_width = x_offset + 30
active_blocks = [(bx,by,c,n) for (bx,by,c,n) in block_grid if n > 0]
total_active = len(active_blocks)

# Each block gets 1.2s: 0.8s mining (cracks) + 0.4s break
BLOCK_DUR = 1.2
MINE_DUR  = 0.8   # cracking phase
BREAK_DUR = 0.4   # shatter phase
total_anim = total_active * BLOCK_DUR + 2  # +2s pause at end before loop

# ── crack line sets (3 stages) drawn as SVG path relative to block origin ──
CRACK_STAGES = [
    # stage 1 – hairline
    "M2,5 L8,5 M5,2 L5,8",
    # stage 2 – more cracks
    "M1,4 L5,2 L9,5 M2,7 L6,9 L8,6 M4,1 L4,4 M7,7 L7,10",
    # stage 3 – heavy damage
    "M0,3 L4,1 L8,4 L10,7 M1,6 L3,9 L7,10 M5,0 L5,4 M3,5 L0,7 M8,3 L10,2 M6,6 L9,8",
]

svg_static  = ""   # permanent dark grid
svg_mine    = ""   # animated green blocks + cracks + shatter
svg_player  = ""   # Steve parts

# ── static dark grid ──
for (bx,by,color,count) in block_grid:
    svg_static += f'  <rect x="{bx}" y="{by}" width="10" height="10" fill="{color}" rx="1"/>\n'

# ── per active-block animations ──
for i,(bx,by,color,count) in enumerate(active_blocks):
    t0      = i * BLOCK_DUR          # block animation starts
    t_break = t0 + MINE_DUR          # shatter moment
    t_end   = t0 + BLOCK_DUR         # block fully gone
    D       = total_anim             # total cycle

    def kf(*pairs):
        """Build keyTimes and values strings from (time, value) pairs, normalized to D."""
        times  = ";".join(f"{p[0]/D:.4f}" for p in pairs)
        values = ";".join(str(p[1])       for p in pairs)
        return times, values

    # ── green block: visible → flash white → gone ──
    op_kt, op_v = kf((0,0),(max(t0-0.01,0),0),(t0,1),(t_break-0.05,1),(t_break,1),(t_break+0.05,0),(D,0))
    fl_kt, fl_v = kf((0,color),(t0,color),(t_break-0.1,color),(t_break-0.05,"#ffffff"),(t_break,"#ffffff"),(t_break+0.05,color),(D,color))

    svg_mine += f'''  <rect x="{bx}" y="{by}" width="10" height="10" fill="{color}" rx="1">
    <animate attributeName="opacity" values="{op_v}" keyTimes="{op_kt}" dur="{D}s" begin="0s" repeatCount="indefinite"/>
    <animate attributeName="fill"    values="{fl_v}" keyTimes="{fl_kt}" dur="{D}s" begin="0s" repeatCount="indefinite"/>
  </rect>\n'''

    # ── crack overlays (3 stages during MINE_DUR) ──
    stage_dur = MINE_DUR / 3
    for si, crack_d in enumerate(CRACK_STAGES):
        cs = t0 + si * stage_dur
        ce = t0 + (si+1) * stage_dur
        c_kt, c_v = kf((0,0),(max(cs-0.01,0),0),(cs,1),(ce,1),(ce+0.01,0),(D,0))
        svg_mine += f'''  <path transform="translate({bx},{by})" d="{crack_d}"
        stroke="#000000" stroke-width="0.8" fill="none" stroke-linecap="round" opacity="0">
    <animate attributeName="opacity" values="{c_v}" keyTimes="{c_kt}" dur="{D}s" begin="0s" repeatCount="indefinite"/>
  </path>\n'''

    # ── shatter: 8 fragments fly outward ──
    import math
    for fi in range(8):
        angle = fi * 45
        rad   = math.radians(angle)
        fx0   = bx + 3 + (fi % 3) * 2
        fy0   = by + 3 + (fi // 3) * 2
        fx1   = bx + 5 + math.cos(rad) * 14
        fy1   = by + 5 + math.sin(rad) * 14
        sz    = 3 if fi % 2 == 0 else 2
        fcolor = color if fi % 3 != 2 else "#ffffff"

        f_op_kt, f_op_v = kf((0,0),(max(t_break-0.01,0),0),(t_break,1),(t_break+BREAK_DUR*0.7,1),(t_break+BREAK_DUR,0),(D,0))
        f_x_kt,  f_x_v  = kf((0,fx0),(t_break,fx0),(t_break+BREAK_DUR,fx1),(D,fx1))
        f_y_kt,  f_y_v  = kf((0,fy0),(t_break,fy0),(t_break+BREAK_DUR,fy1),(D,fy1))

        svg_mine += f'''  <rect x="{fx0}" y="{fy0}" width="{sz}" height="{sz}" fill="{fcolor}" opacity="0">
    <animate attributeName="opacity" values="{f_op_v}" keyTimes="{f_op_kt}" dur="{D}s" begin="0s" repeatCount="indefinite"/>
    <animate attributeName="x"       values="{f_x_v}"  keyTimes="{f_x_kt}"  dur="{D}s" begin="0s" repeatCount="indefinite"/>
    <animate attributeName="y"       values="{f_y_v}"  keyTimes="{f_y_kt}"  dur="{D}s" begin="0s" repeatCount="indefinite"/>
  </rect>\n'''

# ── player path: walk to each active block ──
if active_blocks:
    segments = " ".join(f"L {bx+5} 90" for (bx,by,c,n) in active_blocks)
    player_path = f"M 16 90 {segments} L {total_width-20} 90"
else:
    player_path = f"M 16 90 L {total_width-20} 90"

# ── Steve parts helper ──
def steve(attrs, extra=""):
    return f'''  <rect {attrs}>
    <animateMotion dur="{total_anim}s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
    {extra}
  </rect>'''

xp_fill  = min(total_commits,500)/500*300
level    = min(total_commits//50+1,99)

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

<!-- Sky -->
<rect width="100%" height="100%" fill="url(#sky)"/>
<circle cx="80"  cy="6"  r="1"   fill="white" opacity="0.6"/>
<circle cx="200" cy="4"  r="1"   fill="white" opacity="0.4"/>
<circle cx="340" cy="8"  r="1.2" fill="white" opacity="0.7"/>
<circle cx="470" cy="3"  r="1"   fill="white" opacity="0.5"/>
<circle cx="590" cy="7"  r="1"   fill="white" opacity="0.6"/>

<!-- Static grid -->
{svg_static}

<!-- Mining animations: cracks + shatter + fragments -->
{svg_mine}

<!-- Ground -->
<rect x="0" y="104" width="{total_width}" height="18" fill="url(#dirt)"/>
<rect x="0" y="100" width="{total_width}" height="5"  fill="#4a7c3f"/>
<rect x="0" y="99"  width="{total_width}" height="2"  fill="#5a9e4f"/>

<!-- Steve -->
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

<path id="pp" d="{player_path}" fill="none"/>

<!-- HUD -->
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

print(f"✅ Done! Commits: {total_commits} | Active blocks: {total_active} | Level: {level} | Cycle: {total_anim:.1f}s")