import os
import sys
import time

import requests

import clear_types
from constants import DiffType, ClearType, NotificationType


def send_diff_messages_to_webhook(diff_list, only_print=False):
    primary_discord_url = os.environ.get('PRIMARY_DISCORD_WEBHOOK_URL')
    secondary_discord_url = os.environ.get('SECONDARY_DISCORD_WEBHOOK_URL')

    if not primary_discord_url or not secondary_discord_url:
        print("Warning: PRIMARY_DISCORD_WEBHOOK_URL or SECONDARY_DISCORD_WEBHOOK_URL not set. Skipping notification.")
        return

    for i, (diff_type, *values) in enumerate(diff_list):
        if i > 0 and not only_print:
            # webhooks have a rate limit of 5 requests per 2 seconds per webhook
            # send 4 requests per 2 seconds just to be safe
            time.sleep(0.5)
        msg, notif_type = diff_to_message(diff_type, values)
        if only_print:
            print("[PRIMARY]  " if notif_type == NotificationType.PRIMARY else "[SECONDARY]", msg)
        else:
            payload = {"content": msg}
            try:
                discord_url = primary_discord_url if notif_type == NotificationType.PRIMARY else secondary_discord_url
                requests.post(discord_url, json=payload)
            except Exception as e:
                print(f"ERROR: Failed to send Discord message: {e}")


def format_player_or_map_name(value):
    # remove newlines
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")
    value = value.replace("  ", " ")
    # use backticks for monospace formatting
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
    cleaned_values = values[:]
    # only need to format the first 2 values (which will always be map and player names). should not format any further
    # ones since those will be cell values
    for i in range(min(2, len(values))):
        cleaned_values[i] = format_player_or_map_name(cleaned_values[i])
    values = cleaned_values

    match diff_type:
        case DiffType.ADDED_CLEAR:
            player_name, map_name, cell_value = values
            clear_type = clear_types.cell_value_to_clear_type(cell_value)
            if clear_type == ClearType.OTHER:
                return (f"⚠️ An unrecognized value ({cell_value}) was added to {player_name}'s cell for {map_name}!",
                        NotificationType.SECONDARY)
            else:
                clear_action, _ = clear_type_to_action_and_tier(clear_type)
                return f"🎉 {player_name} {clear_action} {map_name}!", NotificationType.PRIMARY

        case DiffType.REMOVED_CLEAR:
            player_name, map_name, old_cell_value = values
            clear_type = clear_types.cell_value_to_clear_type(old_cell_value)
            return (f"🔴 {player_name}'s clear of {map_name} was REMOVED (was {old_cell_value} ({clear_type}))!",
                    NotificationType.SECONDARY)

        case DiffType.CHANGED_CLEAR:
            player_name, map_name, old_cell_value, new_cell_value = values
            old_clear_type = clear_types.cell_value_to_clear_type(old_cell_value)
            new_clear_type = clear_types.cell_value_to_clear_type(new_cell_value)
            _, old_tier = clear_type_to_action_and_tier(old_clear_type)
            new_action, new_tier = clear_type_to_action_and_tier(new_clear_type)
            if new_tier > old_tier:
                return f"🎉 {player_name} {new_action} {map_name}!", NotificationType.PRIMARY
            else:
                return (f"🟡 {player_name}'s clear of {map_name} was changed from {old_cell_value} ({old_clear_type}) "
                        f"to {new_cell_value} ({new_clear_type})",
                        NotificationType.SECONDARY)

        case DiffType.ADDED_PLAYER:
            player_name, = values
            return f"👋 A new player was added: {player_name}", NotificationType.SECONDARY
        case DiffType.REMOVED_PLAYER:
            player_name, = values
            return f"🪦 A player was removed: {player_name}", NotificationType.SECONDARY
        case DiffType.RENAMED_PLAYER:
            old_player_name, new_player_name = values
            return f"🤷 Player {old_player_name} was RENAMED to {new_player_name}!", NotificationType.SECONDARY

        case DiffType.ADDED_MAP:
            map_name, = values
            return f"🗺️ A new map was added: {map_name}", NotificationType.PRIMARY
        case DiffType.REMOVED_MAP:
            map_name, = values
            return f"❌ A map was removed: {map_name}", NotificationType.PRIMARY
        case DiffType.RENAMED_MAP:
            old_map_name, new_map_name = values
            return f"📋 Map {old_map_name} was RENAMED to {new_map_name}!", NotificationType.SECONDARY

    print(f"ERROR: unknown diff type {diff_type} (values: {values})")
    sys.exit(1)
