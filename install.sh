#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== 1. System deps ==="
apt update && apt install -y python3-pip python3-venv git git-lfs nginx certbot python3-certbot-nginx
git lfs install

echo "=== 2. Python venv ==="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt

echo "=== 3. Download models ==="
pip install huggingface_hub[cli]
mkdir -p models
huggingface-cli download Qwen/Qwen-Image --local-dir models/qwen-image
huggingface-cli download Qwen/Qwen-Image-Edit-2511 --local-dir models/qwen-image-edit

echo "=== 4. Nginx ==="
cp nginx.conf /etc/nginx/sites-available/qwen
ln -sf /etc/nginx/sites-available/qwen /etc/nginx/sites-enabled/qwen
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== 5. SSL ==="
certbot --nginx -d qwen.rossiinfrastructure.ru --non-interactive --agree-tos -m admin@rossiinfrastructure.ru

echo "=== 6. Systemd ==="
cp qwen-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable qwen-api
systemctl start qwen-api

echo "=== Done ==="
echo "API running at https://qwen.rossiinfrastructure.ru"
