"""
create_user.py
──────────────
CLI script to manually create a user account.

Useful when ALLOW_REGISTRATION=false in .env (production lockdown)
and you need to add a new user directly from the server terminal.

Usage
─────
  python create_user.py
  python create_user.py --username alice --password MySecret123

Options
───────
  --username   Username (3-50 chars, alphanumeric + underscore)
  --password   Password (min 8 chars)
"""

import argparse
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    parser = argparse.ArgumentParser(description="Create a new expense tracker user.")
    parser.add_argument("--username", help="Username (3-50 chars)")
    parser.add_argument("--password", help="Password (min 8 chars)")
    args = parser.parse_args()

    # Interactive prompts if args not provided
    username = args.username
    password = args.password

    if not username:
        username = input("Username: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("Password: ")

    if not username or not password:
        print("❌  Username and password are required.")
        sys.exit(1)

    # Import after env is loaded
    from init_db import init_db
    from api.auth import create_user

    print("🔌  Connecting to database …")
    await init_db()

    print(f"👤  Creating user '{username}' …")
    result = await create_user(username, password)

    if "error" in result:
        print(f"❌  {result['error']}")
        sys.exit(1)

    print(f"✅  User '{result['username']}' created successfully.")
    print(f"    They can now POST to /auth/token with their credentials to get a JWT.")


if __name__ == "__main__":
    asyncio.run(main())
