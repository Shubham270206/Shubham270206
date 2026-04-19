import requests
import math

USERNAME = "Shubham270206"

url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}"
data = requests.get(url).json()

weeks = data["contributions"]

svg_blocks = ""
svg_particles = ""

x_offset = 60
y_offset_start = 20

block_index = 0
total_commits = 0

for week in weeks:
    y_offset = y_offset_start

    for day in week["contributionDays"]:
        count = day["contributionCount"]
        total_commits += count

        color = "#1a1f2e"
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

        block_id = f"block{block_index}"
        delay = block_index * 0.045
        anim_dur = 9

        # Main block with fade-out when mined
        svg_blocks += f'''
  <rect id="{block_id}" x="{x_offset}" y="{y_offset}" width="10" height="10" fill="{color}" rx="1">
    <animate attributeName="opacity"
             values="1;1;1;0;0"
             keyTimes="0;0.6;0.7;0.72;1"
             dur="{anim_dur}s"
             begin="{delay}s"
             repeatCount="indefinite"/>
    <animate attributeName="fill"
             values="{color};{color};#ffffff;{color}"
             keyTimes="0;0.65;0.68;0.7"
             dur="{anim_dur}s"
             begin="{delay}s"
             repeatCount="indefinite"/>
  </rect>
'''

        # Particles burst in 4 directions
        if count > 0:
            directions = [(-6, -8), (6, -8), (-8, 2), (8, 2)]
            p_colors = [color, "#56e368", "#ffffff", color]
            for i, (dx, dy) in enumerate(directions):
                p_delay = delay + 5.8
                svg_particles += f'''
  <rect x="{x_offset + 4}" y="{y_offset + 4}" width="3" height="3" fill="{p_colors[i]}" opacity="0">
    <animate attributeName="x"
             values="{x_offset + 4};{x_offset + 4 + dx}"
             dur="0.5s"
             begin="{p_delay}s"
             repeatCount="indefinite"/>
    <animate attributeName="y"
             values="{y_offset + 4};{y_offset + 4 + dy}"
             dur="0.5s"
             begin="{p_delay}s"
             repeatCount="indefinite"/>
    <animate attributeName="opacity"
             values="0;0;1;1;0"
             keyTimes="0;0.1;0.2;0.6;1"
             dur="0.5s"
             begin="{p_delay}s"
             repeatCount="indefinite"/>
  </rect>
'''

        y_offset += 12
        block_index += 1

    x_offset += 12

total_width = x_offset + 20
player_start_x = 46
player_end_x = x_offset - 10

# XP bar fill
xp_fill_width = min(total_commits, 500) / 500 * 300

