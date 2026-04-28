#!/bin/bash
set -e

DEST="models/qwen-image-edit"

echo "Downloading Qwen/Qwen-Image-Edit-2511 to $DEST ..."
python3 - <<EOF
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="Qwen/Qwen-Image-Edit-2511",
    local_dir="$DEST",
)
EOF
echo "Done."
