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


def check_event(service, max_results=10, start_date='now', last_week: bool = True, days: int = 0):
    events = []
    if days != 0:
        last_week = False

    if start_date == 'now':
        # now = datetime.datetime.now(datetime.timezone.utc)
        now = datetime.datetime(2025, 5, 5, 0, 0, 0, 0, tzinfo=datetime.UTC)  # TEST ONLY

    else:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        now = datetime.datetime.combine(start_date, datetime.time(8, 0, 0, tzinfo=datetime.UTC))

    if last_week and days == 0:
        time_min = (now - datetime.timedelta(days=(now.isoweekday() - 1))).isoformat()
        time_max = (now + datetime.timedelta(days=7)).isoformat()
    elif not last_week and days != 0:
        print(f'Days: {days}')
        time_min = (now - datetime.timedelta(days=(now.isoweekday() - 1))).isoformat()
        time_max = (now + datetime.timedelta(days=days - 1)).isoformat()

    print(f'\nCheck event time_min: {str(time_min)[:10]}')
    print(f'Check event time_max: {str(time_max)[:10]}\n')

    print(f"Getting upcoming {max_results} events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    event_list = events_result.get("items", [])

    for event in event_list:
        event_type = event.get('eventType', '').lower()
        if event_type != 'birthday':
            events.append(event)

    print(f'Event count: {len(events)}')
    return events


def last_work_day(events: list[dict]):
    last_day = ''

    event = events[len(events) - 1]
    if event['summary'] == 'Urlop':
        last_day = datetime.datetime.strptime(event['end']['date'], '%Y-%m-%d').date()
        last_day = last_day - datetime.timedelta(days=1)
        last_day = str(last_day)[:10]
    elif event['summary'] == 'Praca':
        last_day = str(event['end']['dateTime'])[:10]

    last_day = datetime.datetime.strptime(last_day, '%Y-%m-%d').date()
    return last_day


def get_work_holidays(events: list[dict]):
    work_holidays = []
    holidays_first_day = ''
    holidays_last_day = ''
    for event in events:
        if event['summary'] == 'Urlop':
            holidays_first_day = event['start']['date']
            holidays_last_day = event['end']['date']

    # print(f'First_day holidays: {holidays_first_day}')
    # print(f'Last_day holidays: {holidays_last_day}')

    if holidays_first_day != '' or holidays_last_day != '':
        holidays_first_day = datetime.datetime.strptime(holidays_first_day, '%Y-%m-%d').date()
        holidays_last_day = datetime.datetime.strptime(holidays_last_day, '%Y-%m-%d').date()
        holidays_last_day = holidays_last_day - datetime.timedelta(days=1)
        print(f'First_day holidays: {holidays_first_day}')
        print(f'Last_day holidays: {holidays_last_day}')
        holidays_delta = (holidays_last_day - holidays_first_day).days
        # print(f'Holidays_delta: {holidays_delta}')
        for i in range(holidays_delta + 1):
            day = holidays_first_day + datetime.timedelta(days=i)
            work_holidays.append(day)
    else:
        work_holidays = []
    return work_holidays


def main():
    # now_date = datetime.datetime.now().date()
    creds = auth_google_calendar(SCOPES)
    service = build("calendar", "V3", credentials=creds)

    event_check = check_event(service, max_results=50, last_week=False, days=7)

    last_day = last_work_day(event_check)
    print(f'Last day: {last_day}\n')

    next_week_firstday = ''
    next_week_lastday = ''
    # print(f'last_day.isoweekday(): {last_day} {last_day.isoweekday()}')
    if last_day.isoweekday() >= 5:
        next_week_firstday = last_day + datetime.timedelta(days=(8 - last_day.isoweekday()))
        next_week_lastday = next_week_firstday + datetime.timedelta(days=5)
    else:
        next_week_firstday = last_day + datetime.timedelta(days=1)
        next_week_lastday = next_week_firstday + datetime.timedelta(days=(5 - next_week_firstday.isoweekday()))

    print(f'next_week_first_day: {next_week_firstday}')
    print(f'next_week_last_day: {next_week_lastday}\n')
    next_week_delta = (next_week_lastday - next_week_firstday).days

    print(f'\n\n\n')
    print(f'Work Holidays')
    work_holidays = get_work_holidays(check_event(service, start_date=str(next_week_firstday)))
    work_holidays_str = ', '.join(str(day) for day in work_holidays)
    for day in work_holidays:
        print(f'day type: {type(day)}')
    print(f'Work holidays: {work_holidays_str}\n')

    for i in range(next_week_delta + 1):
        day = next_week_firstday + datetime.timedelta(days=i)
        print(f'Type day: {type(day)}')
        # print(f'day: {day}')
        # print(day not in work_holidays)

        if (day not in PL_Holidays) or (day not in work_holidays):
            if day.isoweekday() <= 5:
                print(f'day: {day}')
                day = str(day) + 'T08:00:00.000000'
                day = datetime.datetime.strptime(day, '%Y-%m-%dT%H:%M:%S.%f')
        #       add_work_event(service, day)


if __name__ == "__main__":
    main()
