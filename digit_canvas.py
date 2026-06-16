# digit_canvas.py
import tkinter as tk
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import tensorflow as tf
import os

_model = None  # lazy-loaded once

def load_model():
    global _model
    if _model is None:
        model_path = os.path.join(os.path.dirname(__file__), "mnist_model.keras")
        _model = tf.keras.models.load_model(model_path)
    return _model


class DigitCanvas(tk.Frame):
    """
    A drawable canvas that predicts the digit the user drew.
    Drop-in replacement for the tk.Entry in MathWindow.

    Usage:
        canvas = DigitCanvas(parent, size=200)
        canvas.pack()
        digit = canvas.predict()   # returns int 0–9, or None if blank
        canvas.clear()
    """

    def __init__(self, parent, size=200, brush=12, bg="#1a1a2e", fg="#00ffaa"):
        super().__init__(parent, bg=bg, bd=2, relief="flat")
        self._size   = size
        self._brush  = brush
        self._bg_col = bg
        self._fg_col = fg

        self._canvas = tk.Canvas(
            self, width=size, height=size,
            bg=bg, cursor="crosshair", highlightthickness=0
        )
        self._canvas.pack()

        # PIL image we draw into in parallel (this is what the model sees)
        self._pil_img  = Image.new("L", (size, size), color=0)   # black bg
        self._pil_draw = ImageDraw.Draw(self._pil_img)

        self._last_xy = None
        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

    # ── Drawing callbacks ──────────────────────────────────────────────

    def _on_press(self, event):
        self._last_xy = (event.x, event.y)

    def _on_drag(self, event):
        if self._last_xy is None:
            return
        x0, y0 = self._last_xy
        x1, y1 = event.x, event.y
        r = self._brush // 2
        # Draw on Tkinter canvas (visible)
        self._canvas.create_oval(x1-r, y1-r, x1+r, y1+r,
                                 fill=self._fg_col, outline=self._fg_col)
        # Draw on PIL image (fed to model) — white digit on black bg
        self._pil_draw.ellipse([x1-r, y1-r, x1+r, y1+r], fill=255)
        self._last_xy = (x1, y1)

    def _on_release(self, event):
        self._last_xy = None

    # ── Public API ─────────────────────────────────────────────────────

    def clear(self):
        """Wipe the canvas and the PIL backing image."""
        self._canvas.delete("all")
        self._pil_img  = Image.new("L", (self._size, self._size), color=0)
        self._pil_draw = ImageDraw.Draw(self._pil_img)

    def is_blank(self):
        """Return True if the user hasn't drawn anything."""
        return self._pil_img.getbbox() is None

    def predict(self):
        """
        Run the MNIST model on what's been drawn.
        Returns the predicted digit (int 0–9), or None if canvas is blank.
        """
        if self.is_blank():
            return None

        # 1. Crop to the drawn content, then resize to 28×28
        bbox = self._pil_img.getbbox()
        cropped = self._pil_img.crop(bbox)

        # Add a small border so the digit isn't edge-to-edge (matches MNIST style)
        padded = ImageOps.expand(cropped, border=10, fill=0)
        resized = padded.resize((28, 28), Image.LANCZOS)

        # 2. Normalise and reshape for the model: (1, 28, 28, 1)
        arr = np.array(resized, dtype=np.float32) / 255.0
        arr = arr.reshape(1, 28, 28, 1)

        # 3. Predict
        model = load_model()
        probs  = model.predict(arr, verbose=0)
        return int(np.argmax(probs))