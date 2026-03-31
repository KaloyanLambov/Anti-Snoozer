# Math Alarm Clock  
**A Python app that forces you to solve arithmetic problems before you can dismiss your alarm**

---

## Table of Contents
- [Why?](#why)
- [Features](#features)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Using It](#using-it)
  - [Setting an Alarm](#setting-an-alarm)
  - [Difficulty Levels](#difficulty-levels)
  - [Cancelling / Dismissing](#cancelling--dismissing)
- [How It Works](#how-it-works)
- [Customization](#customization)
  - [Sound File](#sound-file)

---

## Why?

Most alarm clocks let you snooze or just press a button to stop the sound.  
This one forces you to **exercise your brain**.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎯 Math Challenge | Solve 3 consecutive problems (Easy / Medium / Hard) to silence the alarm. |
| ⏰ Live Countdown | See exactly how long until your alarm rings. |
| 🔊 Cross‑platform sound | Uses `pygame` if available, falls back to OS beeps or a bundled WAV/MP3 file. |
| 📅 Date & Time display | Full-window clock with current date. |
| 🛠️ One‑file distribution | No external modules required (except optional `pygame`). |
| 🔌 Easy cancel / update | Cancel an upcoming alarm or change the time/difficulty on the fly. |

---

## Installation

> **Python 3.8+ is required** (the app uses `datetime`, `tkinter` and the standard library only).

```bash
# Clone the repo
git clone https://github.com/KaloyanLambov/Anti-Snoozer
cd Anti-Snoozer

# Optional: create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install optional dependency for nicer sound (pygame)
pip install -r requirements.txt
```

> If you skip `requirements.txt`, the app will still run – it will either play a bundled WAV file or use OS beeps.

---

## Running the App

```bash
python anti-snoozer.py
```

The window is **single‑file**; just drop it into any folder and double‑click (or launch via terminal). No installation scripts needed.

---

## Using It

### Setting an Alarm

1. Enter a time in **HH:MM** format (24‑hour clock).
2. Pick a difficulty level.
3. Click **SET ALARM**.  
   *The status bar will say “Alarm set for 07:30 (Medium)”.*

### Difficulty Levels

- **Easy** – simple addition/subtraction, answers are single digits.
- **Medium** – includes multiplication with higher numbers.
- **Hard** – also division, higher numbers.

The chosen difficulty appears next to the alarm time in both the status bar and the countdown label.

### Cancelling / Dismissing

- **Cancel**: Press the **CANCEL** button before the alarm rings. The status will revert to “No alarm set”.
- **Dismiss**: When the alarm rings, solve three correct problems consecutively – the alarm window closes automatically and the status updates to “Alarm dismissed”.

---

## How It Works

1. **Clock Loop** (`_tick`)  
   Updates every 500 ms, refreshing time, date and countdown.
2. **Alarm Trigger**  
   When the set time matches the current hour/minute, the app switches to *ringing* mode:
   - Sound starts looping via `SoundEngine`.
   - A full‑screen modal (`MathWindow`) pops up.
3. **Math Challenge**  
   Uses `MathChallenge.generate()` to produce random problems based on difficulty.
4. **Answer Checking**  
   Three consecutive correct answers are required. Any wrong answer resets the streak and shakes the window.

All logic lives in a single Python file – no external config or database is needed.

---

## Customization

### Sound File

If you want a different alarm tone:

1. Place a WAV, MP3 or OGG file named **`alarm.wav`** (or one of the other supported extensions) next to `anti-snoozer.py`.
2. The app will automatically use it instead of generating a beep.

> If no file is found and `pygame` isn’t installed, you’ll hear OS beeps – still functional but less pleasant.

---