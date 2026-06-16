# Anti-Snoozer

**A Python app that forces you to solve handwritten math problems before you can dismiss your alarm**

---

## Table of Contents

- [Why?](#why)
- [Features](#features)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Using It](#using-it)
  * [Setting an Alarm](#setting-an-alarm)
  * [Difficulty Levels](#difficulty-levels)
  * [Solving the Challenge](#solving-the-challenge)
  * [Cancelling / Dismissing](#cancelling--dismissing)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Customization](#customization)
  * [Sound File](#sound-file)

---

## Why?

Most alarm clocks let you snooze or just press a button to stop the sound.
This one forces you to **exercise your brain** — and now your handwriting, too. Instead of typing an answer, you draw a digit on screen and a neural network reads it.

---

## Features

| Feature                    | Description                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------ |
| ✍️ Handwriting CAPTCHA      | Draw your answer with the mouse/trackpad — a CNN trained on MNIST reads the digit, no typing allowed.  |
| 🎯 Math Challenge           | Solve 3 consecutive problems (Easy / Medium / Hard) to silence the alarm.                              |
| 🔢 Digit‑position prompts   | For multi‑digit answers, you're asked to draw a specific digit (e.g. "draw the 2nd digit of the answer"), keeping every answer a single digit (0–9) so the OCR model can read it. |
| ⏰ Live Countdown            | See exactly how long until your alarm rings.                                                            |
| 🔊 Cross‑platform sound     | Uses `pygame` if available (file or synthesised beep‑pause‑beep pattern), falls back to OS beeps.      |
| 📅 Date & Time display      | Full‑window clock with current date.                                                                    |
| 🔌 Easy cancel / update     | Cancel an upcoming alarm or change the time/difficulty on the fly.                                      |

---

## Installation

> **Python 3.8+ is required.**

```bash
# Clone the repo
git clone https://github.com/KaloyanLambov/Anti-Snoozer
cd Anti-Snoozer

# Optional: create and run a virtual environment
python -m venv .venv
venv\Scripts\activate

# Install dependencies (pygame for sound, TensorFlow + Pillow + NumPy for the handwriting OCR)
pip install -r requirements.txt
```

> If you skip `requirements.txt`, the alarm clock itself will still run — but the handwriting CAPTCHA requires TensorFlow, Pillow, and NumPy, and the sound engine works best with `pygame` installed (it will fall back to OS beeps otherwise).

`requirements.txt`:
```
pygame
tensorflow-cpu
pillow
numpy
```

---

## Running the App

```bash
python anti_snoozer.py
```

The window opens centred on screen. No installation scripts needed beyond the one‑time model training above.

---

## Using It

### Setting an Alarm

1. Enter a time in **HH:MM** format (24‑hour clock).
2. Pick a difficulty level.
3. Click **SET ALARM**.

*The status bar will say "Alarm set for 07:30 (Medium)".*

### Difficulty Levels

- **Easy** – simple addition/subtraction, smaller numbers.
- **Medium** – includes multiplication with higher numbers.
- **Hard** – also division, higher numbers.

The chosen difficulty appears next to the alarm time in both the status bar and the countdown label. Difficulty controls the size of the numbers involved, not how many digits you have to draw — that's always one digit per problem.

### Solving the Challenge

When the alarm rings, a full‑screen window shows an equation and asks for one specific digit of the answer — for example:

```
341 × 4 = ?

Draw the 2nd digit of the answer
```

(Since 341 × 4 = 1364, the correct digit to draw here is **3**.)

Instead of typing, you **draw the digit** on the canvas with your mouse or trackpad. The drawing is converted to a 28×28 grayscale image and fed into the trained CNN, which predicts what digit you drew and checks it against the correct answer. Use the **Clear** button to redo a drawing before submitting.

Three correct digits in a row are required to dismiss the alarm. Any wrong answer resets the streak to zero and shakes the window.

### Cancelling / Dismissing

- **Cancel**: Press the **CANCEL** button before the alarm rings. The status will revert to "No alarm set".
- **Dismiss**: When the alarm rings, draw three correct digits consecutively — the alarm window closes automatically and the status updates to "Alarm dismissed".

---

## How It Works

1. **Clock Loop** (`_tick`)
   Updates every 500 ms, refreshing time, date, and countdown.
2. **Alarm Trigger**
   When the set time matches the current hour/minute, the app switches to *ringing* mode:
   - Sound starts looping via `SoundEngine` (file playback, synthesised beep‑pause‑beep tone, or OS beep fallback).
   - A full‑screen modal (`MathWindow`) pops up.
3. **Math Challenge**
   `MathChallenge.generate()` produces a random arithmetic problem based on difficulty, then randomly selects one digit position within the multi‑digit answer (e.g. "2nd digit") as the target you need to draw.
4. **Handwriting Recognition**
   `DigitCanvas` captures your strokes, crops and centers the drawing, resizes it to 28×28 pixels, and passes it to the pre‑trained CNN (`mnist_model.keras`) for prediction.
5. **Answer Checking**
   Three consecutive correctly‑drawn digits are required. Any wrong digit resets the streak and shakes the window.

No external config or database is needed.

---

## Project Structure

```
Anti-Snoozer/
├── anti_snoozer.py     # Main app window: clock, alarm setter, difficulty picker
├── maths.py             # MathWindow (alarm challenge UI) + MathChallenge (problem generator)
├── digit_canvas.py      # Drawable canvas widget + MNIST model inference
├── sound.py              # Cross-platform alarm sound engine
├── train_mnist.py        # One-time script to train and save the CNN model
├── mnist_model.keras     # Generated by train_mnist.py (not committed — train it yourself)
└── requirements.txt
```

---

## Customization

### Sound File

If you want a different alarm tone:

1. Place a WAV, MP3, or OGG file named **`alarm.wav`** (or one of the other supported extensions) next to `anti_snoozer.py`.
2. The app will automatically use it instead of the synthesised beep pattern.

> If no file is found, the app generates a beep‑pause‑beep tone via `pygame`/`numpy`. If neither is installed, you'll hear OS beeps — still functional but less pleasant.