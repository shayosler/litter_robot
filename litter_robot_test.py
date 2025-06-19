#!/usr/bin/env python3
import asyncio
from lr_credentials import lr_username, lr_password
from pylitterbot import Account
from pylitterbot import exceptions as lr_exceptions


async def main():
    # Create an account.
    account = Account()

    try:
        # Connect to the API and load robots.
        print(f"Connecting to account for {lr_username}...")
        await account.connect(username=lr_username,
                              password=lr_password,
                              load_robots=True)

        # Print robots associated with account.
        print("Robots:")
        for robot in account.robots:
            print(robot)
            if robot.serial == "LR4C515746":
                print("Found olive's robot")
            print(f"Is online: {robot.is_online}")
    except lr_exceptions.LitterRobotLoginException:
        print(f"Failed to connect to account for {lr_username}...")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
    finally:
        # Disconnect from the API.
        await account.disconnect()


if __name__ == "__main__":
    print(f"username: {lr_username}\npassword: {lr_password}")
    asyncio.run(main())
