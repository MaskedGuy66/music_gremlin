# Agnes - Desktop Music Gremlin

A draggable desktop widget powered by the Agnes gremlin sprite model. Drag Agnes onto any image on your screen -- a photo, album art, a thumbnail in Chrome -- and she will automatically search for and play a matching YouTube music video (audio only) with a colorful beat-synced visualizer.

---

## How It Works

```
Drag Agnes onto an image
        |
        v
  Screen capture + Image recognition
        |
        v
  Identify context (album art, artist, song, mood)
        |
        v
  Search YouTube for matching music
        |
        v
  Play audio in background (no video)
        |
        v
  Beat-synced colorful visualizer + Agnes dances
```

### State Machine

Agnes follows a strict state lifecycle to keep animations smooth and transitions seamless:

| State      | Agnes Animation | Description                                  |
|------------|-----------------|----------------------------------------------|
| FREE       | IDLE (340f)     | Agnes roams freely, random idle actions      |
| ANALYZING  | HOVER (30f)     | Agnes observes -- screen capture in progress |
| LOADING    | GRAB (40f)      | Agnes grabs -- searching YouTube             |
| PLAYING    | EMOTE1/3/SLEEP  | Agnes dances to the beat -- visualizer active|

The lifecycle follows: **Map -> Lock -> Execute -> Unlock**

- **Lock** prevents IDLE from interrupting a dance mid-animation
- **Unlock** restores random actions when the music session ends

### Audio-Reactive Dancing

During PLAYING, a real-time audio analysis thread reads system audio and maps intensity to Agnes's dance moves:

| Audio Intensity | Agnes Animation | Vibe        |
|-----------------|-----------------|-------------|
| < 500 RMS       | SLEEP (255f)    | Calm / quiet |
| 500 - 3000 RMS  | EMOTE1 (42f)    | Grooving     |
| > 3000 RMS      | EMOTE3 (189f)   | Full energy  |

---

## Architecture

```
audio_widget.py          -- Main widget (Tkinter, always-on-top, draggable)
  |
  +-- Screen capture (PIL ImageGrab)
  +-- Image context analysis (numpy)
  +-- YouTube search + audio playback
  +-- Beat visualizer (colorful, audio-synced)
  +-- Audio analysis thread (pyaudio, RMS intensity)
  |
bridge_controller.py     -- TCP bridge to C# sprite renderer
  |
  +-- State mapping (Python state -> C# animation key)
  +-- Lock/Unlock mechanism
  +-- JSON over TCP (127.0.0.1:65432)
  |
spriteManager.cs         -- C# sprite sheet renderer
  |
  +-- Frame-by-frame animation from PNG sprite sheets
  +-- State -> filename mapping
  +-- Receives commands via TCP bridge
  |
SpriteSheet/Gremlins/Agnes/
  +-- config.txt          -- Frame counts, dimensions, column layout
  +-- *.png               -- Sprite sheets for each animation
  |
Sounds/Agnes/
  +-- *.wav              -- Sound effects per animation state
```

### Bridge Protocol

The Python widget communicates with the C# renderer over TCP using JSON messages:

```json
{"action": "CHANGE_STATE", "state": "EMOTE1", "locked": true}
{"action": "LOCK"}
{"action": "UNLOCK"}
```

---

## Sprite Sheet Reference

Agnes uses 300x300 sprite sheets with 10 columns. Frame counts from `config.txt`:

**Loopable Animations** (cycle continuously):
- IDLE: 340 frames | IDLE2: 44 frames | HOVER: 30 frames
- SLEEP: 255 frames | EMOTE1: 42 frames | EMOTE4: 24 frames
- GRAB: 40 frames | WALK_IDLE: 41 frames | OUTRO: 65 frames

**Non-Loopable Animations** (play once, then transition):
- INTRO: 50 frames | PAT: 35 frames | CLICK: 117 frames
- EMOTE2: 42 frames | EMOTE3: 189 frames | RELOAD: 70 frames

**Walk/Run** (8-directional, 18-30 frames each):
- Run: UPRIGHT/UPLEFT/DOWNRIGHT/DOWNLEFT/UP/DOWN/LEFT/RIGHT (18f)
- Walk: WALK_L/WALK_U/WALK_D/WALK_R (30f)

---

## Dependencies

### Python (Widget + Bridge)
- `tkinter` -- Always-on-top draggable window
- `Pillow` (PIL) -- Screen capture via ImageGrab
- `numpy` -- Image analysis, audio RMS calculation
- `pyaudio` -- System audio capture for beat detection
- `pyautogui` -- Screen interaction utilities
- `winsound` -- Quick sound playback (Windows)

### C# (Sprite Renderer)
- .NET with WinForms or WPF
- TCP listener on port 65432

---

## Setup

```bash
# Install Python dependencies
pip install Pillow numpy pyaudio pyautogui

# Start the C# sprite renderer first
# (listens on 127.0.0.1:65432)

# Then launch the widget
python audio_widget.py
```

---

## Roadmap

- [ ] **Image recognition** -- Use OCR or image search API to identify album art, artist names, or song titles from the captured screen region
- [ ] **YouTube search** -- Query YouTube Data API with identified context, pick the best matching music video
- [ ] **Audio-only playback** -- Stream YouTube audio without the video window (yt-dlp + ffmpeg or similar)
- [ ] **Beat visualizer** -- Colorful, audio-reactive visualizer overlay that pulses with the music intensity
- [ ] **Drag-to-search UX** -- Drop Agnes on any image to trigger the full pipeline: capture -> identify -> search -> play -> visualize
- [ ] **Cross-platform audio** -- Replace `winsound` with a portable audio library for macOS/Linux support
- [ ] **Configurable thresholds** -- Let users adjust audio intensity thresholds for dance mapping
- [ ] **Playlist mode** -- Queue multiple tracks, auto-advance when one finishes

---

## Project Structure

```
project/
  audio_widget.py              -- Main widget application
  bridge_controller.py         -- TCP bridge to C# renderer
  spriteManager.cs             -- C# sprite animation manager
  SpriteSheet/
    Gremlins/
      Agnes/
        config.txt             -- Frame counts and layout
        idle.png               -- Sprite sheets...
        hover.png
        grab.png
        sleep.png
        emote1.png
        emote2.png
        emote3.png
        emote4.png
        intro.png
        outro.png
        pat.png
        click.png
        ...
  Sounds/
    Agnes/
      hover.wav                -- Sound effects per state
      intro.wav
      grab.wav
      mambo.wav
      sleep.wav
      emote1.wav
      emote2.wav
      emote3.wav
      emote4.wav
      ...
```
