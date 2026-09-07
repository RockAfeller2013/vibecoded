#!/bin/bash
#
# install_h3.sh
#
# Standalone installer for MiniMax-H3 / h3.c on Apple Silicon.
# Upstream project : https://github.com/antirez/h3.c
# Model            : https://huggingface.co/MiniMaxAI/MiniMax-H3
#
# Target hardware  : Apple Silicon M5 Pro, 24 GB unified memory
# Everything lives under /Volumes/Disk2 -- nothing touches the boot disk.
# No Homebrew is used anywhere in this script.
#
# Usage:
#   chmod +x install_h3.sh
#   ./install_h3.sh
#
set -euo pipefail

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

BASE="/Volumes/Disk2/Projects/MiniMax-H3"
SRC="$BASE/h3.c"
MODEL="$BASE/MiniMax-H3"
TOOLS="$BASE/tools"
BIN="$TOOLS/bin"
OUTPUTS="$BASE/outputs"
TMP="$BASE/tmp"
LOGS="$BASE/logs"

FFMPEG="$BIN/ffmpeg"
FFPROBE="$BIN/ffprobe"

# Native Apple Silicon (arm64) static builds. evermeet.cx is deliberately
# NOT used here: it only publishes Intel x86_64 binaries, which would only
# run on this Mac under Rosetta 2, if at all. These OSXExperts.NET links are
# versioned in the filename, so if either 404s in the future, grab the
# current "Apple Silicon" links from http://www.osxexperts.net/ and update
# the two URLs (and the two expected-checksum variables) below.
FFMPEG_URL="https://www.osxexperts.net/ffmpeg9arm.zip"
FFPROBE_URL="https://www.osxexperts.net/ffprobe9arm.zip"
FFMPEG_SHA256_EXPECTED="591260c945d0eef150e3bf82b0ef988bd36a9cecc18ff05d6679617159f0a95e"
FFPROBE_SHA256_EXPECTED="e11c17e8200b3ee4c4c186d245e2b4053f01d56957336c1817fca0b997469106"

H3_REPO_URL="https://github.com/antirez/h3.c.git"

log() { printf '\n== %s ==\n' "$1"; }

log "MiniMax-H3 / h3.c -- Apple Silicon installation"
echo "Base directory: $BASE"

# ------------------------------------------------------------
# Platform checks
# ------------------------------------------------------------

if [ "$(uname -s)" != "Darwin" ]; then
    echo "ERROR: this script targets macOS." >&2
    exit 1
fi

if [ "$(uname -m)" != "arm64" ]; then
    echo "ERROR: Apple Silicon (arm64) is required." >&2
    exit 1
fi
echo "Architecture: $(uname -m)"

if [ ! -d "/Volumes/Disk2" ]; then
    echo "ERROR: /Volumes/Disk2 was not found. Mount it and re-run." >&2
    exit 1
fi
echo "Disk2: OK ($(df -h /Volumes/Disk2 | awk 'NR==2{print $4" free"}'))"

echo "macOS: $(sw_vers -productVersion)"

if ! xcode-select -p >/dev/null 2>&1; then
    log "Apple Command Line Tools are required"
    xcode-select --install
    echo "Finish that install, then re-run: ./install_h3.sh"
    exit 0
fi
echo "Command Line Tools: $(xcode-select -p)"

for cmd in git curl make clang unzip tar shasum python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $cmd" >&2
        exit 1
    fi
done

# ------------------------------------------------------------
# Directory layout
# ------------------------------------------------------------

mkdir -p "$BASE" "$MODEL" "$TOOLS" "$BIN" "$OUTPUTS" "$TMP" "$LOGS"
log "Directory structure created under $BASE"

# ------------------------------------------------------------
# Clone / update h3.c
# ------------------------------------------------------------

log "Fetching h3.c"

if [ -d "$SRC/.git" ]; then
    echo "Updating existing checkout..."
    git -C "$SRC" fetch --all --prune
    git -C "$SRC" pull --ff-only
else
    rm -rf "$SRC"
    git clone "$H3_REPO_URL" "$SRC"
fi

echo "h3.c revision: $(git -C "$SRC" rev-parse --short HEAD)"

# ------------------------------------------------------------
# Local FFmpeg / FFprobe (native arm64, no Homebrew)
# ------------------------------------------------------------

log "FFmpeg / FFprobe"