svg_content = f"""<svg width="{total_width}" height="210" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} 210">
<defs>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&amp;display=swap');
    .pixel {{ font-family: 'Press Start 2P', 'Courier New', monospace; }}
  </style>
  <!-- Dirt ground texture pattern -->
  <pattern id="dirt" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
    <rect width="10" height="10" fill="#5c3d1e"/>
    <rect x="0" y="0" width="5" height="5" fill="#6b4423" opacity="0.5"/>
    <rect x="5" y="5" width="5" height="5" fill="#4a2e12" opacity="0.4"/>
    <rect x="2" y="3" width="2" height="2" fill="#3d2409" opacity="0.6"/>
    <rect x="7" y="1" width="2" height="2" fill="#7a5230" opacity="0.5"/>
  </pattern>
  <!-- Sky gradient -->
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#1a3a5c"/>
    <stop offset="100%" stop-color="#0d1117"/>
  </linearGradient>
  <!-- Glow filter for active player -->
  <filter id="glow">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <!-- XP bar gradient -->
  <linearGradient id="xpGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#57ff57"/>
    <stop offset="100%" stop-color="#00c800"/>
  </linearGradient>
</defs>

<!-- Background -->
<rect width="100%" height="100%" fill="url(#sky)"/>

<!-- Stars -->
<circle cx="100" cy="8" r="1" fill="white" opacity="0.6"/>
<circle cx="230" cy="5" r="1" fill="white" opacity="0.4"/>
<circle cx="380" cy="10" r="1" fill="white" opacity="0.7"/>
<circle cx="510" cy="4" r="1" fill="white" opacity="0.5"/>
<circle cx="650" cy="9" r="1" fill="white" opacity="0.6"/>
<circle cx="780" cy="6" r="1" fill="white" opacity="0.3"/>
<circle cx="880" cy="11" r="1" fill="white" opacity="0.5"/>

<!-- Commit blocks -->
{svg_blocks}

<!-- Particles -->
{svg_particles}

<!-- Ground (dirt) -->
<rect x="0" y="100" width="{total_width}" height="20" fill="url(#dirt)"/>
<!-- Grass top -->
<rect x="0" y="98" width="{total_width}" height="4" fill="#4a7c3f"/>
<rect x="0" y="97" width="{total_width}" height="2" fill="#5a9e4f"/>

<!-- Player (Steve pixel art style - simplified) -->
<g filter="url(#glow)">
  <!-- Body: blue shirt -->
  <rect width="10" height="6" fill="#3d5eff" y="4" rx="0">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
  <!-- Head: skin color -->
  <rect width="10" height="8" fill="#c68642" y="-4" rx="1">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
  <!-- Eyes -->
  <rect width="2" height="2" fill="#3d2b1f" x="2" y="-3" opacity="0">
    <animate attributeName="opacity" values="0;1;1" keyTimes="0;0.001;1" dur="9s" repeatCount="indefinite"/>
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
  <rect width="2" height="2" fill="#3d2b1f" x="6" y="-3" opacity="0">
    <animate attributeName="opacity" values="0;1;1" keyTimes="0;0.001;1" dur="9s" repeatCount="indefinite"/>
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
  <!-- Legs -->
  <rect width="4" height="5" fill="#4a3728" y="10" rx="0">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
  <rect width="4" height="5" fill="#3d2b1f" x="6" y="10" rx="0">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
  <!-- Pickaxe -->
  <rect width="12" height="2" fill="#a0a0a0" x="10" y="0" rx="1">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
    <animateTransform attributeName="transform" type="rotate"
                      values="0 16 2;-30 16 2;0 16 2"
                      dur="0.4s" repeatCount="indefinite"/>
  </rect>
  <rect width="4" height="4" fill="#7c5c3c" x="20" y="-2" rx="0">
    <animateMotion dur="9s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#playerPath"/>
    </animateMotion>
  </rect>
</g>

<!-- Hidden player path -->
<path id="playerPath" d="M {player_start_x} 86 L {player_end_x} 86" fill="none"/>

<!-- HUD Panel bottom -->
<rect x="0" y="170" width="{total_width}" height="40" fill="#0d1117" opacity="0.9"/>
<rect x="0" y="170" width="{total_width}" height="1" fill="#30363d"/>

<!-- Mining text -->
<text x="20" y="187" fill="#39d353" font-size="9" class="pixel" font-family="'Press Start 2P', monospace">
  &#x26CF;&#xFE0E; MINING COMMITS...
</text>

<!-- Total commits counter -->
<text x="20" y="202" fill="#8b949e" font-size="7" class="pixel" font-family="'Courier New', monospace">
  BLOCKS MINED: {total_commits:,}
</text>

<!-- XP Bar label -->
<text x="{total_width - 340}" y="183" fill="#57ff57" font-size="7" class="pixel" font-family="'Courier New', monospace">XP</text>

<!-- XP bar background -->
<rect x="{total_width - 320}" y="174" width="300" height="10" fill="#1f2937" rx="2"/>
<!-- XP bar border -->
<rect x="{total_width - 320}" y="174" width="300" height="10" fill="none" stroke="#30363d" stroke-width="1" rx="2"/>
<!-- XP bar fill -->
<rect x="{total_width - 320}" y="174" width="{xp_fill_width:.1f}" height="10" fill="url(#xpGrad)" rx="2"/>

<!-- Level text -->
<text x="{total_width - 320}" y="202" fill="#8b949e" font-size="7" class="pixel" font-family="'Courier New', monospace">
  SHUBHAM270206 — LEVEL {min(total_commits // 50 + 1, 99)}
</text>

</svg>"""

with open("assets/minecraft-commits.svg", "w") as f:
    f.write(svg_content)

print(f"✅ SVG generated! Total commits tracked: {total_commits:,}")
print(f"   Blocks rendered: {block_index}")
print(f"   Player level: {min(total_commits // 50 + 1, 99)}")