#!/usr/bin/env python3
import asyncio
from config import username, password
from pylitterbot import Account


async def main():
    # Create an account.
    account = Account()

    try:
        # Connect to the API and load robots.
        print(f"Connecting to account for {username}...")
        await account.connect(username=username, password=password, load_robots=True)

        # Print robots associated with account.
        print("Robots:")
        for robot in account.robots:
            print(robot)
    except:
        print(f"Failed to connect to account for {username}...")
    finally:
        # Disconnect from the API.
        await account.disconnect()


if __name__ == "__main__":
    print(f"username: {username}\npassword: {password}")
    asyncio.run(main())