fetch_and_install() {
    local url="$1" dest="$2" name="$3" expected_sha="$4"

    if [ -x "$dest" ]; then
        echo "$name already installed at $dest"
        return
    fi

    local workdir="$TMP/${name}-download"
    rm -rf "$workdir"
    mkdir -p "$workdir"
    (
        cd "$workdir"
        echo "Downloading $name..."
        curl --fail --location --retry 3 "$url" -o "${name}.zip"
        unzip -o "${name}.zip" >/dev/null
    )

    local found
    found="$(find "$workdir" -type f -name "$name" -perm -111 | head -n 1)"
    if [ -z "$found" ]; then
        echo "ERROR: $name executable not found in downloaded archive." >&2
        exit 1
    fi

    local actual_sha
    actual_sha="$(shasum -a 256 "$found" | awk '{print $1}')"
    if [ "$actual_sha" != "$expected_sha" ]; then
        echo "WARNING: $name checksum does not match the value this script"
        echo "         has recorded (the file at osxexperts.net may simply"
        echo "         have been updated to a newer release). Compare"
        echo "         manually against http://www.osxexperts.net/ before"
        echo "         trusting this binary."
        echo "         expected: $expected_sha"
        echo "         actual:   $actual_sha"
    fi

    cp "$found" "$dest"
    chmod +x "$dest"

    # Apple Silicon Gatekeeper: downloaded binaries are quarantined and
    # must be ad-hoc signed before they will run.
    xattr -dr com.apple.quarantine "$dest" 2>/dev/null || true
    codesign -s - "$dest" 2>/dev/null || true
}

fetch_and_install "$FFMPEG_URL" "$FFMPEG" "ffmpeg" "$FFMPEG_SHA256_EXPECTED"
fetch_and_install "$FFPROBE_URL" "$FFPROBE" "ffprobe" "$FFPROBE_SHA256_EXPECTED"

echo "FFmpeg:  $("$FFMPEG" -version | head -n 1)"
echo "FFprobe: $("$FFPROBE" -version | head -n 1)"

# ------------------------------------------------------------
# Build h3.c
# ------------------------------------------------------------

log "Building h3.c"

NPROC="$(sysctl -n hw.ncpu 2>/dev/null || echo 8)"

(
    cd "$SRC"
    make clean >/dev/null 2>&1 || true
    make -j"$NPROC"
)

if [ ! -x "$SRC/h3" ]; then
    echo "ERROR: h3 binary was not produced by the build." >&2
    exit 1
fi
echo "Built: $(ls -lh "$SRC/h3" | awk '{print $9, $5}')"

# ------------------------------------------------------------
# env.sh
# ------------------------------------------------------------

cat > "$BASE/env.sh" <<ENVEOF
#!/bin/bash
export MINIMAX_H3_HOME="$BASE"
export H3_HOME="$SRC"
export H3_MODEL_DIR="$MODEL"
export H3_OUTPUT_DIR="$OUTPUTS"
export H3_FFMPEG="$FFMPEG"
export H3_FFPROBE="$FFPROBE"
export PATH="$BIN:\$PATH"
cd "\$H3_HOME"
ENVEOF
chmod +x "$BASE/env.sh"

# ------------------------------------------------------------
# Model download helper
#
# The MiniMaxAI/MiniMax-H3 Hugging Face repository hosts the native
# FL2VA/ and Ref2VA/ checkpoint trees that h3.c expects, side by side
# with a much larger Diffusers-format copy of the same weights. The
# --include filters below fetch only the native trees h3.c needs.
#
# Each checkpoint bundles its own copy of the Qwen3-VL-32B text encoder,
# so both trees together are a very large download. Check available
# disk space and consider downloading a single task family first with
# "./download_model.sh fl2va" if you only need text/first-last-frame to
# video and not the reference-conditioned path.
# ------------------------------------------------------------

cat > "$BASE/download_model.sh" <<'MODELEOF'
#!/bin/bash
set -euo pipefail

BASE="/Volumes/Disk2/Projects/MiniMax-H3"
MODEL="$BASE/MiniMax-H3"
TOOLS="$BASE/tools"
BIN="$TOOLS/bin"
HF="$BIN/hf"

WHICH="${1:-both}"

mkdir -p "$MODEL" "$BIN"

echo "MiniMax-H3 model downloader"
echo "Target: $MODEL"
echo "Free space there: $(df -h "$MODEL" | awk 'NR==2{print $4}')"

