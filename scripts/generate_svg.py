import requests

USERNAME = "Shubham270206"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
data = requests.get(url).json()

# API returns flat list of days: [{"date": "...", "count": 0, "level": 0}, ...]
days_flat = data["contributions"]

# Group into weeks of 7
weeks = [days_flat[i:i+7] for i in range(0, len(days_flat), 7)]

svg_blocks = ""
svg_particles = ""

x_offset = 30
y_offset_start = 20
block_index = 0
total_commits = 0

for week in weeks:
    y_offset = y_offset_start

    for day in week:
        count = day["count"]
        total_commits += count

        if count == 0:
            color = "#1a1f2e"
        elif count <= 2:
            color = "#1e4620"
        elif count <= 5:
            color = "#2ea043"
        elif count <= 10:
            color = "#39d353"
        else:
            color = "#56e368"

        delay = block_index * 0.045
        anim_dur = 9

        svg_blocks += f'''  <rect x="{x_offset}" y="{y_offset}" width="10" height="10" fill="{color}" rx="1">
    <animate attributeName="opacity" values="1;1;1;0;0" keyTimes="0;0.6;0.7;0.72;1" dur="{anim_dur}s" begin="{delay}s" repeatCount="indefinite"/>
    <animate attributeName="fill" values="{color};{color};#ffffff;{color}" keyTimes="0;0.65;0.68;0.7" dur="{anim_dur}s" begin="{delay}s" repeatCount="indefinite"/>
  </rect>\n'''

        if count > 0:
            directions = [(-6, -8), (6, -8), (-8, 2), (8, 2)]
            p_colors = [color, "#56e368", "#ffffff", color]
            for i, (dx, dy) in enumerate(directions):
                p_delay = delay + 5.8
                svg_particles += f'''  <rect x="{x_offset+4}" y="{y_offset+4}" width="3" height="3" fill="{p_colors[i]}" opacity="0">
    <animate attributeName="x" values="{x_offset+4};{x_offset+4+dx}" dur="0.5s" begin="{p_delay}s" repeatCount="indefinite"/>
    <animate attributeName="y" values="{y_offset+4};{y_offset+4+dy}" dur="0.5s" begin="{p_delay}s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.1;0.2;0.6;1" dur="0.5s" begin="{p_delay}s" repeatCount="indefinite"/>
  </rect>\n'''

        y_offset += 12
        block_index += 1

    x_offset += 12

total_width = x_offset + 30
player_end_x = x_offset - 10
xp_fill_width = min(total_commits, 500) / 500 * 300
level = min(total_commits // 50 + 1, 99)

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

<circle cx="80" cy="6" r="1" fill="white" opacity="0.6"/>
<circle cx="200" cy="4" r="1" fill="white" opacity="0.4"/>
<circle cx="340" cy="8" r="1.2" fill="white" opacity="0.7"/>
<circle cx="470" cy="3" r="1" fill="white" opacity="0.5"/>
<circle cx="590" cy="7" r="1" fill="white" opacity="0.6"/>

{svg_blocks}
{svg_particles}

<rect x="0" y="104" width="{total_width}" height="18" fill="url(#dirt)"/>
<rect x="0" y="100" width="{total_width}" height="5" fill="#4a7c3f"/>
<rect x="0" y="99" width="{total_width}" height="2" fill="#5a9e4f"/>

<g filter="url(#glow)">
  <rect width="10" height="8" fill="#c68642" y="-4" rx="1">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
  </rect>
  <rect width="2" height="2" fill="#3d2b1f" x="2" y="-3">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
  </rect>
  <rect width="2" height="2" fill="#3d2b1f" x="6" y="-3">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
  </rect>
  <rect width="10" height="6" fill="#3d5eff" y="4">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
  </rect>
  <rect width="4" height="5" fill="#4a3728" y="10">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
  </rect>
  <rect width="4" height="5" fill="#3d2b1f" x="6" y="10">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
  </rect>
  <rect width="2" height="14" fill="#7c5c3c" x="11" y="-2">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
    <animateTransform attributeName="transform" type="rotate" values="0 12 5;-35 12 5;0 12 5" dur="0.35s" repeatCount="indefinite"/>
  </rect>
  <rect width="8" height="3" fill="#aaaaaa" x="10" y="-3">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear"><mpath href="#pp"/></animateMotion>
    <animateTransform attributeName="transform" type="rotate" values="0 12 5;-35 12 5;0 12 5" dur="0.35s" repeatCount="indefinite"/>
  </rect>
</g>

<path id="pp" d="M 16 88 L {player_end_x} 88" fill="none"/>

<rect x="0" y="178" width="{total_width}" height="42" fill="#0d1117" opacity="0.95"/>
<rect x="0" y="178" width="{total_width}" height="1" fill="#30363d"/>

<text x="20" y="196" fill="#39d353" font-size="9" font-family="'Courier New', monospace" font-weight="bold">&#x26CF; MINING COMMITS...</text>
<text x="20" y="212" fill="#8b949e" font-size="8" font-family="'Courier New', monospace">BLOCKS MINED: {total_commits:,}  |  SHUBHAM270206  |  LVL {level}</text>

<text x="{total_width - 340}" y="193" fill="#57ff57" font-size="8" font-family="'Courier New', monospace" font-weight="bold">XP</text>
<rect x="{total_width - 318}" y="183" width="304" height="12" fill="#1f2937" rx="2"/>
<rect x="{total_width - 318}" y="183" width="304" height="12" fill="none" stroke="#30363d" stroke-width="1" rx="2"/>
<rect x="{total_width - 318}" y="183" width="{xp_fill_width:.1f}" height="12" fill="url(#xpGrad)" rx="2"/>

</svg>"""

with open("assets/minecraft-commits.svg", "w") as f:
    f.write(svg)

print(f"✅ SVG generated! Total commits: {total_commits:,} | Level: {level} | Blocks: {block_index}")