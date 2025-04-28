import os.path
import holidays

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import datetime  # import datetime, timedelta, UTC


SCOPES = ["https://www.googleapis.com/auth/calendar"]

PL_Holidays = holidays.CountryHoliday('PL', years=datetime.datetime.now().year)


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
    start_time,
    end_time,
    timezone="Europe/Warsaw",
):
    event = {
        "summary": summary,
        "start": {"dateTime": start_time.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end_time.isoformat(), "timeZone": timezone},
    }
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"Event created: {created_event.get('htmlLink')}")


def add_work_event(service, start_time):
    end_time = start_time + datetime.timedelta(hours=7)
    add_event(service, 'Praca', start_time, end_time)


def check_event(service, max_results=10):
    now = datetime.datetime.now(datetime.timezone.utc)
    time_min = (now - datetime.timedelta(days=7)).isoformat()
    time_max = now.isoformat()

    # print(f'Time: {now}')
    # print(f'Time: {time_min}')
    # print(f'Time: {time_max}')

    print(f"Getting upcoming {max_results} events")
    events_result = (
        service.events()
        .list(
            q='Praca',
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    print(f'Event count: {len(events)}')
    return events


def last_work_day(events: list[dict]):
    last_day = ''
    event = events[len(events) - 1]

    for key, value in event.items():
        if key == 'end':
            last_day = str(value['dateTime'])[:10]

    last_day = datetime.datetime.strptime(last_day, '%Y-%m-%d').date()
    return last_day


def main():
    now_date = datetime.datetime.now().date()
    creds = auth_google_calendar(SCOPES)
    service = build("calendar", "V3", credentials=creds)
    events = check_event(service, max_results=15)

    last_day = last_work_day(events)
    # print(f'Last day: {last_day}')

    next_week_firstday = ''
    next_week_lastday = ''

    if last_day <= now_date:
        next_week_firstday = last_day + datetime.timedelta(days=(8 - last_day.isoweekday()))

    next_week_lastday = next_week_firstday + datetime.timedelta(days=4)
    next_week_delta = (next_week_lastday - next_week_firstday).days

    for i in range(next_week_delta + 1):
        day = next_week_firstday + datetime.timedelta(days=i)
        if day not in PL_Holidays:
            day = str(day) + 'T08:00:00.000000'
            day = datetime.datetime.strptime(day, '%Y-%m-%dT%H:%M:%S.%f')
            add_work_event(service, day)


if __name__ == "__main__":
    main()
