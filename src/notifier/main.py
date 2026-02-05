import argparse

from dotenv import load_dotenv

from .clears import get_current_state_and_maps_from_sheet_values, get_state_diff_list, save_state_as_grid
from .discord import send_diff_messages_to_webhook
from .sheets import load_previous_state_from_state_sheet, load_current_clears_from_main_sheet, \
    save_clears_to_state_sheet
from .timing import Timer


def setup_and_run():
    args = setup()
    run_notifier(args)


# noinspection PyShadowingNames
def run_notifier(args):
    with Timer("Starting script!\n\n", lambda d: f"\nScript done in {d:.3f} sec!"):
        with Timer("Loading previous and current states... "):
            state_sheet, previous_state = load_previous_state_from_state_sheet()
            current_clears_sheet = load_current_clears_from_main_sheet()
            current_state, map_difficulties = get_current_state_and_maps_from_sheet_values(current_clears_sheet)

        with Timer("Calculating diffs... "):
            diff_list = get_state_diff_list(previous_state, current_state, map_difficulties)

        if diff_list:
            with Timer("Printing messages...\n" if args.print else "Sending Discord messages... "):
                send_diff_messages_to_webhook(diff_list, args.print)
            if args.dry_run:
                print("Dry run - not saving current state to state sheet")
            else:
                with Timer("Saving current state to state sheet... "):
                    state_grid = save_state_as_grid(current_state)
                    save_clears_to_state_sheet(state_sheet, state_grid)
        else:
            print("No changes detected since last run.")


def setup():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dry-run", action="store_true",
                        help="Dry run mode - do not save diffs to state sheet")
    parser.add_argument("-p", "--print", action="store_true",
                        help="Print mode - print messages instead of sending to Discord")
    args = parser.parse_args()

    return args
