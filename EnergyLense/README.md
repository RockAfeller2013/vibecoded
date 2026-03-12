# ⚡ EnergyLens — Electricity Bill Analyser

> A fully offline, zero-backend Progressive Web App that reads your Red Energy PDF bills directly from a local folder and builds a rich energy usage dashboard — all inside the browser.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Live Demo / Usage](#live-demo--usage)
- [Features](#features)
- [File Structure](#file-structure)
- [Getting Started](#getting-started)
- [How It Works](#how-it-works)
- [PDF Parser — Supported Fields](#pdf-parser--supported-fields)
- [Charts & Visualisations](#charts--visualisations)
- [Print / PDF Report](#print--pdf-report)
- [Solar & Battery Analysis](#solar--battery-analysis)
- [PWA — Offline & Install](#pwa--offline--install)
- [Browser Requirements](#browser-requirements)
- [Tech Stack](#tech-stack)
- [The Prompt](#the-prompt)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

EnergyLens parses your electricity bills, extracts key data points using regex, and renders an interactive dashboard with D3.js charts, summary statistics, solar/battery recommendations, and a printable PDF report.

**Nothing is uploaded anywhere.** The app uses the browser's [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API) to read PDFs directly from your local `bills/` folder. All processing happens in-browser. Parsed data is cached in `localStorage` so the dashboard loads instantly on every subsequent visit.

---

## Live Demo / Usage

```
1. Clone or download this repo
2. Put your Red Energy PDF bills in a folder called  bills/
3. Open  index.html  in Chrome 86+ or Edge 86+
4. Click "Select folder containing bills" and pick your bills/ folder
5. The app scans all PDFs recursively and renders the dashboard
```

> **No build step. No server. No npm install.** Just open `index.html`.

---

## Features

### 🗂 Folder Loading
- **File System Access API** — grant one-time permission to a folder; the handle is persisted in IndexedDB so the app auto-loads on every subsequent visit with zero interaction
- **Recursive scan** — walks the entire directory tree (up to 6 levels deep), finds every `.pdf` file regardless of subfolder nesting
- **Smart root detection** — if you select a parent folder that contains a `bills/` subfolder, it automatically navigates into it; if you select `bills/` directly, it scans that
- **4-phase progress UI** — Locating → Discovering → Parsing (per-file counter) → Done
- **Deduplication** — merges new bills with cached data by `bill_date`; re-scanning never creates duplicates

### 📊 Dashboard — Summary Cards
| Card | Value |
|------|-------|
| Total Usage | Sum of all kWh across all bills |
| Average Daily Usage | Mean daily kWh across billing periods |
| Solar Recommendation | Estimated system size (kW) |
| Battery Recommendation | Estimated storage size (kWh) |
| Peak / Off-Peak Ratio | Peak kWh ÷ Off-Peak kWh |
| Total Spend | Sum of all bill charges |

### 📈 D3.js Charts
1. **Monthly Energy Usage** — animated bar chart, total kWh per billing period
2. **Peak vs Off-Peak** — stacked bar chart with legend, showing 4–9pm peak vs all other hours
3. **Demand Trend** — line chart with area fill, peak demand (kW) per period
4. **Average Daily Usage** — line chart with mean reference line

All charts support:
- Hover tooltips with per-bill detail
- Smooth enter animations (bars grow up, lines draw from left)
- Responsive resize (redraws on window resize)

### 🔍 Analysis Modals
Four clickable tool cards open Bootstrap modals with dedicated D3 charts:

| Tool | Description |
|------|-------------|
| ☀️ Solar Sizing | Bar chart across system sizes, highlights recommended bracket |
| 🔋 Battery Sizing | Bar chart across storage sizes, highlights recommended range |
| 📜 Usage History | Daily average kWh trend over time |
| 💰 Cost Analysis | Bill-by-bill cost bar chart with tooltips |

### 🖨 Print / PDF Report
A full 5-page print-ready report generated as a new browser tab:

| Page | Content |
|------|---------|
| Cover | Dark branded cover, period, headline stats |
| 1 — Executive Summary | Six stat cards, key insights table (monthly averages, highest/lowest bill, usage splits) |
| 2 — Usage Analysis | Monthly kWh chart, stacked peak/off-peak chart, per-bill usage split table with inline bar |
| 3 — Demand & Daily | Demand stat boxes (max/avg/min), demand trend chart, daily average chart |
| 4 — Solar & Battery | Personalised sizing cards with formulas, indicative savings estimate, time-of-use tips |
| 5 — Full Bill History | Complete table of every bill with totals/averages footer row |

Charts are captured as live SVGs from the dashboard at print time, then inlined into the report.

### 🌙 Dark / Light Mode
Toggles via the header button; preference saved to `localStorage`.

---

## File Structure

```
energylens/
├── index.html          # Single-page app (all JS inline)
├── styles.css          # Design system — CSS variables, components, charts
├── app.js              # Unused module stub (logic lives inline for file:// compat)
├── manifest.json       # PWA manifest — name, icons, theme colour
├── service-worker.js   # Caches CDN assets for offline use
└── bills/              # ← Put your Red Energy PDF bills here
    ├── 09_MAR_26.pdf
    ├── 09_FEB_26.pdf
    └── ...
```

> **Why inline JS?** ES modules require a server (CORS) when split across files. Since this app is designed to run directly from a local folder via `file://`, all JavaScript lives inside `index.html` to avoid that restriction.

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/energylens.git
cd energylens
```

### 2. Add your bills

Create a `bills/` subfolder and copy your Red Energy PDF statements into it:

```bash
mkdir bills
cp ~/Downloads/*.pdf bills/
```

Subfolders are fine — the app scans recursively:

```
bills/
├── 2024/
│   ├── jan_2024.pdf
│   └── feb_2024.pdf
└── 2025/
    ├── jan_2025.pdf
    └── ...
```

### 3. Open the app

Simply open `index.html` in **Chrome 86+** or **Edge 86+**:

```bash
# macOS
open index.html

# Windows
start index.html

# Or drag index.html into your browser
```

### 4. Grant folder access

On first load you'll see the permission screen. Click **"Select folder containing bills"** and choose either:
- Your `bills/` folder directly, **or**
- Any parent folder that contains a `bills/` subfolder

The app will discover all PDFs automatically and start parsing.

### 5. Subsequent visits

On every visit after the first, the app silently re-reads the saved folder handle from IndexedDB and re-scans automatically. No clicks needed. If browser permission needs re-confirming after a restart, a slim amber banner appears with a single "Grant Access" button.

---

## How It Works

### PDF Parsing Pipeline

```
FileSystemFileHandle
    → file.arrayBuffer()
    → pdfjsLib.getDocument()
    → page.getTextContent()
    → items.map(i => i.str).join(' ')   ← raw text string
    → parseBill(text, filename)         ← regex extraction
    → bill object
    → deduplicated bills[] array
    → localStorage cache
    → render()
```

### Directory Resolution Logic

```
User selects folder
    │
    ├─ Does it contain a 'bills/' subfolder?
    │       YES → scan bills/ recursively
    │       NO  → scan selected folder recursively
    │
    └─ collectPdfs(root, maxDepth=6)
            ├─ kind === 'file' && name ends .pdf → push to list
            └─ kind === 'directory' → recurse
```

### Data Flow

```
bills[] array (in memory + localStorage)
    │
    ├─ computeStats()  → { totalKwh, avgDaily, solar, battery, ratio, totalCost }
    │
    ├─ renderCards()   → update DOM stat cards
    ├─ renderUsageChart()    → D3 bar chart
    ├─ renderStackedChart()  → D3 stacked bar
    ├─ renderDemandChart()   → D3 line chart
    ├─ renderDailyChart()    → D3 line chart
    └─ renderTable()   → HTML table
```

---

## PDF Parser — Supported Fields

The parser uses regex against the raw text extracted by PDF.js. It targets the Red Energy bill format specifically.

| Field | Regex Target | Example Value |
|-------|-------------|---------------|
| `bill_date` | `ISSUE DATE dd MMM yy` | `2026-03-09` |
| `billing_start` | `From dd Month yyyy` | `2026-02-06` |
| `billing_end` | `to dd Month yyyy` | `2026-03-05` |
| `billing_days` | `(28 days)` | `28` |
| `peak_kwh` | `Total Peak NNN $` | `115` |
| `offpeak_kwh` | `Total Off Peak NNN $` | `313` |
| `demand_kw` | `Demand N.NN KW $` | `3.24` |
| `average_daily_kwh` | `Average daily usage for this account: N.N kWh` | `15.4` |
| `total_cost` | `AMOUNT DUE (Including GST) $NNN.NN` | `173.13` |
| `avg_daily_cost` | `Average Daily Cost $N.NN` | `6.18` |

**Derived fields:**

```js
total_kwh  = peak_kwh + offpeak_kwh
solar_size = average_daily_kwh / 4          // kW
battery    = average_daily_kwh * 1.2        // kWh
```

**Filename fallback:** If `ISSUE DATE` is not found in the PDF text, the filename is parsed for a date pattern (`dd_MMM_yy` or `dd-MMM-yyyy`).

---

## Charts & Visualisations

All charts are rendered with **D3.js v7** directly into `<div>` container elements. No canvas, no external charting library.

### Design decisions
- **Band scales** for bar charts, **linear scales** for Y axes
- **CatmullRom curves** for smooth line charts
- **Stroke-dasharray animation** for line draw-on effect
- **Area fills** at 7–8% opacity for depth without noise
- **Transparent hit-rect overlay** for clean hover detection without interfering with bar transitions
- **Responsive**: all charts redraw on `window.resize` with 200ms debounce

### Colour palette

| Colour | Hex | Used for |
|--------|-----|----------|
| Cyan | `#00d4ff` | Total usage, off-peak |
| Amber | `#ffa500` | Peak usage, cost |
| Green | `#39d353` | Daily average, battery |
| Purple | `#a371f7` | Demand |
| Red | `#ff6b6b` | Total spend card |
| Gold | `#f9c74f` | Solar |

---

## Print / PDF Report

Click the **🖨 print icon** in the header to open the report in a new tab.

From there, click **"Print / Save as PDF"** — Chrome's print dialog lets you save directly as PDF with layout preserved.

### Report pages

```
Cover ─────────── Dark branded cover, period, 3 headline stats
Page 1 ─────────── Executive Summary (stat grid + insights table)
Page 2 ─────────── Usage Analysis (2 charts + per-bill split table)
Page 3 ─────────── Demand & Daily Trends (3 demand stats + 2 charts)
Page 4 ─────────── Solar & Battery (sizing cards + savings estimate + TOU tips)
Page 5 ─────────── Complete Bill History (full table with totals row)
```

Charts are captured from the live dashboard SVGs at print time using `XMLSerializer` and inlined into the report HTML. CSS variable colours are substituted for print-safe hex values during capture.

### Print tips
- In Chrome's print dialog, set **Margins: None** and enable **Background graphics** for best results
- Use **A4** paper size
- **Save as PDF** preserves all colours and chart graphics

---

## Solar & Battery Analysis

Recommendations use standard Australian solar industry formulas:

```
Solar system size (kW)  = Average daily usage (kWh) ÷ 4 peak sun hours
Battery size (kWh)      = Average daily usage (kWh) × 1.2
```

The `× 1.2` battery multiplier adds a 20% buffer to cover overnight usage plus morning demand before solar generation begins.

**Queensland context:** QLD typically receives 4–5 peak sun hours/day, making it one of Australia's best solar locations. The app uses 4 hours as a conservative baseline.

**Indicative savings estimate** (in the print report):
```
Annual generation  = solar_kw × 4 × 365
Self-consumption   = ~70% offset of grid usage
Feed-in income     = exported kWh × $0.10/kWh (indicative)
```

> ⚠️ All estimates are indicative only. Consult a Clean Energy Council accredited installer for site-specific advice.

---

## PWA — Offline & Install

### Service Worker (`service-worker.js`)

Uses a **stale-while-revalidate** strategy for CDN assets and **cache-first** for local files:

```
Install  → cache all static assets (Bootstrap, PDF.js, D3, Material Icons, fonts)
Activate → delete old cache versions
Fetch    → serve from cache; revalidate in background
```

### Install prompt

When Chrome detects the app is installable (manifest + service worker), an **Install** button appears in the header. Clicking it triggers the native `beforeinstallprompt` flow — the app can be added to your desktop or home screen and runs in standalone window mode.

### Data persistence

| Data | Storage | Cleared by |
|------|---------|-----------|
| Parsed bills | `localStorage` key `energy_bills` | "Clear" button |
| Folder handle | `IndexedDB` db `energylens`, store `handles` | "Clear" button |
| Theme preference | `localStorage` key `theme` | Browser clear |

---

## Browser Requirements

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 86+ | ✅ Full | Recommended |
| Edge 86+ | ✅ Full | |
| Opera 72+ | ✅ Full | Chromium-based |
| Firefox | ❌ No | No File System Access API |
| Safari | ❌ No | No File System Access API |

The app detects API availability on load and shows a clear error message if the browser is unsupported.

---

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| [Bootstrap](https://getbootstrap.com/) | 5.3.3 | Layout, grid, modals |
| [D3.js](https://d3js.org/) | 7.8.5 | All charts and visualisations |
| [PDF.js](https://mozilla.github.io/pdf.js/) | 3.11.174 | PDF text extraction |
| [Google Material Icons](https://fonts.google.com/icons) | latest | UI icons |
| [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed) | — | Display / heading font |
| [IBM Plex Mono](https://fonts.google.com/specimen/IBM+Plex+Mono) | — | Body / data font |

**No build tools. No framework. No npm.** All libraries loaded from CDN; cached by the service worker for offline use.

---

## The Prompt

The following prompt was used to generate this entire application with [Claude](https://claude.ai). You can use it to regenerate, extend, or fork the app.

---

```
You are a senior frontend engineer.

Goal
Create a Progressive Web App (PWA) that reads electricity bill PDFs directly in the
browser and builds an energy usage dashboard. The app must not use Python or any backend.
All processing happens in the browser.

Environment
- Static web app only
- Runs locally from a folder containing multiple PDF bills
- Use PDF.js to read the PDFs
- Use D3.js for charts
- Use Bootstrap 5 for layout
- Use Google Material Icons for UI icons
- Implement as a PWA with offline capability

Input
- Multiple electricity bill PDFs located in a subfolder called bills/
- Filenames contain the bill date
- Bills follow the Red Energy / Australian electricity bill structure

Example fields inside the PDF:
- Issue Date
- Billing period
- Peak kWh
- Off Peak kWh
- Demand (kW)
- Average daily usage
- Total electricity charges

Processing
Use PDF.js to extract text from each PDF and parse the following values using regex:

Fields to extract:
- bill_date
- billing_start
- billing_end
- peak_kwh
- offpeak_kwh
- demand_kw
- average_daily_kwh
- total_cost

Derived values
- total_kwh = peak_kwh + offpeak_kwh
- total_usage_all_bills
- monthly_usage
- average_monthly_usage
- peak_vs_offpeak_ratio
- estimated_daily_usage

Solar estimation
Using Australian averages:
- solar_size_kw = average_daily_kwh / 4
- battery_size_kwh = average_daily_kwh * 1.2

Frontend requirements

Single page app: index.html

Libraries
- Bootstrap 5
- Google Material Icons
- PDF.js
- D3.js

UI layout

Header
- App title
- Material icon
- Dark/light mode toggle

File loader
- Auto-load all PDFs from bills/ subfolder using the File System Access API
- Persist the directory handle in IndexedDB so the app auto-loads on every visit
- Recursive scan — find all PDFs in the selected folder and all subfolders
- If user selects a parent folder that contains a bills/ subfolder, auto-navigate into it
- Show a clean first-run permission screen on first visit
- Show a reconnect banner (not full-screen) if permission needs re-confirming

Summary cards (Bootstrap grid)
Each card has an icon and value:
- Total kWh Usage
- Average Daily Usage
- Estimated Solar System Size
- Estimated Battery Size
- Peak vs Off Peak Ratio
- Total Spend

Charts using D3.js
1. Monthly energy usage — bar chart, X=bill date, Y=total kWh
2. Peak vs Off Peak — stacked bar chart
3. Demand trend — line chart (kW)
4. Daily average trend — line chart
All charts must support tooltips, hover highlight, smooth transitions.

Data table
Columns: Bill Date, Peak kWh, Off-Peak kWh, Total kWh, Demand kW, Avg Daily kWh, Cost

Analysis tool modals
Four clickable cards each open a Bootstrap modal with a D3 chart:
- Solar sizing (bar chart across system sizes, highlight recommended)
- Battery sizing (bar chart across storage sizes, highlight recommended)
- Usage history (daily average line chart)
- Cost analysis (bill-by-bill bar chart)

Print / PDF report
A print button in the header opens a new browser tab containing a full 5-page
print-ready report including:
- Branded cover page with headline stats
- Executive summary (stat grid + key insights table)
- Usage analysis (charts captured as live SVGs + per-bill split table with inline bars)
- Demand and daily trends (demand stat boxes + charts)
- Solar and battery recommendations (sizing cards + indicative savings estimate + TOU tips)
- Complete bill history table with totals/averages footer row

PWA requirements
Create:
- manifest.json
- service-worker.js

Features:
- Installable PWA
- Offline capability (stale-while-revalidate for CDN, cache-first for local)
- LocalStorage caching of parsed bill data
- IndexedDB persistence of folder handle

Performance
- Discover all PDFs first (show count), then parse with per-file progress
- Handle 50+ bills
- Show 4-phase loading: Locating → Discovering → Parsing (N/total) → Done

Output files
- index.html   (all JS inline — required for file:// protocol compatibility)
- manifest.json
- service-worker.js
- styles.css
- app.js       (stub — logic stays inline)

Coding rules
- ES6
- Clean Bootstrap layout
- Modular JavaScript functions
- No backend dependencies
- Everything runs locally in the browser
- Dark/light theme via CSS custom properties
- Barlow Condensed (display) + IBM Plex Mono (body) fonts
```

---

## Contributing

Pull requests welcome. A few areas where contributions would be valuable:

- **Parser extensions** — support for other Australian energy retailers (AGL, Origin, Ausgrid, etc.)
- **Export** — CSV export of parsed bill data
- **Tariff comparison** — fetch current tariff rates from energymadeeasy.gov.au API
- **Alerts** — flag unusually high bills compared to seasonal average
- **Multi-property** — support multiple `bills/` folders / accounts

To extend the parser for a new retailer, add regex patterns in the `parseBill()` function inside `index.html`. Each bill format only needs to match the 8 core fields.

---

## License

MIT — free to use, modify, and distribute.

---

<div align="center">
  <sub>Built with ⚡ using Claude — <a href="https://claude.ai">claude.ai</a></sub>
</div>