if [ ! -x "$HF" ]; then
    echo "Installing the Hugging Face CLI into a local virtualenv..."
    python3 -m venv "$TOOLS/hf-env"
    "$TOOLS/hf-env/bin/pip" install --upgrade pip huggingface_hub
    if [ -x "$TOOLS/hf-env/bin/hf" ]; then
        ln -sf "$TOOLS/hf-env/bin/hf" "$HF"
    elif [ -x "$TOOLS/hf-env/bin/huggingface-cli" ]; then
        ln -sf "$TOOLS/hf-env/bin/huggingface-cli" "$HF"
    else
        echo "ERROR: could not find hf or huggingface-cli after install." >&2
        exit 1
    fi
fi

echo "Using: $("$HF" --version 2>&1 | head -n 1)"

echo
echo "MiniMax-H3 is released under the MiniMax H3 Community License."
echo "If this is your first download: open"
echo "  https://huggingface.co/MiniMaxAI/MiniMax-H3"
echo "in a browser, log in, and accept the license if prompted. Then run"
echo "  $HF auth login"
echo "(or export HF_TOKEN=hf_xxx) before re-running this script."
echo

case "$WHICH" in
    fl2va)
        INCLUDES=(--include "model_index.json" "FL2VA/*")
        ;;
    ref2va)
        INCLUDES=(--include "model_index.json" "Ref2VA/*")
        ;;
    both)
        INCLUDES=(--include "model_index.json" "FL2VA/*" "Ref2VA/*")
        ;;
    *)
        echo "Usage: $0 [fl2va|ref2va|both]" >&2
        exit 1
        ;;
esac

set +e
"$HF" download MiniMaxAI/MiniMax-H3 "${INCLUDES[@]}" --local-dir "$MODEL"
STATUS=$?
set -e

if [ "$STATUS" -ne 0 ]; then
    echo
    echo "Download failed (exit $STATUS)."
    echo "This is almost always a login/license-acceptance issue -- see above."
    exit "$STATUS"
fi

echo
echo "Downloaded. Top-level contents:"
find "$MODEL" -maxdepth 1 -type d | sort

echo
echo "Next: $BASE/check_model.sh"
MODELEOF
chmod +x "$BASE/download_model.sh"

# ------------------------------------------------------------
# Model / Metal validation
# ------------------------------------------------------------

cat > "$BASE/check_model.sh" <<'CHECKEOF'
#!/bin/bash
set -euo pipefail

BASE="/Volumes/Disk2/Projects/MiniMax-H3"
source "$BASE/env.sh"

echo "MiniMax-H3 model validation"

if [ ! -f "$H3_MODEL_DIR/model_index.json" ]; then
    echo "ERROR: model_index.json not found in $H3_MODEL_DIR" >&2
    exit 1
fi

FOUND_ANY=0
if [ -d "$H3_MODEL_DIR/FL2VA" ]; then
    echo "FL2VA: OK"
    FOUND_ANY=1
fi
if [ -d "$H3_MODEL_DIR/Ref2VA" ]; then
    echo "Ref2VA: OK"
    FOUND_ANY=1
fi

if [ "$FOUND_ANY" -eq 0 ]; then
    echo "ERROR: neither FL2VA/ nor Ref2VA/ was found under $H3_MODEL_DIR" >&2
    echo "Run download_model.sh first." >&2
    exit 1
fi

echo
echo "Running h3 --info..."
"$H3_HOME/h3" --info -d "$H3_MODEL_DIR"
CHECKEOF
chmod +x "$BASE/check_model.sh"

# ------------------------------------------------------------
# Run presets
#
# All four presets add --ssd-streaming: on 24 GB of unified memory the
# full BF16 DiT residency (tens of GB) will not fit, and streaming trims
# tracked DiT storage down to roughly 2 GB at 512x512, at some throughput
# cost. --show is intentionally omitted everywhere: it keeps an extra
# preview VAE resident, which is a meaningful chunk of memory on this
# machine. --reuse and --core-reuse are mutually exclusive, and
# --ssd-streaming cannot be combined with --use-int8-row-fc2; none of
# these presets touch either of those, so there's nothing to reconcile.
#
# "Fast/Balanced/Quality/Reference" below are labels of convenience for
# this install, not upstream terminology. See the "Choose a speed/quality
# preset" section of the h3.c README for the full tuning discussion.
# ------------------------------------------------------------

