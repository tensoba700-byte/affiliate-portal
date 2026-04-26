#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
CERT="$DIR/taro-bot-venv/lib/python3.14/site-packages/certifi/cacert.pem"
export SSL_CERT_FILE="$CERT"
export REQUESTS_CA_BUNDLE="$CERT"
LOG="$DIR/taro-bot.log"
exec "$DIR/taro-bot-venv/bin/python3" -u "$DIR/taro-discord-bot.py" >> "$LOG" 2>&1
