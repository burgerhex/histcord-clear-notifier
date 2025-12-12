import os
import requests
import sys
from datetime import datetime

from constants import DiffType


def send_diff_messages_to_webhook(diff_list):
    discord_url = os.environ.get('DISCORD_WEBHOOK_URL')

    if not discord_url:
        print("Warning: DISCORD_WEBHOOK_URL not set. Skipping notification.")
        return

    header = f"--- 📜 Sheet Monitor Report ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---"

    content = header
    chunks = []

    for diff_type, *values in diff_list:
        msg = diff_to_message(diff_type, values)
        if len(content) + len(msg) + 1 > 1900:
            chunks.append(content)
            content = header
        content += "\n" + msg
    chunks.append(content)

    for chunk in chunks:
        payload = {"content": chunk}
        try:
            requests.post(discord_url, json=payload)
        except Exception as e:
            print(f"ERROR: Failed to send Discord message: {e}")


def diff_to_message(diff_type, values):
    match diff_type:
        case DiffType.ADDED_CLEAR:
            return f"🎉 `{values[0]}` cleared {values[1]}! ({values[2]})"
        case DiffType.REMOVED_CLEAR:
            return f"🔴 `{values[0]}`'s clear of {values[1]} was REMOVED (was {values[2]})"
        case DiffType.CHANGED_CLEAR:
            return f"🟡 `{values[0]}`'s clear of {values[1]} was changed ({values[2]} -> {values[3]})"
        case DiffType.ADDED_PLAYER:
            return f"👋 new player! `{values[0]}`"
        case DiffType.REMOVED_PLAYER:
            return f"🪦 removed player :( `{values[0]}`"
        case DiffType.ADDED_MAP:
            return f"🗺️ new map! {values[0]}"
        case DiffType.REMOVED_MAP:
            return f"❌ removed map :( {values[0]}"

    print(f"ERROR: unknown diff type {diff_type}")
    sys.exit(1)