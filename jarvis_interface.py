"""
jarvis_interface.py - animated sci-fi interface for your Jarvis assistant.

Install:  pip install pygame

Use from your assistant:
    from jarvis_interface import Jarvisinterface
    interface = Jarvis_Interface()
    interface.set_state("listening")   # idle | listening | thinking | speaking
    interface.log("Opening YouTube...")
    interface.run()                    # blocks - must be called on the MAIN thread
"""
import math #module for mathematical functions
import queue
import random #to generate rando values from given parameters wherever needed
import time 

import pygame

# state -> colour of the interface
STATE_COLORS = {
    "idle":      (30, 120, 255), #blue
    "listening": (0, 190, 255),   # cyan
    "thinking":  (255, 190, 40),  # amber
    "speaking":  (120, 220, 255), # bright ice blue
}

BOOT_LINES = [
    "INITIALIZING DESKTOP SYSTEM...... ACTIVE",
    "LOADING LOCAL DATABASE........ COMPLETE",
    "CALIBRATING SPEECH RECOGNITION........ ONLINE",
    "SYNTHESIZING VOICE ENGINE........... READY",
    "ESTABLISHING LANGUAGE MODEL........ SECURE",
    "ALL SYSTEMS NOMINAL.WAITING FOR WAKE WORD.",
]

MAX_LOGS = 7   # how many command/reply lines will ne showed on the screen

def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def dim(color, f):
    return tuple(int(c * f) for c in color)


def draw_arc(surface, color, center, radius, start, end, width=3):
    """Smooth arc drawn as a polyline (angles in radians)."""
    steps = max(8, int(abs(end - start) * radius / 4))
    pts = [
        (center[0] + math.cos(start + (end - start) * i / steps) * radius,
         center[1] + math.sin(start + (end - start) * i / steps) * radius)
        for i in range(steps + 1)
    ]
    pygame.draw.lines(surface, color, False, pts, width)


def make_glow(size=400):
    """Grayscale radial gradient; tinted + added to the screen each frame."""
    glow = pygame.Surface((size, size))
    glow.fill((0, 0, 0))
    half = size // 2
    for r in range(half, 0, -2):
        v = int(255 * (1 - r / half) ** 2.2)
        pygame.draw.circle(glow, (v, v, v), (half, half), r)
    return glow


