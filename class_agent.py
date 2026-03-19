from pydantic_ai import Agent, RunContext
from garmin import init_api
import datetime
import os

OPENAI_MODEL = "gpt-4o-mini"


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
    system_prompt="""You are a sleep analysis agent. Your goal is to analyze the user's sleep data and provide a binary result of true or false.'"""
    )


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_calendar_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
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

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

@train_agent.tool
async def sleep_well(ctx: RunContext[None]) -> bool:
    api = init_api()
    today = datetime.date.today().isoformat()

    sleep_data = api.get_sleep_data(today)
    if sleep_data is None:
        return True
    result = await sleep_analysis_agent.run(f"Was my sleep good? {sleep_data}")
    return result.data

@train_agent.tool
def busy_day(ctx: RunContext[None]) -> bool:
    service = get_calendar_service()
    if not service:
        return False

    today = datetime.date.today()
    start_of_day = datetime.datetime.combine(today, datetime.time.min).isoformat() + 'Z'
    end_of_day = datetime.datetime.combine(today, datetime.time.max).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    total_duration_seconds = 0
    for event in events:
        start_str = event['start'].get('dateTime', event['start'].get('date'))
        end_str = event['end'].get('dateTime', event['end'].get('date'))

        # Handle all-day events by skipping them
        if 'T' not in start_str or 'T' not in end_str:
            continue

        start = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        duration = end - start
        total_duration_seconds += duration.total_seconds()

    total_hours = total_duration_seconds / 3600
    return total_hours > 4

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