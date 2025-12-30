import os
import sys
import time

import requests

import clear_types
import goldens
from constants import DiffType, ClearType, NotificationType, FULL_CLEAR_EMOJI, SILVER_EMOJI, GOLDEN_EMOJI, \
    CLEAR_EMOJI, ANIMATED_GOLDEN_EMOJI, STAR_EMOJIS


def send_diff_messages_to_webhook(diff_list, gc, only_print=False):
    primary_discord_url = os.environ.get('PRIMARY_DISCORD_WEBHOOK_URL')
    secondary_discord_url = os.environ.get('SECONDARY_DISCORD_WEBHOOK_URL')

    if not primary_discord_url or not secondary_discord_url:
        print("Warning: PRIMARY_DISCORD_WEBHOOK_URL or SECONDARY_DISCORD_WEBHOOK_URL not set. Skipping notification.")
        return

    # create an "object" reference to hold golden tiers if they're required
    golden_tiers_obj = [None]

    for i, (diff_type, *values) in enumerate(diff_list):
        if i > 0 and not only_print:
            # webhooks have a rate limit of 5 requests per 2 seconds per webhook
            # send 4 requests per 2 seconds just to be safe
            time.sleep(0.5)
        msg, notif_type = diff_to_message(diff_type, values, gc, golden_tiers_obj)
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
def clear_type_to_action_tier_emoji(clear_type):
    match clear_type:
        case ClearType.NO_VIDEO | ClearType.VIDEO | ClearType.OTHER:
            return "cleared", 1, CLEAR_EMOJI
        case ClearType.CREATOR:
            return "cleared their own map,", 1, CLEAR_EMOJI
        case ClearType.NO_VIDEO_FC | ClearType.VIDEO_FC | ClearType.VIDEO_AND_FC:
            return "full cleared", 2, FULL_CLEAR_EMOJI
        case ClearType.CREATOR_FC:
            return "full cleared their own map,", 2, FULL_CLEAR_EMOJI
        case ClearType.ALL_SILVERS | ClearType.ALL_SILVERS_AND_FC:
            return "got all segments deathless in", 3, SILVER_EMOJI
        case ClearType.GOLDEN | ClearType.GOLDEN_AND_FC:
            return "GOLDENED", 4, GOLDEN_EMOJI
        case ClearType.GOLDEN_FC:
            return "FULL CLEAR GOLDENED", 5, ANIMATED_GOLDEN_EMOJI

    print(f"ERROR: unknown clear type {clear_type}")
    sys.exit(1)


def normal_clear_message(player_name, map_name, map_emoji, clear_type, gc, golden_tiers_obj):
    clear_action, _, emoji = clear_type_to_action_tier_emoji(clear_type)
    msg = (f"{emoji} {format_player_or_map_name(player_name)} {clear_action} {map_emoji} "
           f"{format_player_or_map_name(map_name)}")
    if clear_type in [ClearType.GOLDEN, ClearType.GOLDEN_AND_FC, ClearType.GOLDEN_FC]:
        if golden_tiers_obj[0] is None:
            print("Getting CLD...")
            golden_tiers_obj[0] = goldens.get_golden_tiers(gc)
        golden_tiers = golden_tiers_obj[0]
        index = 1 if clear_type == ClearType.GOLDEN_FC else 0
        if map_name in golden_tiers and golden_tiers[map_name][index]:
            msg += f" ({golden_tiers[map_name][index]})"
        else:
            print(f"WARNING: No golden tier found for map {map_name} [{'FC' if index == 1 else 'C'}]")
    return msg + "!"


def diff_to_message(diff_type, values, gc, golden_tiers_obj):
    match diff_type:
        case DiffType.ADDED_CLEAR:
            player_name, map_name, cell_value, map_difficulty = values
            map_emoji = STAR_EMOJIS[map_difficulty]
            clear_type = clear_types.cell_value_to_clear_type(cell_value)
            if clear_type == ClearType.OTHER:
                return (f"⚠️ An unrecognized value ({cell_value}) was added to "
                        f"{format_player_or_map_name(player_name)}'s cell for "
                        f"{map_emoji} {format_player_or_map_name(map_name)}!",
                        NotificationType.SECONDARY)
            else:
                return (normal_clear_message(player_name, map_name, map_emoji, clear_type, gc, golden_tiers_obj),
                        NotificationType.PRIMARY)

        case DiffType.REMOVED_CLEAR:
            player_name, map_name, old_cell_value, map_difficulty = values
            clear_type = clear_types.cell_value_to_clear_type(old_cell_value)
            map_emoji = STAR_EMOJIS[map_difficulty]
            return (f"🔴 {format_player_or_map_name(player_name)}'s clear of {map_emoji} "
                    f"{format_player_or_map_name(map_name)} was REMOVED (was {old_cell_value} ({clear_type}))!",
                    NotificationType.SECONDARY)

        case DiffType.CHANGED_CLEAR:
            player_name, map_name, old_cell_value, new_cell_value, map_difficulty = values
            old_clear_type = clear_types.cell_value_to_clear_type(old_cell_value)
            new_clear_type = clear_types.cell_value_to_clear_type(new_cell_value)
            _, old_tier, _ = clear_type_to_action_tier_emoji(old_clear_type)
            _, new_tier, _ = clear_type_to_action_tier_emoji(new_clear_type)
            map_emoji = STAR_EMOJIS[map_difficulty]
            if new_tier > old_tier:
                return (normal_clear_message(player_name, map_name, map_emoji, new_clear_type, gc, golden_tiers_obj),
                        NotificationType.PRIMARY)
            else:
                return (f"🟡 {format_player_or_map_name(player_name)}'s clear of {map_emoji} "
                        f"{format_player_or_map_name(map_name)} was changed from "
                        f"{old_cell_value} ({old_clear_type}) to {new_cell_value} ({new_clear_type})",
                        NotificationType.SECONDARY)

        case DiffType.ADDED_PLAYER:
            player_name, = values
            return f"👋 A new player was added: {format_player_or_map_name(player_name)}", NotificationType.PRIMARY
        case DiffType.REMOVED_PLAYER:
            player_name, = values
            return f"🪦 A player was removed: {format_player_or_map_name(player_name)}", NotificationType.SECONDARY
        case DiffType.RENAMED_PLAYER:
            old_player_name, new_player_name = values
            return (f"🤷 Player {format_player_or_map_name(old_player_name)} was RENAMED to "
                    f"{format_player_or_map_name(new_player_name)}!",
                    NotificationType.SECONDARY)

        case DiffType.ADDED_MAP:
            map_name, map_difficulty = values
            map_emoji = STAR_EMOJIS[map_difficulty]
            return (f"🗺️ A new map was added: {map_emoji} {format_player_or_map_name(map_name)}",
                    NotificationType.PRIMARY)
        case DiffType.REMOVED_MAP:
            map_name, = values
            return f"❌ A map was removed: {format_player_or_map_name(map_name)}", NotificationType.PRIMARY
        case DiffType.RENAMED_MAP:
            old_map_name, new_map_name, map_difficulty = values
            map_emoji = STAR_EMOJIS[map_difficulty]
            return (f"📋 Map {format_player_or_map_name(old_map_name)} was RENAMED to "
                    f"{map_emoji} {format_player_or_map_name(new_map_name)}!",
                    NotificationType.SECONDARY)

    print(f"ERROR: unknown diff type {diff_type} (values: {values})")
    sys.exit(1)
