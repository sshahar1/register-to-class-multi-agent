import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from garmin import init_api
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic_ai import Agent, RunContext

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

OPENAI_MODEL = "gpt-4o-mini"
LOCAL_TIMEZONE = ZoneInfo(os.getenv("CALENDAR_TIMEZONE", "Asia/Jerusalem"))


sleep_agent = Agent(
    f"openai:{OPENAI_MODEL}",
    system_prompt="""You are a sleep agent. Your goal is to determine if the user had a good sleep.
    A good sleep is defined as 7 or more hours of sleep.
    Respond with 'True' if it was a good sleep and 'False' otherwise.
    """,
)

busyness_agent = Agent(
    f"openai:{OPENAI_MODEL}",
    system_prompt="""You are a busyness agent. Your goal is to determine if the user's day was busy.
    A busy day is defined as having more than 5 meetings.
    Respond with 'True' if the day was busy and 'False' otherwise.
    """,
)

train_agent = Agent(
    f"openai:{OPENAI_MODEL}",
    system_prompt="""You are my wellness keeper.
    I need to train regular and go to Ivonne's class every Wednesday at 8 PM, however, before registering
    I was you to check 'sleep_well' and 'busy_day'. 
    If they are anything but (False, True) respectively use 'register' to register.
    """,
)

sleep_analysis_agent = Agent(
    f"openai:{OPENAI_MODEL}",
    system_prompt="""You are a sleep analysis agent. Your goal is to analyze the user's sleep data and provide a binary result of true or false."""
    )


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_FILE = Path(os.getenv("GOOGLE_CALENDAR_TOKEN_FILE", PROJECT_DIR / "token.json"))
CREDENTIALS_FILE = Path(
    os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE", PROJECT_DIR / "credentials.json")
)


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() == "true"


def get_calendar_service():
    """Authenticate with Google Calendar and return a Calendar API service."""
    creds = None
    # The token file stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"Missing Google Calendar credentials file: {CREDENTIALS_FILE}")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with TOKEN_FILE.open("w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

@train_agent.tool
async def sleep_well(ctx: RunContext[None]) -> bool:
    api = init_api()
    if not api:
        return True

    today = datetime.date.today().isoformat()

    sleep_data = api.get_sleep_data(today)
    if sleep_data is None:
        return True
    result = await sleep_analysis_agent.run(f"Was my sleep good? {sleep_data}")
    return parse_bool(result.data)

@train_agent.tool
def busy_day(ctx: RunContext[None]) -> bool:
    service = get_calendar_service()
    if not service:
        return False

    today = datetime.datetime.now(LOCAL_TIMEZONE).date()
    start_of_day = datetime.datetime.combine(
        today, datetime.time.min, tzinfo=LOCAL_TIMEZONE
    )
    end_of_day = datetime.datetime.combine(
        today, datetime.time.max, tzinfo=LOCAL_TIMEZONE
    )

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    except HttpError as error:
        print(f"Could not read Google Calendar events: {error}")
        return False

    events = events_result.get("items", [])
    meeting_count = sum(1 for event in events if "dateTime" in event.get("start", {}))
    return meeting_count > 5

@train_agent.tool
def register(ctx: RunContext[None]) -> str:
    # todo call Ivonne's class registration API'
    return "You have registered for Ivonne's class."

if __name__ == "__main__":
    query = "Did you register for Ivonne's class on Wednesday?"
    print(f"User: {query}\n")

    # This single line replaces the entire while loop!
    result = train_agent.run_sync(query)

    print(f"Agent: {result.data}")
