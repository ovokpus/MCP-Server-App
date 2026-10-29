#!/usr/bin/env bash
# Build the Compose stack and prove the UI, the API, and the dice tool
# work together. Local mode is forced so the check does not call OpenAI.
set -euo pipefail

cd "$(dirname "$0")/.."

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
elif sudo docker info >/dev/null 2>&1; then
  DOCKER=(sudo docker)
else
  echo "Docker is not running." >&2
  exit 1
fi

"${DOCKER[@]}" compose build
AGENT_MODE=local "${DOCKER[@]}" compose up -d --wait

cleanup() {
  "${DOCKER[@]}" compose down
}
trap cleanup EXIT

curl --fail --silent --show-error http://127.0.0.1:8000/health > /tmp/mcp-health.json
python3 - <<'PY'
import json
body = json.load(open("/tmp/mcp-health.json"))
assert body["status"] == "ok", body
assert body["backend"] == "local", body
assert body["tool_count"] >= 10, body
print("health ok", body["tool_count"], "tools")
PY

curl --fail --silent --show-error http://127.0.0.1:8000/api/tools | grep -q roll_dice

curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"message":"Roll 2d6"}' > /tmp/mcp-chat.json
grep -q 'ROLLS:' /tmp/mcp-chat.json

curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/api/tools/call \
  -H 'content-type: application/json' \
  -d '{"name":"roll_dice","arguments":{"notation":"1d20"}}' | grep -q 'ROLLS:'

curl --fail --silent --show-error http://127.0.0.1:3000/ | grep -q 'MCP Server App'
curl --fail --silent --show-error http://127.0.0.1:3000/backend/health | grep -q '"backend"'

"${DOCKER[@]}" compose exec -T api python -m pytest tests -q -p no:cacheprovider

echo "Docker end-to-end checks passed."
