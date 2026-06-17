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
        self._active_sound = None
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
        self.stop()                      # always stop any previous sound first

        if self._pygame_ok and self._sound_file:
            try:
                sound = self._pygame.mixer.Sound(self._sound_file)
                sound.play(loops=-1)
                self._active_sound = sound
                return
            except Exception:
                pass

        if self._pygame_ok:
            self._start_synth_beep()
            return

        self._beeping = True
        self._beep_thread = threading.Thread(target=self._os_beep_loop, daemon=True)
        self._beep_thread.start()

    def stop(self):
        """Stop all alarm sounds."""
        self._beeping = False
        if self._beep_thread is not None:
            self._beep_thread.join(timeout=1.0)   # wait for old thread to actually exit
            self._beep_thread = None
        if self._pygame_ok:
            try:
                self._pygame.mixer.stop()
            except Exception:
                pass
        self._active_sound = None

    # ── Internal helpers ─────────────────────────


    def _start_synth_beep(self):
        """Use pygame to generate a simple beep-pause-beep alarm pattern."""
        try:
            import numpy as np
            sr = 44100
            beep_duration = 0.4
            silence_duration = 0.3          # add a gap so it's not continuous
            t = np.linspace(0, beep_duration, int(sr * beep_duration), False)
            beep = (np.sin(2 * np.pi * 880 * t) * 32767).astype(np.int16)
            silence = np.zeros(int(sr * silence_duration), dtype=np.int16)
            wave = np.concatenate([beep, silence])      # one cycle = beep + gap
            stereo = np.column_stack([wave, wave])
            sound = self._pygame.sndarray.make_sound(stereo)
            sound.play(loops=-1)
            self._active_sound = sound
        except Exception:
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