class Jarvis_interface:
    def __init__(self, title="J.A.R.V.I.S  V27.10", size=(1000, 620)):
        self.title = title
        self.size = size
        self.state = "idle"
        self.running = True
        self._log_q = queue.Queue()
        self.logs = []
        self.timer_end = None   # time when the countdown finishes (if nothing that means no timer is set up)

        # ring definitions: (radius as fraction of base, width, speed, [(start, length), ...])
        rng = random.Random(7)
        self.rings = []
        for frac, width, speed in [(0.42, 3, 0.6), (0.55, 2, -0.4),
                                   (0.68, 4, 0.25), (0.80, 2, -0.7),
                                   (0.95, 3, 0.15)]:
            arcs = []
            angle = rng.random() * math.tau
            while angle < math.tau * 2 - 1:
                length = rng.uniform(0.4, 1.4)
                arcs.append((angle, length))
                angle += length + rng.uniform(0.3, 0.9)
            self.rings.append((frac, width, speed, arcs))

    # ---------- thread-safe API (call these from your assistant thread) ----------
    def set_state(self, state):
        if state in STATE_COLORS:
            self.state = state

    def log(self, text):
        self._log_q.put(str(text))

    def start_countdown(self, seconds):
        self.timer_end = time.time() + seconds

    def stop_countdown(self):
        self.timer_end = None

    def close(self):
        self.running = False

    # ---------- main loop (MAIN thread only) ----------
    def run(self):
        pygame.init()
        screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        pygame.display.set_caption("JARVIS")
        clock = pygame.time.Clock()

        mono = "menlo,consolas,couriernew,monospace"
        font = pygame.font.SysFont(mono, 15)
        big = pygame.font.SysFont(mono, 34, bold=True)
        glow_src = make_glow()

        color = STATE_COLORS["idle"]
        t0 = time.time()
        bars = [0.3] * 72

        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    self.running = False

            while not self._log_q.empty():
                self.logs.append(self._log_q.get())
            self.logs = self.logs[-MAX_LOGS:]

            t = time.time() - t0
            w, h = screen.get_size()
            cx, cy = int(w * 0.62), h // 2
            base = min(w * 0.38, h * 0.46)

            # smooth colour change between states
            color = lerp_color(color, STATE_COLORS[self.state], 0.08)
            speed_mul = {"idle": 1.0, "listening": 1.6, "thinking": 3.5, "speaking": 1.8}[self.state]

            # ---- background + grid ----
            screen.fill((2, 8, 20))
            grid = dim(color, 0.10)
            for x in range(0, w, 40):
                pygame.draw.line(screen, grid, (x, 0), (x, h))
            for y in range(0, h, 40):
                pygame.draw.line(screen, grid, (0, y), (w, y))

            # ---- glowing core ----
            pulse = 1 + 0.12 * math.sin(t * (2 + speed_mul))
            if self.state == "speaking":
                pulse += 0.12 * abs(math.sin(t * 14))
            gsize = int(base * 1.1 * pulse)
            glow = pygame.transform.smoothscale(glow_src, (gsize, gsize))
            glow.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(glow, (cx - gsize // 2, cy - gsize // 2), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(screen, (235, 250, 255), (cx, cy), int(base * 0.07 * pulse))

            # ---- rotating arc rings ----
            for frac, width, speed, arcs in self.rings:
                r = base * frac
                rot = t * speed * speed_mul
                for start, length in arcs:
                    draw_arc(screen, color, (cx, cy), r, start + rot, start + rot + length, width)
                pygame.draw.circle(screen, dim(color, 0.18), (cx, cy), int(r), 1)

            # ---- tick-mark ring ----
            for i in range(120):
                a = i / 120 * math.tau - t * 0.1
                long = i % 10 == 0
                r1, r2 = base * 1.04, base * (1.11 if long else 1.07)
                pygame.draw.line(screen, dim(color, 0.8 if long else 0.4),
                                 (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                                 (cx + math.cos(a) * r2, cy + math.sin(a) * r2), 2 if long else 1)

            # ---- audio-style radial bars (react to state) ----
            for i in range(len(bars)):
                if self.state == "speaking":
                    target = random.uniform(0.2, 1.0)
                elif self.state == "listening":
                    target = 0.25 + 0.2 * abs(math.sin(t * 3 + i * 0.4))
                else:
                    target = 0.12 + 0.05 * math.sin(t + i)
                bars[i] = lerp(bars[i], target, 0.3)
                a = i / len(bars) * math.tau
                r1 = base * 0.30
                r2 = r1 + bars[i] * base * 0.10
                pygame.draw.line(screen, dim(color, 0.9),
                                 (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                                 (cx + math.cos(a) * r2, cy + math.sin(a) * r2), 2)

            # ---- left panel: title, boot text, logs ----
            screen.blit(big.render(self.title, True, color), (30, 25))
            pygame.draw.line(screen, color, (30, 72), (w * 0.34, 72), 1)

            chars_shown = int(t * 45)  # typewriter effect
            y = 90
            for line in BOOT_LINES:
                if chars_shown <= 0:
                    break
                txt = line[:chars_shown]
                chars_shown -= len(line)
                screen.blit(font.render(txt, True, dim(color, 0.85)), (30, y))
                y += 22

            # fixed layout: the STATE line and log area never move
            log_top = h - 30 - 22 * MAX_LOGS
            state_y = log_top - 30
            screen.blit(font.render(f"STATE: {self.state.upper()}", True, color), (30, state_y))
            y = log_top
            for line in self.logs:
                screen.blit(font.render("> " + line[:60], True, dim(color, 0.9)), (30, y))
                y += 22

            # ---- study timer countdown (between the boot text and the STATE line) ----
            if self.timer_end is not None:
                left = int(self.timer_end - time.time())
                if left <= 0:
                    self.timer_end = None
                else:
                    hrs, rem = divmod(left, 3600)
                    mins, secs = divmod(rem, 60)
                    text = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins:02d}:{secs:02d}"
                    boot_bottom = 90 + 22 * len(BOOT_LINES)
                    top = (boot_bottom + state_y) // 2 - 30
                    screen.blit(font.render("STUDY TIMER", True, dim(color, 0.85)), (30, top))
                    screen.blit(big.render(text, True, color), (30, top + 24))

            # ---- corner brackets ----
            m, L = 12, 40
            for (x0, y0, dx, dy) in [(m, m, 1, 1), (w - m, m, -1, 1),
                                     (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
                pygame.draw.lines(screen, color, False,
                                  [(x0 + dx * L, y0), (x0, y0), (x0, y0 + dy * L)], 3)

            # ---- scanline sweep ----
            sy = int((t * 120) % h)
            sweep = pygame.Surface((w, 3), pygame.SRCALPHA)
            sweep.fill((*color, 40))
            screen.blit(sweep, (0, sy))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


# Quick demo: run this file directly to preview the interface
if __name__ == "__main__":
    import threading

    interface = Jarvis_interface()

    def demo():
        time.sleep(5)
        while interface.running:
            for state, msg in [("listening", "Listening for wake word..."),
                               ("thinking", "Processing therequest..."),
                               ("speaking", "Opening YouTube, sir."),
                               ("idle", "Standing by.")]:
                interface.set_state(state)
                interface.log(msg)
                time.sleep(3)

    threading.Thread(target=demo, daemon=True).start()
    interface.run()