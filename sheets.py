import json
import os
import sys

import gspread
from google.oauth2.service_account import Credentials

from constants import MIN_REQUIRED_ROWS

_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def authenticate_gspread():
    creds_json_string = os.environ.get('GOOGLE_CREDS_JSON')

    if not creds_json_string:
        print("ERROR: GOOGLE_CREDS_JSON environment variable not found. Check GitHub Secrets.")
        sys.exit(1)

    try:
        creds_info = json.loads(creds_json_string)
    except json.JSONDecodeError:
        print("ERROR: Could not parse GOOGLE_CREDS_JSON. Ensure the secret is a valid JSON string.")
        sys.exit(1)

    try:
        creds = Credentials.from_service_account_info(
            creds_info, scopes=_SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        print(f"ERROR: Failed to authenticate with Google API: {e}")
        sys.exit(1)


def load_previous_state_from_state_sheet(gc):
    state_sheet_id = os.environ.get('STATE_SHEET_ID')

    previous_state = {}

    try:
        state_sheet = gc.open_by_key(state_sheet_id)

        state_table = state_sheet.sheet1.get_all_values()

        if not state_table:
            print("State sheet is empty; initializing empty state.")
            return state_sheet, {}
        if len(state_table) < MIN_REQUIRED_ROWS:
            print(f"ERROR: State sheet has too few rows ({len(state_table)})")
            sys.exit(1)

        player_names = state_table[0][1:]

        for data_row in state_table[1:]:
            if not data_row or not data_row[0]:
                continue

            map_name = data_row[0]

            for i, value in enumerate(data_row[1:]):
                if i < len(player_names):
                    player_name = player_names[i]
                    unique_key = (player_name, map_name)
                    previous_state[unique_key] = value.strip()

        return state_sheet, previous_state

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"ERROR: Could not find state sheet: {state_sheet_id}")
        sys.exit(1)

    except Exception as e:
        print(f"ERROR: Failed to load/create state sheet: {e}")
        sys.exit(1)


def load_current_clears_from_main_sheet(gc):
    clears_sheet_id = os.environ.get('CLEARS_SHEET_ID')
    clears_page_name = os.environ.get('CLEARS_PAGE_NAME')

    try:
        target_sh = gc.open_by_key(clears_sheet_id)
        worksheet = target_sh.worksheet(clears_page_name)
        return worksheet.get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        print(f"ERROR: Worksheet '{clears_page_name}' not found in sheet '{clears_sheet_id}'.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read target sheet: {e}")
        sys.exit(1)


def save_clears_to_state_sheet(state_sheet, state_grid):
    try:
        num_rows = len(state_grid)
        num_cols = len(state_grid[0])
        range_end = gspread.utils.rowcol_to_a1(num_rows, num_cols)

        state_sheet.sheet1.clear()
        state_sheet.sheet1.update(range_name=f'A1:{range_end}', values=state_grid, value_input_option='USER_ENTERED')
        print("Successfully saved new state.")
    except Exception as e:
        print(f"ERROR: Could not save state to sheet: {e}")
        sys.exit(1)
