from pydantic_ai import Agent, RunContext

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

@train_agent.tool
def sleep_well(ctx: RunContext[None]) -> bool:
    return True # todo get from Garmin

@train_agent.tool
def busy_day(ctx: RunContext[None]) -> bool:
    return False # todo get from Google Calendar

@train_agent.tool
def register(ctx: RunContext[None]) -> str:
    # todo call Ivonne's class registration API'
    return "You have registered for Ivonne's class."

if __name__ == "__main__":
    query = "Did you register for Ivonne's class on Wednesday?"
    print(f"User: {query}\n")

    # This single line replaces the entire while loop!
    result = train_agent.run_sync(query)

    print(f"Agent: {result.output}")