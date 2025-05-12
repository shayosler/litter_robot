#!/usr/bin/env python3
# Read Olive's weight history from the litter robot
# Update a Google sheet with new data
import asyncio
import os.path

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
    olive = None
    for pet in account.pets:
        print(pet)
        if pet.name == "Olive":
            olive = pet

    return olive


async def get_weight_history(name: str):# -> list[plb.WeightMeasurement]:
    # Create an account.
    account = plb.Account()
    weights = None
    try:
        # Connect to the API and load robots.
        print(f"Connecting to account for {username}...")
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
            print(f"{name} weights:")
            print(weights)
        else:
            print(f"Failed to find pet '{name}'")
    except:
        print(f"Failed to connect to account for {username}...")
    finally:
        # Disconnect from the API.
        await account.disconnect()

    return weights


async def main():
    name = "Olive"
#    weights = get_weight_history(name)
#    if not weights:
#        print(f"Failed to get weight history for {name}")
#        return

    # Update google sheets

    try:
        sheet = setup_sheets()

        # Get current data
        # TODO: someday be smarter and only fetch the end of
        # the weight history
        start_row = 2
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=f"{name}!A{start_row}:B")
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return

        rows = len(values)
        print(f"{rows} rows")
        print("Date, Weight")
        for row in values:
            print(f"{row[0]}, {row[1]}")

        next_row = start_row + rows
    except HttpError as err:
        print(err)


if __name__ == "__main__":

    asyncio.run(main())
