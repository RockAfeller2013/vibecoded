# MiniMax-H3 / h3.c on Apple Silicon — Setup Guide

Target machine: **Apple Silicon M5 Pro, 24 GB unified memory**, everything installed to `/Volumes/Disk2`.

Upstream project: https://github.com/antirez/h3.c
Model: https://huggingface.co/MiniMaxAI/MiniMax-H3

This guide goes with **`install_h3.sh`** — a single standalone script (no Homebrew) that builds `h3.c` and generates the helper scripts referenced below.

---

## What was checked before writing this

Your draft script was close, but two things were verified and fixed against current upstream sources:

1. **FFmpeg source.** The draft used `evermeet.cx`, which only publishes **Intel x86_64** binaries. On an Apple Silicon Mac those would run under Rosetta 2 at best, or fail Gatekeeper outright. The installer now pulls **native arm64** static builds from OSXExperts.NET, and adds the `xattr -dr com.apple.quarantine` + `codesign -s -` steps Apple Silicon requires for any downloaded (unsigned) binary — the original script was missing this too.
2. **Model repository and download command.** `MiniMaxAI/MiniMax-H3` is correct. The repo hosts the native `FL2VA/` and `Ref2VA/` checkpoint trees **side by side with a full Diffusers-format copy** of the same weights, so a plain `hf download MiniMaxAI/MiniMax-H3 --local-dir ...` would pull both — likely an enormous, mostly-redundant download. The installer instead uses the `--include` filters from the official model card to fetch only the native trees h3.c expects.

Everything else in your draft (the `--ssd-streaming` numbers, the `--show` memory cost, `make -j`, the FL2VA/Ref2VA layout, `./h3 --info -d ./MiniMax-H3`) matched the current upstream README and was kept.

---

## Prerequisites

