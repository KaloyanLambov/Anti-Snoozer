"""
╔═════════════════════════════════════════════════════════════╗
║                      MATH ALARM CLOCK                       ║
║  Solve math problems to dismiss the alarm. No cheating!     ║
╚═════════════════════════════════════════════════════════════╝
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tkinter as tk
from tkinter import messagebox
import datetime
from sound import SoundEngine
from maths import MathWindow

# ─────────────────────────────────────────────
#  MAIN APPLICATION WINDOW
# ─────────────────────────────────────────────

class AlarmClockApp(tk.Tk):
    """Root window: clock display, alarm setter, difficulty picker."""

    PALETTE = {
        "bg":         "#0f0f1a",
        "panel":      "#181828",
        "accent":     "#7c6aff",
        "accent2":    "#ff6a9e",
        "fg":         "#e8e8f0",
        "muted":      "#5a5a78",
        "success":    "#00d4aa",
        "danger":     "#ff4455",
        "entry_bg":   "#22223a",
        "entry_fg":   "#a0f0d8",
    }

    def __init__(self):
        super().__init__()
        self._sound  = SoundEngine()
        self._alarm_time: str | None  = None   # "HH:MM"
        self._alarm_active   = False
        self._alarm_ringing  = False
        self._math_open      = False

        self._build_ui()
        self._center_window(520, 650)
        self._tick()   # start clock loop

    # ── Layout ──────────────────────────────────

    def _build_ui(self):
        self.title("Anti-Snoozer")
        self.configure(bg=self.PALETTE["bg"])
        self.resizable(False, False)

        P = self.PALETTE

        # ── Header ──
        header = tk.Frame(self, bg=P["panel"], pady=20)
        header.pack(fill="x")

        tk.Label(
            header, text="Anti-Snoozer",
            font=("Courier New", 26, "bold"),
            fg=P["accent"], bg=P["panel"]
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

        # ── **New alarm status labels** ──
        self._alarm_set_label = tk.Label(
            clock_frame,
            text="No alarm set",
            font=("Courier New", 16),
            fg=P["muted"],
            bg=P["bg"]
        )
        self._alarm_set_label.pack()

        self._countdown_label = tk.Label(
            clock_frame,
            text="",
            font=("Courier New", 16),
            fg=P["muted"],
            bg=P["bg"]
        )
        self._countdown_label.pack()
        # ── End of new section ──

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

        # Update countdown label while an alarm is pending
        if self._alarm_active and not self._alarm_ringing:
            self._update_countdown_label()

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
        
        difficulty = self._difficulty.get()

        self._alarm_time   = raw
        self._alarm_active = True
        self._status_var.set(f"⏰  Alarm set for {raw} ({difficulty})")
        self._status_label.config(fg=self.PALETTE["success"])
        self._cancel_btn.config(state="normal")
        self._set_btn.config(text="  UPDATE ALARM  ")

        self._alarm_set_label.config(text=f"Alarm set for {raw} ({difficulty})")
        self._update_countdown_label()

    def _cancel_alarm(self):
        if self._alarm_ringing:
            return   # can't cancel while ringing
        self._alarm_active  = False
        self._alarm_ringing = False
        self._alarm_time    = None
        self._sound.stop()
        self._status_var.set("Alarm cancelled")
        self._status_label.config(fg=self.PALETTE["muted"])
        self._cancel_btn.config(state="disabled")
        self._set_btn.config(text="  SET ALARM  ")

        # Clear status labels
        self._alarm_set_label.config(text="No alarm set")
        self._countdown_label.config(text="")

    def _trigger_alarm(self):
        self._alarm_ringing = True
        self._math_open     = True
        self._alarm_active  = False

        self._status_var.set("⚠  ALARM RINGING — SOLVE THE MATH!")
        self._status_label.config(fg=self.PALETTE["danger"])

        # Clear the status labels while ringing
        self._alarm_set_label.config(text="")
        self._countdown_label.config(text="")

        self._sound.play_loop()
        self._open_math_window()

    def _open_math_window(self):
        MathWindow(
            parent      = self,
            sound_engine= self._sound,
            difficulty  = self._difficulty.get(),
            on_solved   = self._alarm_dismissed,
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

    # ── Countdown handling ───────────────────────

    def _update_countdown_label(self):
        """Compute and display the remaining time until alarm triggers."""
        if not self._alarm_time:
            self._countdown_label.config(text="")
            return

        now = datetime.datetime.now()
        hh, mm = map(int, self._alarm_time.split(":"))
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if target <= now:           # alarm is for tomorrow
            target += datetime.timedelta(days=1)

        delta_seconds = int((target - now).total_seconds())
        h, rem = divmod(delta_seconds, 3600)
        m, s   = divmod(rem, 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        self._countdown_label.config(text=f"Alarm in {time_str}")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = AlarmClockApp()
    app.mainloop()