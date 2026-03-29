import random
import math
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from sound import SoundEngine

# ─────────────────────────────────────────────
# MATH WINDOW (WHEN ALARM TRIGGERS)
# ─────────────────────────────────────────────
class MathWindow(tk.Toplevel):
    """
    Full‑screen modal that appears when the alarm fires.
    Cannot be closed until the math problem is solved correctly.
    """

    REQUIRED_CORRECT = 3   # solve this many in a row to dismiss

    def __init__(self, parent, sound_engine: SoundEngine, difficulty: str, on_solved):
        super().__init__(parent)
        self._sound     = sound_engine
        self._engine    = MathChallenge(difficulty)
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
#  MATH CHALLENGE ENGINE
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
        else:   # "-"
            if b > a:
                a, b = b, a   # keep answer positive
            answer = a - b

        question = f"{a}  {op}  {b}  =  ?"
        return question, answer
