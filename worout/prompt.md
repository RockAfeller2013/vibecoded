Build a Progressive Web App (PWA) fitness interval timer as a single index.html file.

## Stack & Setup
- Bootstrap 5 for layout/responsiveness
- Google Material Icons Round for all icons
- Google Fonts: Bebas Neue (display) + DM Sans (body)
- Web Audio API for all sounds (no external audio files)
- PWA: register a real sw.js service worker and manifest.json (not blob URLs)
- Mobile-first, installable, works offline

## Visual Design
- Dark theme: background #0a0a0a, cards #1c1c1c, borders #2a2a2a
- Three phase colors: WORK #ff3c3c (red), REST #00e5a0 (green), PREP #ffc940 (amber)
- Noise texture overlay via inline SVG feTurbulence filter
- Animated SVG ring progress around the countdown clock
- Phase colors propagate to: badge, clock digits, ring stroke, play button glow
- Bebas Neue for all numbers/headings, DM Sans for body text
- Subtle fadeUp animation on screen transitions
- Set progress shown as dot indicators below the clock ring

## Screens
Three screens (no page loads, JS show/hide):
1. **Home** — large typographic hero "PUSH YOUR LIMIT.", three workout cards
2. **Timer** — phase badge, SVG ring clock, set dots, control buttons
3. **Complete** — trophy icon, "NAILED IT.", return home button

## Workouts (3 cards on home screen)
| Name | Color | Work | Rest | Sets |
|---|---|---|---|---|
| Sprint (10 MINS) | #ff3c3c | 15s | 45s | 10 |
| Endurance (20 MINS) | #ff8c00 | 60s | 60s | 10 |
| Hard Mode (30 MINS) | #7c4dff | 240s | 180s | 4 |

## Timer Logic
- Every workout starts with a **15-second PREP phase** (amber color scheme)
  - Auto-starts immediately when a workout card is tapped
  - Soft metronome tick every second
  - Loud beep + clock pulse animation at 3, 2, 1
  - Ascending 5-note fanfare on GO, then work sound plays
- WORK phase → REST phase → next set, repeat until all sets done
- On completion: victory jingle + show complete screen
- Reset button returns to prep phase and auto-restarts

## Controls
- Play/Pause button (large, 72px, colored by phase)
- Reset button (returns to PREP)
- Skip button (advances to next phase immediately)
- Sound toggle button (mute/unmute icon, top-right of timer)
- Keyboard: Space = play/pause, R = reset, S = skip

## Sound System (Web Audio API — sfxr-inspired synthesis)
**Critical:** Call `unlockAudio()` synchronously inside every user-gesture handler
(selectWorkout, toggleTimer) to satisfy browser autoplay policy. Play a silent
1-sample buffer as the unlock trick for iOS Safari.

Each workout has unique WORK + REST sounds:
- **Sprint WORK**: two rising square blips (660→990 Hz, then 990→1320 Hz)
- **Sprint REST**: descending sine whistle (1000→280 Hz)
- **Endurance WORK**: rising sawtooth sweep + square punch chord
- **Endurance REST**: warm sine chord (528→264 Hz) with vibrato LFO
- **Hard Mode WORK**: sub-bass sine BOOM (110→38 Hz) + metallic square sting
- **Hard Mode REST**: long falling sawtooth whoosh (800→60 Hz)

Per-second ticks during active phases:
- WORK tick: subtle 1600→1200 Hz square click (volume ~0.12)
- REST tick: gentle 600→450 Hz sine click (volume ~0.11)
- Last 3 seconds of WORK: sharp 1400→1100 Hz blip (volume ~0.48) + clock pulse
- Last 3 seconds of REST: soft 660→520 Hz ping (volume ~0.44) + clock pulse

All tone() volumes should be 0.3–0.6 range (Web Audio clips above 1.0 so stay under).
Use exponentialRampToValueAtTime for envelope release (not linear) to avoid clicks.

## tone() function signature
```js
function tone({ freq, endFreq, type, duration, volume, attack, release,
                vibratoRate, vibratoDepth, delay }) { ... }
```
type = 'square' | 'sine' | 'sawtooth'. Connect osc → gain → ctx.destination.

## PWA Files (separate from index.html)
- **manifest.json**: name, short_name, display: standalone, theme_color #0a0a0a,
  icons array for sizes 72/96/128/144/152/192/384/512, 3 shortcuts for each workout
- **sw.js**: cache-first strategy, precache index.html + manifest + icons,
  skipWaiting() on install, clients.claim() on activate, delete old caches on activate
- **icons/**: generate icon-{size}.png programmatically — dark rounded square background,
  red left stripe accent, stopwatch graphic with red progress arc
- Register sw.js with: navigator.serviceWorker.register('/sw.js') on window load

## Vibration patterns
- Phase change: [50]
- Prep GO: [60, 30, 60]  
- Countdown 3-2-1: [25]
- Complete: [200, 80, 200, 80, 400]

Output: full working index.html + manifest.json + sw.js + icon generation script.
