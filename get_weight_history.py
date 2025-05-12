#!/usr/bin/env python3
import asyncio
from config import username, password
import pylitterbot as plb


def get_pet(account: plb.Account, name: str) -> plb.Pet | None:
    print("Pets:")
    olive = None
    for pet in account.pets:
        print(pet)
        if pet.name == "Olive":
            olive = pet

    return olive



async def main():
    # Create an account.
    account = plb.Account()

    try:
        # Connect to the API and load robots.
        print(f"Connecting to account for {username}...")
        await account.connect(username=username, password=password, load_robots=True, load_pets=True)

        # Print robots associated with account.
        print("Robots:")
        for robot in account.robots:
            print(robot)

        name = "Olive"
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


if __name__ == "__main__":

    asyncio.run(main())
