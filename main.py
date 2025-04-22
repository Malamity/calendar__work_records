import os.path
import holidays

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime, timedelta, UTC


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def auth_google_calendar(scopes, credentials_path="credentials.json", token_path="token.json"):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds


def add_event(
    service,
    summary,
    location,
    description,
    start_time,
    end_time,
    timezone="Europe/Warsaw",
    attendees_emails=None,
):
    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start_time.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end_time.isoformat(), "timeZone": timezone},
        "attendees": ([{"email": email} for email in attendees_emails] if attendees_emails else []),
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"Event created: {created_event.get('htmlLink')}")


def check_event(service, max_results=10):
    now = datetime.now(UTC).isoformat()
    print(f"Getting upcoming {max_results} events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found")
        return

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(f"{start} - {event.get('summary', 'No Title')}")


def main():
    creds = auth_google_calendar(SCOPES)
    service = build("calendar", "V3", credentials=creds)
    # summary = 'Test'
    # location = 'Somewhere'
    # description = 'TEST'
    # start_time = datetime(2025, 4, 22, 10, 0)
    # end_time = start_time + timedelta(hours=36)

    # add_event(service, summary, location, description, start_time, end_time)
    # check_event(service, max_results=15)


if __name__ == "__main__":
    main()
