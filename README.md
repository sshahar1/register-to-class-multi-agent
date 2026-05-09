# register-to-class-multi-agent
Decide whether to enroll to class based on wake up time and number of meetings during the day

## Setup

Create a `.env` file with the API keys and Garmin credentials used by the agents:

```env
OPENAI_API_KEY=...
EMAIL=...
PASSWORD=...
```

To let the app check Google Calendar, download an OAuth desktop client JSON file
from Google Cloud and save it as `credentials.json` in the repo root. On the
first run, the app opens the Google OAuth flow and stores the resulting
`token.json` locally for future Calendar reads.

Optional overrides:

```env
CALENDAR_TIMEZONE=Asia/Jerusalem
GOOGLE_CALENDAR_CREDENTIALS_FILE=/path/to/credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=/path/to/token.json
```