write_run_script() {
    local name="$1" label="$2" steps="$3" layers="$4" reuse="$5" default_prompt="$6"

    cat > "$BASE/run_${name}.sh" <<RUNEOF
#!/bin/bash
set -euo pipefail

BASE="/Volumes/Disk2/Projects/MiniMax-H3"
source "\$BASE/env.sh"
mkdir -p "\$H3_OUTPUT_DIR"

PROMPT="\${1:-${default_prompt}}"
OUTPUT="\$H3_OUTPUT_DIR/${name}-\$(date +%Y%m%d-%H%M%S).mp4"

"\$H3_HOME/h3" --profile \\
    -d "\$H3_MODEL_DIR" \\
    -p "\$PROMPT" \\
    --width 512 --height 512 \\
    --frames 22 \\
    --steps ${steps} --layers ${layers} --reuse ${reuse} \\
    --ssd-streaming \\
    -o "\$OUTPUT"

echo
echo "[${label}] Output: \$OUTPUT"
RUNEOF
    chmod +x "$BASE/run_${name}.sh"
}

write_run_script "fast" "fast" 4 50 1 \
    "A red fox walks through fresh snow in a pine forest. Medium tracking shot, natural winter light, realistic fur."

write_run_script "balanced" "balanced" 20 45 2 \
    "A red fox walks through fresh snow in a pine forest. Medium tracking shot, natural winter light, realistic fur, soft footsteps and wind."

write_run_script "quality" "quality" 20 50 1 \
    "A cinematic shot of a surfer riding inside a large blue ocean wave. One person, one surfboard, realistic water spray, natural movement, cinematic lighting."

write_run_script "reference" "reference, slow" 50 50 1 \
    "A red fox walks through fresh snow in a pine forest. Medium tracking shot, natural winter light, realistic fur, soft footsteps and wind."

# ------------------------------------------------------------
# Interactive session
# ------------------------------------------------------------

cat > "$BASE/run_interactive.sh" <<'INTERACTIVEEOF'
#!/bin/bash
set -euo pipefail

BASE="/Volumes/Disk2/Projects/MiniMax-H3"
source "$BASE/env.sh"

exec "$H3_HOME/h3" \
    -d "$H3_MODEL_DIR" \
    --width 512 --height 512 \
    --steps 6 \
    --ssd-streaming
INTERACTIVEEOF
chmod +x "$BASE/run_interactive.sh"

# ------------------------------------------------------------
# System info
# ------------------------------------------------------------

cat > "$BASE/system_info.sh" <<'INFOEOF'
#!/bin/bash
set -euo pipefail

BASE="/Volumes/Disk2/Projects/MiniMax-H3"
source "$BASE/env.sh"

echo "macOS:  $(sw_vers -productVersion)"
echo "Arch:   $(uname -m)"
echo "CPU:    $(sysctl -n machdep.cpu.brand_string)"
echo "Memory: $(sysctl -n hw.memsize | awk '{printf "%.1f GB\n", $1/1024/1024/1024}')"
echo
"$H3_HOME/h3" --help | head -n 5
echo
"$H3_FFMPEG" -version | head -n 1
"$H3_FFPROBE" -version | head -n 1
INFOEOF
chmod +x "$BASE/system_info.sh"

# ------------------------------------------------------------
# On-disk quick-reference
# ------------------------------------------------------------

cat > "$BASE/README.txt" <<TXTEOF
MiniMax-H3 / h3.c -- $BASE

Scripts:
  env.sh              source this to set up H3_HOME / H3_MODEL_DIR / PATH
  download_model.sh   [fl2va|ref2va|both]  download the model (default: both)
  check_model.sh       validate the checkpoint layout and Metal device
  run_fast.sh          4 steps  / 50 layers / reuse 1  (development)
  run_balanced.sh      20 steps / 45 layers / reuse 2  (normal use)
  run_quality.sh       20 steps / 50 layers / reuse 1  (better quality)
  run_reference.sh     50 steps / 50 layers / reuse 1  (slow, for A/B checks)
  run_interactive.sh   interactive session, --ssd-streaming on by default
  system_info.sh       print host / build info

All run scripts take an optional prompt as \$1 and use --ssd-streaming to
stay within 24 GB of unified memory. --show is deliberately not used.

Full CLI reference: $SRC/h3 --help
Upstream docs:       https://github.com/antirez/h3.c
Model card:          https://huggingface.co/MiniMaxAI/MiniMax-H3
TXTEOF

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------

log "Installation complete"
echo "h3:      $SRC/h3"
echo "FFmpeg:  $FFMPEG"
echo "FFprobe: $FFPROBE"
echo "Base:    $BASE"
echo
echo "Next steps:"
echo "  1. $BASE/download_model.sh          # or: download_model.sh fl2va"
echo "  2. $BASE/check_model.sh"
echo "  3. $BASE/run_fast.sh"
echo "  4. $BASE/run_balanced.sh"
echo "Outputs land in: $OUTPUTS"
