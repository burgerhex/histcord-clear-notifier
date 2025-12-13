import os
import sys
import time

import requests

from constants import DiffType, ClearType, NotificationType


def send_diff_messages_to_webhook(diff_list):
    primary_discord_url = os.environ.get('PRIMARY_DISCORD_WEBHOOK_URL')
    secondary_discord_url = os.environ.get('SECONDARY_DISCORD_WEBHOOK_URL')

    if not primary_discord_url or not secondary_discord_url:
        print("Warning: PRIMARY_DISCORD_WEBHOOK_URL or SECONDARY_DISCORD_WEBHOOK_URL not set. Skipping notification.")
        return

    for i, (diff_type, *values) in enumerate(diff_list):
        if i > 0:
            # webhooks have a rate limit of 5 requests per 2 seconds per webhook
            # send 4 requests per 2 seconds just to be safe
            time.sleep(0.5)
        msg, notif_type = diff_to_message(diff_type, values)
        payload = {"content": msg}
        try:
            discord_url = primary_discord_url if notif_type == NotificationType.PRIMARY else secondary_discord_url
            requests.post(discord_url, json=payload)
        except Exception as e:
            print(f"ERROR: Failed to send Discord message: {e}")


# cell values can be player names, map names, or clear values (which are a pair)
def format_cell_value(value):
    # remove newlines
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    return f"`{value}`"


# a clear "tier" is simply a way to re-notify when clears are updated.
# for example, a non-video clear changing to a video clear would not notify because they're both tier 1,
# but a full clear changing to a golden would notify because full clear (2) is a lower tier than golden (4).
def clear_type_to_action_and_tier(clear_type):
    match clear_type:
        case ClearType.NO_VIDEO | ClearType.VIDEO | ClearType.OTHER:
            return "cleared", 1
        case ClearType.CREATOR:
            return "cleared their own map,", 1
        case ClearType.NO_VIDEO_FC | ClearType.VIDEO_FC | ClearType.VIDEO_AND_FC:
            return "full cleared", 2
        case ClearType.CREATOR_FC:
            return "full cleared their own map,", 2
        case ClearType.ALL_SILVERS | ClearType.ALL_SILVERS_AND_FC:
            return "got all segments deathless in", 3
        case ClearType.GOLDEN | ClearType.GOLDEN_AND_FC:
            return "GOLDENED", 4
        case ClearType.GOLDEN_FC:
            return "FULL CLEAR GOLDENED", 5

    print(f"ERROR: unknown clear type {clear_type}")
    sys.exit(1)


def diff_to_message(diff_type, values):
    cleaned_values = []
    # first 2 values are always strings, last 2 values are always pairs
    for i, value in enumerate(values):
        if i < 2:
            cleaned_values.append(format_cell_value(value))
        else:
            cleaned_values.append((value[0], format_cell_value(value[1])))
    values = cleaned_values

    match diff_type:
        case DiffType.ADDED_CLEAR:
            if values[2][0] == ClearType.OTHER:
                return (f"⚠️ An unrecognized value ({values[2][1]}) was added to {values[0]}'s cell for {values[1]}!",
                        NotificationType.SECONDARY)
            else:
                return (f"🎉 {values[0]} {clear_type_to_action_and_tier(values[2][0])[0]} {values[1]}!",
                        NotificationType.PRIMARY)

        case DiffType.REMOVED_CLEAR:
            return (f"🔴 {values[0]}'s clear of {values[1]} was REMOVED (was {values[2][1]} ({values[2][0]}))!",
                    NotificationType.SECONDARY)

        case DiffType.CHANGED_CLEAR:
            _, old_tier = clear_type_to_action_and_tier(values[2][0])
            new_action, new_tier = clear_type_to_action_and_tier(values[3][0])
            if new_tier > old_tier:
                return f"🎉 {values[0]} {new_action} {values[1]}!", NotificationType.PRIMARY
            else:
                return (f"🟡 {values[0]}'s clear of {values[1]} was changed from {values[2][1]} ({values[2][0]}) to "
                        f"{values[3][1]} ({values[3][0]})",
                        NotificationType.SECONDARY)

        case DiffType.ADDED_PLAYER:
            return f"👋 A new player was added: {values[0]}", NotificationType.SECONDARY
        case DiffType.REMOVED_PLAYER:
            return f"🪦 A player was removed: {values[0]}", NotificationType.SECONDARY
        case DiffType.ADDED_MAP:
            return f"🗺️ A new map was added: {values[0]}", NotificationType.PRIMARY
        case DiffType.REMOVED_MAP:
            return f"❌ A map was removed: {values[0]}", NotificationType.PRIMARY

    print(f"ERROR: unknown diff type {diff_type} (values: {values})")
    sys.exit(1)
