#!/usr/bin/env python3
# Read Olive's weight history from the litter robot
# Updates a Google sheet with new data
#
# For Litter Robot authentication can come from either a file or environment
# variables. The script will attempt to load variables lr_username and
# lr_password from a file called lr_credentials.py. It will also look for
# environment variables LITTER_ROBOT_USER and LITTER_ROBOT_PASSWORD. If either
# environment variable is defined its value will be used. Otherwise the values
# read from the file will be used.
#
# Google sheets authentication requires the environment variable
# GOOGLE_APPLICATION_CREDENTIALS to point to a valid json file containing a key
# for an account to use to access the Sheets API
#
# Alternatively, modify the script to use get_creds_manual(), which requires a
# file credentials.json with the OAuth2 credentials for the Sheets API
#
# Uses https://github.com/natekspencer/pylitterbot/tree/main

import asyncio
import os.path
from datetime import datetime, timezone

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pylitterbot as plb

lr_username = "iwishiwuzskiing@gmail.com"
lr_password = None
try:
    from lr_credentials import lr_username, lr_password
except ImportError:
    print("Did not find Litter Robot credentials file")


SPREADSHEET_ID = "1MfZeel4GIVfo-u4UpIzQ0s49yd-_1DnHFyGsok08-SE"
ROBOT_SERIAL = "LR4C515746"


def get_creds_automatic():
    """
    Automatic auth flow
    Set GOOGLE_APPLICATION_CREDENTIALS environment variable to the location
    of the credentials file for the service account to use
    """
    creds, _ = google.auth.default()
    return creds


def get_creds_manual():
    """
    "Manual" authentication flow. Ask user to authenticate,
    then cache credentials
    """

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
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
    return creds


def setup_sheets():
    """
    Set up the sheets API, authorizing if necessary
    """
    creds = get_creds_automatic()
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


async def get_weight_history(user: str,
                             pw: str,
                             pet_name: str):# -> list[plb.WeightMeasurement]:
    # Create an account.
    account = plb.Account()
    weights = None
    try:
        # Connect to the API and load robots.
        print(f"Connecting to Litter Robot account for {user}...")
        await account.connect(username=user,
                              password=pw,
                              load_robots=True,
                              load_pets=True)

        # Print robots associated with account.
        print("Robots:")
        for robot in account.robots:
            print(robot)
            print(f"Is online: {robot.is_online}")
            if robot.serial == ROBOT_SERIAL and not robot.is_online:
                print("Robot is not online, exiting")
                raise RuntimeError("Robot is not online")

        olive = get_pet(account, pet_name)
        if olive:
            weights = await olive.fetch_weight_history()
        else:
            print(f"Failed to find pet '{pet_name}'")
    except:
        print(f"Failed to connect to account for {user}...")
        raise
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
        raise


async def main():
    name = "Olive"

    env_lr_user = os.getenv("LITTER_ROBOT_USER")
    env_lr_pw = os.getenv("LITTER_ROBOT_PASSWORD")
    lr_u = env_lr_user if env_lr_user else lr_username
    lr_pw = env_lr_pw if env_lr_pw else lr_password
    weights = await get_weight_history(user=lr_u,
                                       pw=lr_pw,
                                       pet_name=name)
    if not weights:
        print(f"Failed to get weight measurements for {name}")
        exit(1)

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
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
