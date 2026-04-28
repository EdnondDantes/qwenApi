#!/bin/bash
set -e
source .env

curl -X POST https://qwen.rossiinfrastructure.ru/edit \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "image=@test_input.png" \
  -F "prompt=make the background a sunset" \
  -o result.png

echo "Saved to result.png"
