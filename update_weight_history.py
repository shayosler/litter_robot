#!/usr/bin/env python3
# Read Olive's weight history from the litter robot
# Updates a Google sheet with new data
# Requires a file config.py that defines two variables, username and password
# with the credentials for the litter robot account.
# Requires a file credentials.json with the OAuth2 credentials for the sheets
# API
#
# Uses https://github.com/natekspencer/pylitterbot/tree/main

import asyncio
import os.path
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pylitterbot as plb

from config import username, password


SPREADSHEET_ID = "1MfZeel4GIVfo-u4UpIzQ0s49yd-_1DnHFyGsok08-SE"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def setup_sheets():
    """
    Set up the sheets API, authorizing if necessary
    """
    # Set up credentials
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, ask to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Set up sheets API
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    return sheet


def get_pet(account: plb.Account, name: str) -> plb.Pet | None:
    """
    Get a pet with the specified name from the
    litter robot account
    Returns None if no pet is found with the specified name
    """
    print("Pets:")
    for pet in account.pets:
        print(pet)
        if pet.name == name:
            return pet

    return None


async def get_weight_history(name: str):# -> list[plb.WeightMeasurement]:
    # Create an account.
    account = plb.Account()
    weights = None
    try:
        # Connect to the API and load robots.
        print(f"Connecting to Litter Robot account for {username}...")
        await account.connect(username=username,
                              password=password,
                              load_robots=True,
                              load_pets=True)

        # Print robots associated with account.
        print("Robots:")
        for robot in account.robots:
            print(robot)

        olive = get_pet(account, name)
        if olive:
            weights = await olive.fetch_weight_history()
        else:
            print(f"Failed to find pet '{name}'")
    except:
        print(f"Failed to connect to account for {username}...")
    finally:
        # Disconnect from the API.
        await account.disconnect()

    return weights


def update_sheet_values(sheet, range_name, values, value_input_option="RAW"):
    """
    Update some cells in a spreadsheet
    """
    try:
        body = {"values": values}
        result = (
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


async def main():
    name = "Olive"
    weights = await get_weight_history(name)
    if not weights:
        print(f"Failed to get weight measurements for {name}")
        return

    print(f"{name} weight measurements:")
    for weight in weights:
        print(f"{weight.timestamp.isoformat()}, {weight.weight}")
    print("")

    # Update google sheets
    try:
        sheet = setup_sheets()

        # Get current data
        # TODO: someday be smarter and only fetch the end of
        # the weight history
        first_data_row = 2
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID,
                 range=f"{name}!A{first_data_row}:B")
            .execute()
        )
        values = result.get("values", [])

        if values:
            rows = len(values)
            print("Stored data:")
            print("Timestamp, Weight")
            for row in values:
                print(f"{row[0]}, {row[1]}")
            # TODO: this assumes the data in the sheet stays sorted
            last_row = values[-1]
            last_timestamp = datetime.fromisoformat(last_row[0])
        else:
            rows = 0
            last_timestamp = datetime.fromtimestamp(0,
                                                    tz=timezone.utc)

        # Determine which weight measurements are new
        new_measurements = []
        for weight in weights:
            if weight.timestamp > last_timestamp:
                new_measurements.append(weight)
                print("Adding new  measurement "
                      f"[{weight.timestamp.isoformat()}, "
                      f"{weight.weight}]")
            else:
                print("Ignoring old measurement "
                      f"[{weight.timestamp.isoformat()}, "
                      f"{weight.weight}]")

        # Append new measurements
        if not new_measurements:
            print("No new measurements")
            return
        # Determine range that new data will be entered in
        first_new_row = first_data_row + rows
        last_new_row = first_new_row + len(new_measurements)
        new_range = f"{name}!A{first_new_row}:B{last_new_row}"

        # TODO: if weights reported from litter robot are not
        # sorted from earliest to latest then will need to sort
        new_measurements.sort(key=lambda w: w.timestamp)
        values = []
        for m in new_measurements:
            val = [m.timestamp.isoformat(), str(m.weight)]
            values.append(val)
            pass

        update_sheet_values(sheet, new_range, values)
    except HttpError as err:
        print(err)


if __name__ == "__main__":
    asyncio.run(main())
