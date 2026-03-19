import os
import sys
from datetime import date
from pathlib import Path

import requests
from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError
from garth.exc import GarthException, GarthHTTPError
from getpass import getpass

def get_credentials():
    """Get email and password from environment or user input."""
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    if not email:
        email = input("Login email: ")
    if not password:
        password = getpass("Enter password: ")

    return email, password


def init_api():
    """Initialize Garmin API with authentication and token management."""
    # Configure token storage
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = Path(tokenstore).expanduser()

    # Check if token files exist
    if tokenstore_path.exists():
        token_files = list(tokenstore_path.glob("*.json"))
        if token_files:
            pass
        else:
            pass
    else:
        pass

    # First, try to log in with stored tokens
    try:
        garmin = Garmin()
        garmin.login(str(tokenstore_path))
        return garmin

    except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            GarminConnectConnectionError,
    ):
        pass

    # Loop for credential entry with retry on auth failure
    while True:
        try:
            # Get credentials
            email, password = get_credentials()

            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                mfa_code = input("Please enter your MFA code: ")

                try:
                    garmin.resume_login(result2, mfa_code)

                except GarthHTTPError as garth_error:
                    # Handle specific HTTP errors from MFA
                    error_str = str(garth_error)
                    if "429" in error_str and "Too Many Requests" in error_str:
                        sys.exit(1)
                    elif "401" in error_str or "403" in error_str:
                        continue
                    else:
                        # Other HTTP errors - don't retry
                        sys.exit(1)

                except GarthException:
                    continue

            # Save tokens for future use
            garmin.garth.dump(str(tokenstore_path))
            return garmin

        except GarminConnectAuthenticationError:
            # Continue the loop to retry
            continue

        except (
                FileNotFoundError,
                GarthHTTPError,
                GarminConnectConnectionError,
                requests.exceptions.HTTPError,
        ):
            return None

        except KeyboardInterrupt:
            return None


def get_sleep_data():
    api = init_api()

    if not api:
        return

    sleep_date = date.today().isoformat()
    return api.get_sleep_data(sleep_date)