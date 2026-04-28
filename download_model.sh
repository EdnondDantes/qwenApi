#!/bin/bash
set -e

DEST="models/qwen-image-edit"

echo "Downloading dimitribarbot/Qwen-Image-Edit-int8wo to $DEST ..."
python3 - <<EOF
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="dimitribarbot/Qwen-Image-Edit-int8wo",
    local_dir="$DEST",
)
EOF
echo "Done."
