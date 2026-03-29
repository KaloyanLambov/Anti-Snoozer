import os
import sys
import threading
import time as time_module

# ─────────────────────────────────────────────
#  SOUND ENGINE  (pygame › winsound fallback)
# ─────────────────────────────────────────────

class SoundEngine:
    """Handles cross‑platform alarm audio with graceful fallbacks."""

    SOUND_FILES = ["alarm.wav", "alarm.mp3", "alarm.ogg"]

    def __init__(self):
        self._pygame_ok = False
        self._sound_file = None
        self._beep_thread = None
        self._beeping = False
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

        # Last‑resort: OS beeps in a background thread
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