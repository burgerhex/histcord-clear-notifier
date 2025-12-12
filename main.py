from dotenv import load_dotenv

import clears
import discord
import sheets
import timing


def main():
    with timing.Timer("Starting script!\n\n", lambda d: f"\nScript done in {d:.3f} sec!"):
        load_dotenv()

        gc = sheets.authenticate_gspread()

        with timing.Timer("Loading previous and current states... "):
            state_sheet, previous_state = sheets.load_previous_state_from_state_sheet(gc)
            current_clears_sheet = sheets.load_current_clears_from_main_sheet(gc)
            current_state = clears.get_current_state_from_sheet_values(current_clears_sheet)

        with timing.Timer("Calculating diffs... "):
            diff_list = clears.get_state_diff_list(previous_state, current_state)

        if diff_list:
            with timing.Timer("Sending Discord messages... "):
                discord.send_diff_messages_to_webhook(diff_list)
            with timing.Timer("Saving current state to state sheet... "):
                state_grid = clears.save_state_as_grid(current_state)
                sheets.save_clears_to_state_sheet(state_sheet, state_grid)
        else:
            print("No changes detected since last run.")


if __name__ == "__main__":
    main()