"""
enc.py  ─  Full Neon Comet Wave on Every Line
══════════════════════════════════════════════════════════════════════
Every line uses the same GLITTER ENGINE:
  • Each character appears as a warm-white flash
  • Fades through yellow → grey → its own base colour
  • Creates the neon comet trail on ALL text, not just module ID

EXACT COLOURS (pixel-sampled from 30fps video):
  Line                    Flash peak        Rested base
  ──────────────────────  ────────────────  ──────────────────
  "Premium"               (223,235,217)  →  (218,145,140)  salmon-red
  "Access Required."      (223,235,217)  →  (183,183,183)  light grey
  "Here is Your..."       (223,235,217)  →  ( 55, 40,141)  deep blue
  Module ID numbers       (223,235,217)  →  ( 55, 40,131)  blue-purple
  "Module Title:"         (223,235,217)  →  (215,213,221)  white
  "cythonenc"             (223,235,217)  →  (215,213,221)  white
  "Share it with..."      (223,235,217)  →  ( 96, 79,180)  violet
  "Pay Him for..."        (223,235,217)  →  ( 65, 13,104)  deep violet

INSTALL:  pip install colorama   (optional, Windows only)
RUN:      python enc.py
"""

import sys, time, math, random, os

try:
    import colorama; colorama.init()
except ImportError:
    pass


# ── ANSI helpers ──────────────────────────────────────────────────────────────
def rgb(r, g, b, text):
    r,g,b = max(0,min(255,int(r))), max(0,min(255,int(g))), max(0,min(255,int(b)))
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"

def cursor_up(n):
    if n > 0: sys.stdout.write(f"\x1b[{n}A")

def erase_line():
    sys.stdout.write("\x1b[2K\r")

def hide_cursor(): sys.stdout.write("\x1b[?25l"); sys.stdout.flush()
def show_cursor(): sys.stdout.write("\x1b[?25h"); sys.stdout.flush()
def clear():       os.system("cls" if os.name == "nt" else "clear")


# ══════════════════════════════════════════════════════════════════════════════
#  GLITTER ENGINE — the neon comet trail
# ══════════════════════════════════════════════════════════════════════════════

# Universal flash peak colour (warm white — same for every line)
FLASH = (223, 235, 217)

def make_keyframes(base_r, base_g, base_b):
    """
    Build the fade keyframe curve for a given base (resting) colour.
    All lines start from the same warm-white flash and arrive at their own colour.

    Curve shape from 30fps analysis:
      0.00s  warm-white        (223, 235, 217)
      0.25s  warm yellow-white (210, 215, 190)  ← always same
      0.50s  neutral grey      (180, 178, 180)  ← always same
      0.75s  grey blending     towards base
      1.10s  near-base         ~70% of base
      1.60s  fully rested      = base
    """
    fr, fg, fb = FLASH
    # Two mid-stop colours are universal (measured from video)
    mid1 = (210, 215, 190)   # t=0.25
    mid2 = (180, 178, 180)   # t=0.50
    # Blend from mid2 into the base colour for the tail
    def lerp(a, b, t): return a + (b - a) * t
    mid3 = (lerp(mid2[0], base_r, 0.30),
            lerp(mid2[1], base_g, 0.30),
            lerp(mid2[2], base_b, 0.30))  # t=0.75

    return [
        (0.00, FLASH),
        (0.25, mid1),
        (0.50, mid2),
        (0.75, mid3),
        (1.10, (lerp(mid2[0], base_r, 0.70),
                lerp(mid2[1], base_g, 0.70),
                lerp(mid2[2], base_b, 0.70))),
        (1.60, (base_r, base_g, base_b)),
    ]


def glitter_color(elapsed, keyframes):
    """Interpolate along keyframes for given elapsed seconds."""
    if elapsed <= keyframes[0][0]:  return keyframes[0][1]
    if elapsed >= keyframes[-1][0]: return keyframes[-1][1]
    for i in range(len(keyframes)-1):
        t0, c0 = keyframes[i]
        t1, c1 = keyframes[i+1]
        if t0 <= elapsed <= t1:
            frac = (elapsed - t0) / (t1 - t0)
            # Ease-out: fast early fade, slow tail
            frac = 1 - (1 - frac) ** 1.8
            return tuple(c0[j] + (c1[j] - c0[j]) * frac for j in range(3))
    return keyframes[-1][1]


def wave_type(text, base_r, base_g, base_b,
              char_delay=0.045, wrap=80,
              fade_extra=0.5, refresh_hz=0.04):
    """
    Type `text` with the neon comet wave effect.
    Works for any single-line or multi-line text, any base colour.

      base_r/g/b  : the resting colour this line fades to
      char_delay  : seconds per character
      wrap        : terminal wrap width
      fade_extra  : seconds of continued fading after last char
      refresh_hz  : repaint interval during fading
    """
    kf = make_keyframes(base_r, base_g, base_b)
    typed = []          # [(char, time_typed), ...]
    lines_on_screen = 0

    hide_cursor()

    for ch in text:
        now = time.time()
        typed.append((ch, now))

        if lines_on_screen > 0:
            cursor_up(lines_on_screen)

        t_now = time.time()
        lines_on_screen = 0
        pos = 0
        while pos < len(typed):
            chunk = typed[pos : pos + wrap]
            erase_line()
            for c, t in chunk:
                cr, cg, cb = glitter_color(t_now - t, kf)
                sys.stdout.write(rgb(cr, cg, cb, c))
            if pos + wrap < len(typed):
                sys.stdout.write("\n")
                lines_on_screen += 1
            pos += wrap

        sys.stdout.flush()
        time.sleep(char_delay)

    # Post-type fade continuation
    deadline = time.time() + fade_extra
    while time.time() < deadline:
        cursor_up(lines_on_screen)
        t_now = time.time()
        lines_on_screen = 0
        pos = 0
        while pos < len(typed):
            chunk = typed[pos : pos + wrap]
            erase_line()
            for c, t in chunk:
                cr, cg, cb = glitter_color(t_now - t, kf)
                sys.stdout.write(rgb(cr, cg, cb, c))
            if pos + wrap < len(typed):
                sys.stdout.write("\n")
                lines_on_screen += 1
            pos += wrap
        sys.stdout.flush()
        time.sleep(refresh_hz)

    sys.stdout.write("\n")
    sys.stdout.flush()
    show_cursor()


