import random
import math
import os
import sys
import tkinter as tk
from digit_canvas import DigitCanvas
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
        self._equation_label = tk.Label(
            outer, text="",
            font=("Courier New", 56, "bold"),
            fg="#ffffff", bg="#0d0d14",
        )
        self._equation_label.pack(pady=(20, 4))

        self._instruction_label = tk.Label(
            outer, text="",
            font=("Courier New", 16),
            fg="#7c6aff", bg="#0d0d14",
        )
        self._instruction_label.pack(pady=(0, 16))

        # ── Drawing canvas (replaces Entry) ──
        tk.Label(
            outer, text="Draw the answer below:",
            font=("Courier New", 12),
            fg="#888", bg="#0d0d14"
        ).pack()

        self._digit_canvas = DigitCanvas(outer, size=200, brush=14)
        self._digit_canvas.pack(pady=8)

        clear_btn = tk.Button(
            outer, text="Clear",
            command=self._digit_canvas.clear,
            font=("Courier New", 11),
            fg="#888", bg="#1a1a2e",
            relief="flat", cursor="hand2",
            padx=10, pady=4,
        )
        clear_btn.pack()

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
        equation_string, instruction_string, answer = self._engine.generate()
        self._current_answer = answer
        self._equation_label.config(text=equation_string)
        self._instruction_label.config(text=instruction_string)
        self._digit_canvas.clear()          # ← add this line
        remaining = self.REQUIRED_CORRECT - self._correct_streak
        self._progress_label.config(
            text=f"Solve {remaining} more problem{'s' if remaining != 1 else ''} correctly to silence the alarm",
            fg="#888"
        )
        self._feedback.config(text="")

    def _check_answer(self):
        if self._digit_canvas.is_blank():
            self._show_feedback("Draw a number first!", success=False)
            return

        predicted = self._digit_canvas.predict()

        if predicted is None:
            self._show_feedback("Couldn't read that — try again.", success=False)
            return

        # For multi-digit answers (e.g. answer is 12), the user draws one digit
        # at a time. But MNIST only reads single digits, so you have two choices:
        #
        # OPTION A (simple): constrain MathChallenge to only produce single-digit
        #   answers (see Phase 5). This is the recommended approach.
        #
        # OPTION B (advanced): collect drawn digits sequentially and concatenate.
        #   Not covered here — stick with Option A for now.

        if predicted == self._current_answer:
            self._correct_streak += 1
            self._digit_canvas.clear()
            if self._correct_streak >= self.REQUIRED_CORRECT:
                self._alarm_solved()
            else:
                self._show_feedback(
                    f"✓ Correct! {self.REQUIRED_CORRECT - self._correct_streak} more to go…",
                    success=True
                )
                self.after(700, self._new_question)
        else:
            self._correct_streak = 0
            self._show_feedback(
                f"✗ Wrong! Model read '{predicted}'. (streak reset)",
                success=False
            )
            self._shake()
            self._digit_canvas.clear()

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
        """
        Return (question_string, target_digit) where target_digit is the
        digit (0-9) at a randomly chosen position of the full answer.
        The question string tells the user which position to draw.
        """
        cfg = self.DIFFICULTIES[self.difficulty]
        op = random.choice(cfg["ops"])
        a = random.randint(2, cfg["max_a"])
        b = random.randint(2, cfg["max_b"])

        if op == "÷":
            b = random.randint(2, 12)
            a = b * random.randint(2, cfg["max_b"] // b or 2)
            answer = a // b
        elif op == "×":
            answer = a * b
        elif op == "+":
            answer = a + b
        else:  # "-"
            if b > a:
                a, b = b, a
            answer = a - b

        answer_str = str(answer)
        num_digits = len(answer_str)

        # Pick which digit position to ask for (1-indexed from the left)
        position = random.randint(1, num_digits)
        target_digit = int(answer_str[position - 1])

        ordinal = self._ordinal(position)
        equation_string = f"{a} {op} {b} = ?\n\n"

        instruction_string = f"Draw the {ordinal} digit of the answer"

        return equation_string, instruction_string, target_digit

    @staticmethod
    def _ordinal(n):
        suffixes = {1: "1st", 2: "2nd", 3: "3rd"}
        return suffixes.get(n, f"{n}th")