- Apple Silicon Mac (arm64), macOS with Xcode Command Line Tools (the script offers to install these if missing)
- `/Volumes/Disk2` mounted with enough free space (see [Disk space](#disk-space-heads-up) below)
- A Hugging Face account, for the model download step

Nothing else needs to be pre-installed — `git`, `make`, `clang`, `unzip`, `tar`, `shasum`, and `python3` are checked for and are all part of the Command Line Tools / base macOS.

## Running the installer

```bash
chmod +x install_h3.sh
./install_h3.sh
```

This will, in order:

1. Verify you're on arm64 macOS with `/Volumes/Disk2` present
2. Check for / offer to install Xcode Command Line Tools
3. Clone (or update) `h3.c` into `/Volumes/Disk2/Projects/MiniMax-H3/h3.c`
4. Download native arm64 FFmpeg/FFprobe, verify their checksum, strip quarantine, ad-hoc sign them
5. Build `h3` with `make -j<core count>`
6. Generate `env.sh` and the helper scripts described below

Re-running the script later is safe — it updates the existing checkout instead of re-cloning, and skips FFmpeg/FFprobe if already installed.

## Generated scripts

All of these are written into `/Volumes/Disk2/Projects/MiniMax-H3/`:

| Script | Purpose |
|---|---|
| `env.sh` | Sets `H3_HOME`, `H3_MODEL_DIR`, `H3_OUTPUT_DIR`, `PATH`, etc. Sourced by every other script. |
| `download_model.sh [fl2va\|ref2va\|both]` | Downloads the model (default: both task families) |
| `check_model.sh` | Confirms the checkpoint layout and runs `h3 --info` to validate the Metal device |
| `run_fast.sh` | 4 steps / 50 layers / reuse 1 — fastest iteration |
| `run_balanced.sh` | 20 steps / 45 layers / reuse 2 — day-to-day use |
| `run_quality.sh` | 20 steps / 50 layers / reuse 1 — better quality, still reasonably fast |
| `run_reference.sh` | 50 steps / 50 layers / reuse 1 — slow, use as an A/B oracle |
| `run_interactive.sh` | Starts an interactive session with `--ssd-streaming` on |
| `system_info.sh` | Prints host/build info |

Every `run_*.sh` script takes an optional prompt as its first argument, e.g. `./run_fast.sh "a hummingbird hovering over red flowers"`.

**Note on the preset names:** "Fast / Balanced / Quality / Reference" are labels of convenience for this install, not official upstream terms. Upstream's own README is slightly inconsistent about which combination counts as the CLI's "default" versus its recommended starting point — the four presets above are all valid, upstream-documented points along that same speed/quality dial, just picked out and named for convenience here.

## Why every preset uses `--ssd-streaming` and skips `--show`

- `--ssd-streaming` keeps only a couple of DiT blocks resident and streams the rest from disk. On your hardware class this drops tracked DiT storage from tens of GB down to roughly 2 GB at 512×512 — necessary headroom on a 24 GB machine, at some throughput cost.
- `--show` keeps an extra preview VAE resident (on the order of 10 GB), which isn't worth trading away on this machine. Omit `--ssd-streaming` from a command if you ever want to add `--show` back in on a spot check — just expect much higher peak memory use.
- `--reuse`/`--core-reuse` are mutually exclusive, and `--ssd-streaming` can't be combined with `--use-int8-row-fc2`. None of the generated scripts touch the second flag of either pair, so there's nothing to reconcile here — worth knowing only if you start hand-editing the commands.

## Model download

```bash
/Volumes/Disk2/Projects/MiniMax-H3/download_model.sh          # both task families
/Volumes/Disk2/Projects/MiniMax-H3/download_model.sh fl2va    # text / first-last-frame → video only
/Volumes/Disk2/Projects/MiniMax-H3/download_model.sh ref2va   # reference-conditioned only
```

The model is gated behind the **MiniMax H3 Community License**. Before the first download:

1. Open https://huggingface.co/MiniMaxAI/MiniMax-H3 in a browser, log in, and accept the license if prompted.
2. Run `hf auth login` (the script installs `hf` into a local virtualenv the first time it runs), or export `HF_TOKEN=hf_xxx` before running the download script.

### Disk space heads-up

Each of `FL2VA/` and `Ref2VA/` is a **self-contained** checkpoint — it bundles its own copy of the transformer *and* the Qwen3-VL-32B text encoder used for prompt understanding. Downloading **both** task families means downloading that encoder twice. Check the file sizes on the [Hugging Face Files tab](https://huggingface.co/MiniMaxAI/MiniMax-H3/tree/main) and your free space on `/Volumes/Disk2` before committing to `both`; if space is tight, start with `fl2va` only, which covers text-to-video and first/last-frame conditioning.

## Validating the install

```bash
/Volumes/Disk2/Projects/MiniMax-H3/check_model.sh
```

This confirms `model_index.json` plus whichever of `FL2VA/`/`Ref2VA/` you downloaded are present, then runs `h3 --info` to confirm the model layout and print the selected Metal device — this step does not map the full weights, so it's fast.

## First generations

```bash
/Volumes/Disk2/Projects/MiniMax-H3/run_fast.sh
/Volumes/Disk2/Projects/MiniMax-H3/run_balanced.sh
```

Output lands in `/Volumes/Disk2/Projects/MiniMax-H3/outputs/`, timestamped per run.

## Resolution and duration limits (for reference)

- Width and height must each be a multiple of 32, at least 32, with `width * height <= 768 * 1344`. `512x512` is the best-validated development size.
- Frame counts snap upward to `5 + 17*n`: 22, 39, 56, 107, 243, 362 frames (≈0.92s, 1.63s, 2.33s, 4.46s, 10.13s, 15.08s at 24 fps). `--seconds N` is a shorthand that rounds to the same table; `--frames` and `--seconds` are mutually exclusive.
- `--seed` defaults to 42.

For the full flag reference — token reduction, internal-canvas rendering, int8 paths, reference-image/video/audio flags, and so on — run `./h3 --help` after building, or see the [upstream README](https://github.com/antirez/h3.c).

## Troubleshooting

- **"cannot be opened because the developer cannot be verified"** on FFmpeg/FFprobe: the installer already strips quarantine and ad-hoc signs both binaries. If you see this anyway, re-run the two commands manually: `xattr -dr com.apple.quarantine <path>` then `codesign -s - <path>`.
- **Checksum warning during install**: OSXExperts.NET's filenames are versioned, so if they've shipped a newer FFmpeg build since this guide was written, the checksum this script has recorded will no longer match — that's expected, not necessarily a problem. Compare manually against the values published at http://www.osxexperts.net/ if you want to be sure.
- **Download fails with an auth-looking error**: almost always means the license hasn't been accepted on the model page yet, or `hf auth login` hasn't been run. See [Model download](#model-download) above.
- **404 on the FFmpeg/FFprobe URLs**: OSXExperts.NET names files by major version (currently `ffmpeg9arm.zip` / `ffprobe9arm.zip`). If they've moved to a new major version, grab the current "Apple Silicon" links from http://www.osxexperts.net/ and update `FFMPEG_URL`/`FFPROBE_URL` (and the two checksum constants) near the top of `install_h3.sh`.