def wave_type_mixed(segments, wrap=80, char_delay=0.045,
                    fade_extra=0.5, refresh_hz=0.04):
    """
    Type a line with MIXED colours using the wave — each segment has its own
    base colour. E.g. "Premium" salmon + " Access Required." grey.

      segments : list of (text, base_r, base_g, base_b)
    """
    # Flatten all chars with their individual keyframes
    full_text = "".join(s[0] for s in segments)
    # Build per-char keyframes list
    char_kfs = []
    for text, br, bg, bb in segments:
        kf = make_keyframes(br, bg, bb)
        for _ in text:
            char_kfs.append(kf)

    typed = []          # [(char, time_typed, keyframes), ...]
    lines_on_screen = 0

    hide_cursor()

    for i, ch in enumerate(full_text):
        now = time.time()
        typed.append((ch, now, char_kfs[i]))

        if lines_on_screen > 0:
            cursor_up(lines_on_screen)

        t_now = time.time()
        lines_on_screen = 0
        pos = 0
        while pos < len(typed):
            chunk = typed[pos : pos + wrap]
            erase_line()
            for c, t, kf in chunk:
                cr, cg, cb = glitter_color(t_now - t, kf)
                sys.stdout.write(rgb(cr, cg, cb, c))
            if pos + wrap < len(typed):
                sys.stdout.write("\n")
                lines_on_screen += 1
            pos += wrap

        sys.stdout.flush()
        time.sleep(char_delay)

    # Post-type fade
    deadline = time.time() + fade_extra
    while time.time() < deadline:
        cursor_up(lines_on_screen)
        t_now = time.time()
        lines_on_screen = 0
        pos = 0
        while pos < len(typed):
            chunk = typed[pos : pos + wrap]
            erase_line()
            for c, t, kf in chunk:
                cr, cg, cb = glitter_color(t_now - t, kf)
                sys.stdout.write(rgb(cr, cg, cb, c))
            if pos + wrap < len(typed):
                sys.stdout.write("\n")
                lines_on_screen += 1
            pos += wrap
        sys.stdout.flush()
        time.sleep(refresh_hz)

    sys.stdout.write("\n")
    sys.stdout.flush()
    show_cursor()


def gen_module_id(length=160):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN SEQUENCE
# ══════════════════════════════════════════════════════════════════════════════
def main():
    clear()
    time.sleep(0.25)

    # ── "Premium Access Required." — mixed wave ───────────────────────────────
    # "Premium" fades to salmon-red, rest fades to light grey
    wave_type_mixed([
        ("Premium",           218, 145, 140),   # salmon-red
        (" Access Required.", 183, 183, 183),    # light grey
    ], char_delay=0.065, fade_extra=0.4)

    sys.stdout.write("\n"); sys.stdout.flush()

    # ── "Here is Your Module ID:" — fades to deep blue ───────────────────────
    wave_type(
        "Here is Your Module ID:",
        55, 40, 141,          # deep blue
        char_delay=0.048,
        fade_extra=0.2,
    )

    # ── Module ID — fades to blue-purple, slower per-char ────────────────────
    wave_type(
        gen_module_id(160),
        55, 40, 131,          # blue-purple
        char_delay=0.020,
        wrap=66,
        fade_extra=0.8,
    )

    sys.stdout.write("\n"); sys.stdout.flush()

    # ── "Module Title:" — fades to white ─────────────────────────────────────
    wave_type(
        "Module Title:",
        215, 213, 221,        # white
        char_delay=0.052,
        fade_extra=0.2,
    )

    # ── "cythonenc" — fades to white ─────────────────────────────────────────
    wave_type(
        "cythonenc",
        215, 213, 221,        # white
        char_delay=0.065,
        fade_extra=0.35,
    )

    sys.stdout.write("\n"); sys.stdout.flush()

    # ── "Share it with @rejerk..." — fades to violet ──────────────────────────
    wave_type(
        "Share it with @rejerk To get Premium Of this tool.",
        96, 79, 180,          # violet
        char_delay=0.052,
        fade_extra=0.3,
    )

    # ── "Pay Him for access..." — fades to deep violet ───────────────────────
    wave_type(
        "Pay Him for access of this tool.",
        65, 13, 104,          # deep violet
        char_delay=0.052,
        fade_extra=0.5,
    )

    # ── Blinking cursor ───────────────────────────────────────────────────────
    for _ in range(1):
        sys.stdout.write(rgb(65, 13, 104, "█"))
        sys.stdout.flush()
        time.sleep(0.38)
        sys.stdout.write("\b \b")
        sys.stdout.flush()
        time.sleep(0.28)
    sys.stdout.write("\n"); sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        show_cursor()
        sys.stdout.write("\n")
