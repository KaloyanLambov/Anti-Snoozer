"""
╔══════════════════════════════════════════════════════════════╗
║           MATH ALARM CLOCK — Single-File Python App          ║
║  Solve math problems to dismiss the alarm. No cheating!      ║
╚══════════════════════════════════════════════════════════════╝

SETUP INSTRUCTIONS
──────────────────
1. Install dependencies:
       pip install pygame

2. (Optional) Add your own alarm sound:
       Place a file named  alarm.wav  (or alarm.mp3) in the
       same folder as this script.
       If no sound file is found, a system beep fallback is used.

3. Run:
       python alarm_clock.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime
import random
import math
import os
import sys
import time as time_module


# ─────────────────────────────────────────────
#  SOUND ENGINE  (pygame › winsound fallback)
# ─────────────────────────────────────────────

class SoundEngine:
    """Handles cross-platform alarm audio with graceful fallbacks."""

    SOUND_FILES = ["alarm.wav", "alarm.mp3", "alarm.ogg"]

    def __init__(self):
        self._pygame_ok  = False
        self._sound_file = None
        self._beep_thread = None
        self._beeping    = False
        self._init_pygame()

    def _init_pygame(self):
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._pygame = pygame
            self._pygame_ok = True

            # Look for a sound file next to the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            for name in self.SOUND_FILES:
                path = os.path.join(script_dir, name)
                if os.path.exists(path):
                    self._sound_file = path
                    break
        except Exception:
            self._pygame_ok = False

    # ── Public API ──────────────────────────────

    def play_loop(self):
        """Start looping alarm sound."""
        if self._pygame_ok and self._sound_file:
            try:
                sound = self._pygame.mixer.Sound(self._sound_file)
                sound.play(loops=-1)          # -1 = loop forever
                return
            except Exception:
                pass

        if self._pygame_ok:
            # Generate a synthesised beep via pygame if no file
            self._start_synth_beep()
            return

        # Last-resort: OS beeps in a background thread
        self._beeping = True
        self._beep_thread = threading.Thread(target=self._os_beep_loop, daemon=True)
        self._beep_thread.start()

    def stop(self):
        """Stop all alarm sounds."""
        self._beeping = False
        if self._pygame_ok:
            try:
                self._pygame.mixer.stop()
            except Exception:
                pass

    # ── Internal helpers ─────────────────────────

    def _start_synth_beep(self):
        """Use pygame to generate a simple synthesised alarm tone."""
        try:
            import numpy as np
            sr = 44100
            duration = 0.4
            t = np.linspace(0, duration, int(sr * duration), False)
            wave = (np.sin(2 * np.pi * 880 * t) * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            sound = self._pygame.sndarray.make_sound(stereo)
            sound.play(loops=-1)
        except Exception:
            # numpy not available — fall back to OS beeps
            self._beeping = True
            self._beep_thread = threading.Thread(target=self._os_beep_loop, daemon=True)
            self._beep_thread.start()

    def _os_beep_loop(self):
        """Platform beep fallback (no external library needed)."""
        while self._beeping:
            try:
                if sys.platform == "win32":
                    import winsound
                    winsound.Beep(880, 400)
                    time_module.sleep(0.2)
                else:
                    # ANSI BEL character — works in most terminals
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                    time_module.sleep(0.6)
            except Exception:
                time_module.sleep(0.6)


# ─────────────────────────────────────────────
#  MATH CHALLENGE ENGINE
# ─────────────────────────────────────────────

class MathChallenge:
    """Generates random arithmetic problems at three difficulty levels."""

    DIFFICULTIES = {
        "Easy":   {"ops": ["+", "-"],          "max_a": 20,  "max_b": 20,  "count": 1},
        "Medium": {"ops": ["+", "-", "×"],     "max_a": 50,  "max_b": 30,  "count": 2},
        "Hard":   {"ops": ["+", "-", "×", "÷"],"max_a": 100, "max_b": 20,  "count": 3},
    }

    def __init__(self, difficulty="Medium"):
        self.difficulty = difficulty

    def generate(self):
        """Return (question_string, answer_int)."""
        cfg = self.DIFFICULTIES[self.difficulty]
        op  = random.choice(cfg["ops"])
        a   = random.randint(2, cfg["max_a"])
        b   = random.randint(2, cfg["max_b"])

        if op == "÷":
            # Guarantee clean integer division
            b = random.randint(2, 12)
            a = b * random.randint(2, cfg["max_b"] // b or 2)
            answer = a // b
        elif op == "×":
            answer = a * b
        elif op == "+":
            answer = a + b
        else:  # "-"
            if b > a:
                a, b = b, a   # keep answer positive
            answer = a - b

        question = f"{a}  {op}  {b}  =  ?"
        return question, answer


# ─────────────────────────────────────────────
#  MATH CHALLENGE WINDOW
# ─────────────────────────────────────────────

class MathWindow(tk.Toplevel):
    """
    Full-screen modal that appears when the alarm fires.
    Cannot be closed until the math problem is solved correctly.
    """

    REQUIRED_CORRECT = 3   # solve this many in a row to dismiss

    def __init__(self, parent, sound_engine: SoundEngine, difficulty: str, on_solved):
        super().__init__(parent)
        self._sound    = sound_engine
        self._engine   = MathChallenge(difficulty)
        self._on_solved = on_solved
        self._correct_streak = 0
        self._current_answer = None
        self._shake_id = None

        self._build_ui()
        self._new_question()

        # Prevent closing via the X button
        self.protocol("WM_DELETE_WINDOW", self._deny_close)
        self.grab_set()   # block interaction with main window

    # ── Build UI ────────────────────────────────

    def _build_ui(self):
        self.title("⚠  WAKE UP — Solve to Dismiss")
        self.configure(bg="#0d0d14")
        self.attributes("-topmost", True)
        self.state("zoomed") if sys.platform == "win32" else self.attributes("-fullscreen", True)
        self.resizable(False, False)

        # ── Outer centred frame ──
        outer = tk.Frame(self, bg="#0d0d14")
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # ── Alarm banner ──
        tk.Label(
            outer, text="⏰  ALARM RINGING",
            font=("Courier New", 22, "bold"),
            fg="#ff4455", bg="#0d0d14"
        ).pack(pady=(0, 8))

        self._progress_label = tk.Label(
            outer, text="",
            font=("Courier New", 13),
            fg="#888", bg="#0d0d14"
        )
        self._progress_label.pack(pady=(0, 30))

        # ── Problem display ──
        self._question_label = tk.Label(
            outer, text="",
            font=("Courier New", 62, "bold"),
            fg="#ffffff", bg="#0d0d14"
        )
        self._question_label.pack(pady=20)

        # ── Answer entry ──
        entry_frame = tk.Frame(outer, bg="#1a1a2e", bd=0)
        entry_frame.pack(pady=10)

        self._answer_var = tk.StringVar()
        self._entry = tk.Entry(
            entry_frame,
            textvariable=self._answer_var,
            font=("Courier New", 36, "bold"),
            width=8,
            justify="center",
            fg="#00ffaa",
            bg="#1a1a2e",
            insertbackground="#00ffaa",
            relief="flat",
            bd=0,
        )
        self._entry.pack(ipady=14, ipadx=10)
        self._entry.bind("<Return>", lambda e: self._check_answer())
        self._entry.focus_set()

        # ── Feedback label ──
        self._feedback = tk.Label(
            outer, text="",
            font=("Courier New", 16, "bold"),
            bg="#0d0d14", fg="#ff4455"
        )
        self._feedback.pack(pady=12)

        # ── Submit button ──
        self._submit_btn = tk.Button(
            outer,
            text="  SUBMIT ANSWER  ",
            command=self._check_answer,
            font=("Courier New", 16, "bold"),
            fg="#0d0d14",
            bg="#00ffaa",
            activeforeground="#0d0d14",
            activebackground="#00cc88",
            relief="flat",
            cursor="hand2",
            padx=24, pady=12,
        )
        self._submit_btn.pack(pady=20)

        # ── Difficulty tag ──
        tk.Label(
            outer, text=f"Difficulty: {self._engine.difficulty}",
            font=("Courier New", 11),
            fg="#444", bg="#0d0d14"
        ).pack(pady=(30, 0))

    # ── Logic ────────────────────────────────────

    def _new_question(self):
        question, answer = self._engine.generate()
        self._current_answer = answer
        self._question_label.config(text=question)
        self._answer_var.set("")
        remaining = self.REQUIRED_CORRECT - self._correct_streak
        self._progress_label.config(
            text=f"Solve {remaining} more problem{'s' if remaining != 1 else ''} correctly to silence the alarm",
            fg="#888"
        )
        self._feedback.config(text="")
        self._entry.focus_set()

    def _check_answer(self):
        raw = self._answer_var.get().strip()
        if not raw:
            return
        try:
            given = int(raw)
        except ValueError:
            self._show_feedback("Numbers only! Try again.", success=False)
            return

        if given == self._current_answer:
            self._correct_streak += 1
            if self._correct_streak >= self.REQUIRED_CORRECT:
                self._alarm_solved()
            else:
                self._show_feedback(f"✓ Correct!  {self.REQUIRED_CORRECT - self._correct_streak} more to go…", success=True)
                self.after(700, self._new_question)
        else:
            self._correct_streak = 0          # reset on wrong answer
            self._show_feedback(f"✗ Wrong!  (streak reset — try again)", success=False)
            self._shake()
            self._answer_var.set("")

    def _show_feedback(self, msg, success=True):
        color = "#00ffaa" if success else "#ff4455"
        self._feedback.config(text=msg, fg=color)

    def _shake(self):
        """Shake the window horizontally on wrong answer."""
        x0 = self.winfo_x()
        y0 = self.winfo_y()
        offsets = [12, -12, 8, -8, 4, -4, 0]
        def step(i=0):
            if i < len(offsets):
                self.geometry(f"+{x0 + offsets[i]}+{y0}")
                self._shake_id = self.after(40, step, i + 1)
            else:
                self.geometry(f"+{x0}+{y0}")
        step()

    def _alarm_solved(self):
        self._sound.stop()
        self._on_solved()
        self.destroy()

    def _deny_close(self):
        """Block the window close button with a taunt."""
        self._show_feedback("Nope! Solve the problem first. 😈", success=False)


# ─────────────────────────────────────────────
#  MAIN APPLICATION WINDOW
# ─────────────────────────────────────────────

class AlarmClockApp(tk.Tk):
    """Root window: clock display, alarm setter, difficulty picker."""

    PALETTE = {
        "bg":        "#0f0f1a",
        "panel":     "#181828",
        "accent":    "#7c6aff",
        "accent2":   "#ff6a9e",
        "fg":        "#e8e8f0",
        "muted":     "#5a5a78",
        "success":   "#00d4aa",
        "danger":    "#ff4455",
        "entry_bg":  "#22223a",
        "entry_fg":  "#a0f0d8",
    }

    def __init__(self):
        super().__init__()
        self._sound  = SoundEngine()
        self._alarm_time: str | None  = None   # "HH:MM"
        self._alarm_active   = False
        self._alarm_ringing  = False
        self._math_open      = False

        self._build_ui()
        self._center_window(520, 600)
        self._tick()   # start clock loop

    # ── Layout ──────────────────────────────────

    def _build_ui(self):
        self.title("Math Alarm Clock")
        self.configure(bg=self.PALETTE["bg"])
        self.resizable(False, False)

        P = self.PALETTE

        # ── Header ──
        header = tk.Frame(self, bg=P["panel"], pady=20)
        header.pack(fill="x")

        tk.Label(
            header, text="⏰  MATH ALARM",
            font=("Courier New", 26, "bold"),
            fg=P["accent"], bg=P["panel"]
        ).pack()
        tk.Label(
            header, text="Solve problems to silence the alarm",
            font=("Courier New", 10),
            fg=P["muted"], bg=P["panel"]
        ).pack()

        # ── Clock display ──
        clock_frame = tk.Frame(self, bg=P["bg"], pady=30)
        clock_frame.pack(fill="x")

        self._clock_label = tk.Label(
            clock_frame, text="00:00:00",
            font=("Courier New", 68, "bold"),
            fg=P["fg"], bg=P["bg"]
        )
        self._clock_label.pack()

        self._date_label = tk.Label(
            clock_frame, text="",
            font=("Courier New", 12),
            fg=P["muted"], bg=P["bg"]
        )
        self._date_label.pack()

        # ── Divider ──
        tk.Frame(self, height=1, bg=P["muted"]).pack(fill="x", padx=30)

        # ── Control panel ──
        panel = tk.Frame(self, bg=P["panel"], pady=28, padx=40)
        panel.pack(fill="x")

        # Time input row
        row = tk.Frame(panel, bg=P["panel"])
        row.pack(fill="x", pady=(0, 18))

        tk.Label(
            row, text="SET ALARM",
            font=("Courier New", 11, "bold"),
            fg=P["muted"], bg=P["panel"]
        ).pack(anchor="w")

        input_row = tk.Frame(panel, bg=P["panel"])
        input_row.pack(fill="x", pady=(0, 6))

        self._time_var = tk.StringVar(value="07:00")
        self._time_entry = tk.Entry(
            input_row,
            textvariable=self._time_var,
            font=("Courier New", 28, "bold"),
            width=6,
            justify="center",
            fg=P["entry_fg"],
            bg=P["entry_bg"],
            insertbackground=P["entry_fg"],
            relief="flat",
        )
        self._time_entry.pack(side="left", ipady=10, ipadx=8)
        tk.Label(input_row, text="HH:MM", font=("Courier New", 10),
                 fg=P["muted"], bg=P["panel"]).pack(side="left", padx=10)

        # Difficulty picker
        diff_row = tk.Frame(panel, bg=P["panel"])
        diff_row.pack(fill="x", pady=(8, 18))

        tk.Label(
            diff_row, text="DIFFICULTY",
            font=("Courier New", 11, "bold"),
            fg=P["muted"], bg=P["panel"]
        ).pack(anchor="w")

        self._difficulty = tk.StringVar(value="Medium")
        for d, color in [("Easy", "#00d4aa"), ("Medium", "#7c6aff"), ("Hard", "#ff4455")]:
            rb = tk.Radiobutton(
                diff_row, text=d,
                variable=self._difficulty, value=d,
                font=("Courier New", 13, "bold"),
                fg=color, bg=P["panel"],
                selectcolor=P["entry_bg"],
                activebackground=P["panel"],
                activeforeground=color,
                relief="flat", cursor="hand2",
            )
            rb.pack(side="left", padx=(0, 16))

        # Buttons row
        btn_row = tk.Frame(panel, bg=P["panel"])
        btn_row.pack(fill="x", pady=(10, 0))

        self._set_btn = tk.Button(
            btn_row,
            text="  SET ALARM  ",
            command=self._set_alarm,
            font=("Courier New", 14, "bold"),
            fg="#0f0f1a",
            bg=P["accent"],
            activeforeground="#0f0f1a",
            activebackground="#6a5aee",
            relief="flat",
            cursor="hand2",
            padx=20, pady=10,
        )
        self._set_btn.pack(side="left")

        self._cancel_btn = tk.Button(
            btn_row,
            text="  CANCEL  ",
            command=self._cancel_alarm,
            font=("Courier New", 14, "bold"),
            fg=P["fg"],
            bg=P["entry_bg"],
            activeforeground=P["danger"],
            activebackground="#2a223a",
            relief="flat",
            cursor="hand2",
            padx=20, pady=10,
            state="disabled",
        )
        self._cancel_btn.pack(side="left", padx=(12, 0))

        # ── Status bar ──
        self._status_var = tk.StringVar(value="No alarm set")
        status_bar = tk.Frame(self, bg=P["bg"], pady=16)
        status_bar.pack(fill="x")

        self._status_label = tk.Label(
            status_bar,
            textvariable=self._status_var,
            font=("Courier New", 13),
            fg=P["muted"], bg=P["bg"]
        )
        self._status_label.pack()

        # ── Footer ──
        tk.Label(
            self, text="Alarm will ring until all math problems are solved correctly",
            font=("Courier New", 9),
            fg=P["muted"], bg=P["bg"]
        ).pack(pady=(0, 14))

    # ── Clock tick ──────────────────────────────

    def _tick(self):
        now = datetime.datetime.now()
        self._clock_label.config(text=now.strftime("%H:%M:%S"))
        self._date_label.config(text=now.strftime("%A, %d %B %Y"))

        # Check alarm trigger
        if (
            self._alarm_active
            and not self._alarm_ringing
            and not self._math_open
            and self._alarm_time == now.strftime("%H:%M")
        ):
            self._trigger_alarm()

        self.after(500, self._tick)

    # ── Alarm control ────────────────────────────

    def _set_alarm(self):
        raw = self._time_var.get().strip()
        if not self._validate_time(raw):
            messagebox.showerror(
                "Invalid Time",
                "Please enter a valid time in HH:MM format (e.g. 07:30).",
                parent=self
            )
            return

        self._alarm_time   = raw
        self._alarm_active = True
        self._status_var.set(f"⏰  Alarm set for  {raw}")
        self._status_label.config(fg=self.PALETTE["success"])
        self._cancel_btn.config(state="normal")
        self._set_btn.config(text="  UPDATE ALARM  ")

    def _cancel_alarm(self):
        if self._alarm_ringing:
            return   # can't cancel while ringing — must solve it
        self._alarm_active  = False
        self._alarm_ringing = False
        self._alarm_time    = None
        self._sound.stop()
        self._status_var.set("Alarm cancelled")
        self._status_label.config(fg=self.PALETTE["muted"])
        self._cancel_btn.config(state="disabled")
        self._set_btn.config(text="  SET ALARM  ")

    def _trigger_alarm(self):
        self._alarm_ringing = True
        self._math_open     = True
        self._alarm_active  = False

        self._status_var.set("⚠  ALARM RINGING — SOLVE THE MATH!")
        self._status_label.config(fg=self.PALETTE["danger"])

        self._sound.play_loop()
        self._open_math_window()

    def _open_math_window(self):
        MathWindow(
            parent       = self,
            sound_engine = self._sound,
            difficulty   = self._difficulty.get(),
            on_solved    = self._alarm_dismissed,
        )

    def _alarm_dismissed(self):
        self._alarm_ringing = False
        self._math_open     = False
        self._status_var.set("✓  Alarm dismissed — well done!")
        self._status_label.config(fg=self.PALETTE["success"])
        self._cancel_btn.config(state="disabled")
        self._set_btn.config(text="  SET ALARM  ")

    # ── Helpers ──────────────────────────────────

    @staticmethod
    def _validate_time(s: str) -> bool:
        try:
            parts = s.split(":")
            if len(parts) != 2:
                return False
            h, m = int(parts[0]), int(parts[1])
            return 0 <= h <= 23 and 0 <= m <= 59
        except ValueError:
            return False

    def _center_window(self, w: int, h: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = AlarmClockApp()
    app.mainloop()