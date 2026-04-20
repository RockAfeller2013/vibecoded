# 📷 Photostream

A single-file NAS media gallery that connects directly to your **Synology** via the File Station API.  
No backend, no install, no build tools — just open `index.html` in a browser.

- [Chat link(https://claude.ai/chat/061a1f22-50c8-4041-a0b0-ca0240c81f39)]
- Easy to select multiple images using mouse and download files to local disk.
- Display / Sort content by Month / Year
- API - https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf
- Snology Wraper - https://github.com/N4S4/synology-api
- Synaudit - https://github.com/gaetangr/synaudit?tab=readme-ov-file#disclaimer
- WebAPI - https://kb.synology.com/fr-fr/DG/DSM_Login_Web_API_Guide/2
- 
- Pick by Date, 
- dont dislay if the date doesnt has got any files, it sees to show the last avaiable month
- File explorer 
- Then click search 
---

## CORS errors BYPASS

```
open -na "Google Chrome" --args \
--disable-web-security \
--user-data-dir=/tmp/chrome-dev \
--ignore-certificate-errors
```

## Features

- Connects to any Synology DSM 6 / DSM 7 NAS over HTTP or HTTPS
- Scans any folder on any volume — no Web Station required
- Uses Synology's built-in thumbnail API for fast gallery loading
- Full-resolution modal viewer with keyboard & swipe navigation
- Photos + videos in a unified view with lazy loading
- Supports HEIC, JPG, PNG, MP4, MOV and more
- Chromecast (Google Cast) streaming
- Dark / light mode toggle
- Add extra folders at runtime without editing code

---

## Quick Start

### 1. Prepare a DSM user account

> **Recommendation:** Create a dedicated read-only account. Never expose your `admin` credentials in a file.

1. Open **DSM** → **Control Panel** → **User & Group**
2. Click **Create** → set a username (e.g. `photostream`) and a strong password
3. On the **Permissions** tab, grant **Read** permission to the shared folders you want to browse  
   *(e.g. `photo`, `video`, `homes`)*
4. On the **Applications** tab, make sure **File Station** is **allowed**
5. Click **Done**

---

### 2. Find your NAS IP / port

| Access method | Host | Port | HTTPS? |
|---|---|---|---|
| Local network (HTTP) | `192.168.1.x` or `nas.local` | `5000` | No |
| Local network (HTTPS) | `192.168.1.x` or `nas.local` | `5001` | Yes |
| Remote via DDNS | `yourname.synology.me` | `5001` | Yes |
| Reverse proxy | your custom domain | `443` | Yes |

You can confirm the port in **DSM** → **Control Panel** → **Login Portal** → **DSM** tab.

---

### 3. Edit `SYNO_CONFIG` in `index.html`

Open `index.html` in a text editor and find this block near the top of the `<script>` section:

```javascript
const SYNO_CONFIG = {
  host:     '192.168.1.x',       // ← your NAS IP or hostname
  port:     5000,                 // ← 5000 (HTTP) or 5001 (HTTPS)
  https:    false,                // ← true if using port 5001

  username: 'photostream',        // ← the DSM user you created
  password: 'yourpassword',       // ← that user's password

  folders: [
    '/volume1/photo',             // ← Synology paths to scan
    '/volume1/video',
    '/volume1/homes/admin/Drive/Photos',
  ],

  recursive:  false,   // true = scan sub-folders (slower)
  thumbnails: true,    // true = use Synology Thumb API (recommended)
  thumbSize:  'medium',// 'small' | 'medium' | 'large'
  pageSize:   500,     // files fetched per API request
};
```

Save the file.

---

### 4. Serve `index.html` over HTTP

Browsers block cross-origin `fetch()` requests made from a `file://` URL.  
You must serve `index.html` from a local HTTP server on the **same network** as your NAS.

**Python (built-in, no install needed):**

```bash
# macOS / Linux
cd /path/to/folder-containing-index.html
python3 -m http.server 8080

# Windows
cd C:\path\to\folder
python -m http.server 8080
```

Then open: **http://localhost:8080**

**Node.js (if you prefer):**

```bash
npx serve .
# or
npx http-server . -p 8080
```

**VS Code Live Server extension** also works — right-click `index.html` → *Open with Live Server*.

---

### 5. Enable CORS on your Synology (required)

The browser needs permission to call the Synology API from your localhost server.

#### Option A — DSM 7 reverse proxy (cleanest)

1. DSM → **Control Panel** → **Login Portal** → **Advanced** tab → **Reverse Proxy**
2. Add a rule:
   - Source: `http://localhost` (or whatever host you serve from)
   - Destination: `http://127.0.0.1:5000`
3. Under **Custom Header** add:
   ```
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: GET, OPTIONS
   Access-Control-Allow-Headers: Content-Type
   ```

#### Option B — Browser CORS extension (quickest for local testing)

Install **"CORS Unblock"** or **"Allow CORS"** in Chrome/Edge/Firefox and enable it while using Photostream. Disable it afterwards.

#### Option C — Serve from the NAS itself (no CORS issue)

Place `index.html` inside `/volume1/web/` on your NAS, then access it at `http://NAS_IP/index.html`. Since both the page and the API are on the same origin, CORS doesn't apply.

---

### 6. Open and scan

1. Open **http://localhost:8080** in your browser
2. Click **Scan Shares** in the toolbar
3. Photostream will:
   - Log in to your NAS (one API call)
   - List every folder in your `folders` array
   - Build the gallery using Synology's thumbnail API
4. Click any tile to open the full-resolution viewer

---

## Folder Path Reference

Synology paths always start with `/volumeN/`. Common locations:

| What you see in File Station | Synology path |
|---|---|
| `photo` shared folder | `/volume1/photo` |
| `video` shared folder | `/volume1/video` |
| Your home folder | `/volume1/homes/YOUR_USERNAME` |
| Synology Photos (personal) | `/volume1/homes/YOUR_USERNAME/Photos` |
| Synology Photos (shared) | `/volume1/photo` |
| Any other shared folder | `/volume1/SHARE_NAME` |

> **Tip:** Hover over a folder in File Station → right-click → **Properties** to confirm the exact path.

---

## Adding Folders at Runtime

You don't have to edit the file every time. Use the **Folders panel** (top-right storage icon):

1. Click the **storage** icon (🗄) in the top-right corner
2. Type a Synology path in the input at the bottom, e.g. `/volume1/photo/holidays/2024`
3. Click **Add**
4. Hit **Scan Shares** again to include the new folder

> Runtime additions are not saved between page refreshes. Edit `SYNO_CONFIG.folders` to make them permanent.

---

## Recursive Scanning

By default, only the top level of each folder is scanned. To include sub-folders:

```javascript
recursive: true,
```

> ⚠️ Be careful with large libraries — a folder with thousands of sub-directories will make many sequential API calls and can take a long time.

---

## Thumbnail Settings

| Setting | Effect |
|---|---|
| `thumbnails: false` | Gallery loads full images (slow, high bandwidth) |
| `thumbnails: true, thumbSize: 'small'` | 120 px tiles — fastest, lowest quality |
| `thumbnails: true, thumbSize: 'medium'` | 320 px tiles — good balance ✅ |
| `thumbnails: true, thumbSize: 'large'` | 1280 px tiles — high quality, more bandwidth |

Thumbnails are generated **on the NAS** by DSM and cached. The first scan of a large library may be slow; subsequent scans will be instant.

> **HEIC / HEIF photos:** Synology generates JPEG thumbnails for HEIC files automatically. If you see broken tiles in the gallery, it may mean DSM hasn't indexed that folder yet — open Synology Photos once to trigger indexing.

---

## Chromecast

Chromecast requires the page to be served over **HTTPS** (browser requirement for the Cast SDK).

**Quick local HTTPS with `mkcert`:**

```bash
# 1. Install mkcert
brew install mkcert   # macOS
# or: https://github.com/FiloSottile/mkcert

# 2. Install local CA
mkcert -install

# 3. Generate certs for localhost
mkcert localhost

# 4. Serve with Python (or any HTTPS server)
python3 -c "
import ssl, http.server
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain('localhost.pem', 'localhost-key.pem')
h = http.server.HTTPServer(('', 8443), http.server.SimpleHTTPRequestHandler)
h.socket = ctx.wrap_socket(h.socket, server_side=True)
h.serve_forever()
"
```

Then open **https://localhost:8443**.

Once on HTTPS, click the **Cast** button in the toolbar to pick a Chromecast device. Each photo or video card also has an individual cast icon on hover.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Wrong username or password" toast | Bad credentials | Double-check `username` / `password` in `SYNO_CONFIG` |
| "Permission denied" toast | User has no File Station access | DSM → Control Panel → User → Applications → allow File Station |
| "Network error — HTTP 0" or fetch fails silently | CORS blocked | See [Enable CORS](#5-enable-cors-on-your-synology-required) above |
| Gallery tiles are all broken | Thumbnails not generated yet | Open **Synology Photos** once to trigger indexing; or set `thumbnails: false` temporarily |
| No items found despite correct path | Path is wrong | Check path in File Station → Properties; must start with `/volume` |
| Scan never completes | Very large folder | Increase `pageSize` or reduce scope; enable `recursive: false` |
| Cast button does nothing | Page not on HTTPS | Serve over `https://` — see [Chromecast](#chromecast) above |
| HEIC images don't show full-res | Safari-only format | HEIC works in Safari; other browsers show the DSM-generated JPEG thumbnail |

---

## Security Notes

- **Do not expose `index.html` to the internet** with credentials hardcoded inside it.
- For remote access, set up Synology's **VPN** or use **Tailscale** and access your NAS over the private tunnel.
- The DSM session (SID) is kept in memory only — it is never written to `localStorage` or cookies.
- The SID is invalidated when you close the tab (`beforeunload` calls logout).
- For shared computers, use a read-only DSM account so no writes are possible even if the SID is leaked.

---

## File Structure

```
photostream/
└── index.html      ← Everything. CSS, HTML, JS — all inline.
└── README.md       ← This file.
```

---

## API Reference (for developers)

Photostream uses these Synology File Station API endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /webapi/auth.cgi` — `SYNO.API.Auth` | Login / logout, returns SID |
| `GET /webapi/entry.cgi` — `SYNO.FileStation.List` | List files in a folder (paginated) |
| `GET /webapi/entry.cgi` — `SYNO.FileStation.Thumb` | Fetch thumbnail JPEG |
| `GET /webapi/entry.cgi` — `SYNO.FileStation.Download` | Download / stream full file |

Full API documentation: [Synology File Station API Guide (PDF)](https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf)

---

*Photostream is a client-side tool intended for personal, local-network use.*
