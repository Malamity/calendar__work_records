import main as m
import os.path
import holidays
import base64
import smtplib
import ssl
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
USERNAME = 'misiu8221@gmail.com'
APP_PASSWORD = 'jpbkkybewlsuazjk'
FROM_EMAIL = 'misiu8221@gmail.com'


def get_workholidays(events) -> list[str]:
    workholidays = []
    for event in events:
        if event['summary'] == 'Urlop':
            end_date = datetime.datetime.strptime(event['end']['date'], '%Y-%m-%d').date()
            end_date = end_date - datetime.timedelta(days=1)
            workholidays.append(str(end_date))

    return workholidays


def get_work_days(events) -> list[str]:
    work_days = []
    for event in events:
        if event['summary'] == 'Praca':
            # end_date = datetime.datetime.strptime(event['end']['dateTime'], '%Y-%m-%d').date()
            work_days.append(str(event['end']['dateTime'])[:10])

    return work_days


def send_email_smtp(
    smtp_host: str, smtp_port: int, username: str, app_password: str, from_email: str, to_emails: list[str], subject: str, body_text: str
) -> None:
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(to_emails)
    msg['Subject'] = subject

    msg.attach(MIMEText(body_text, 'plain', _charset='utf-8'))

    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(username, app_password)
        server.sendmail(from_email, to_emails, msg.as_string())
        print('Email sent successfully via SMTP!')


def main():
    creds = m.auth_google_calendar(m.SCOPES)
    service = build('calendar', 'V3', credentials=creds)
    events = m.check_event(service, max_results=15)
    work_holidays = get_workholidays(events)
    print(f'W_H: {work_holidays}')
    work_days = get_work_days(events)
    print(f'W_D: {work_days}')
    TO_LIST = [
        'michal.szura8221@gmail.com',
    ]
    SUBJECT = 'Obecność'
    hour = datetime.datetime.now().hour
    day = str(datetime.datetime.now().date())
    # if day in work_days:
    print(f'{day}')
    if hour == 8:
        BODY = 'Rozpoczęcie pracy 8:00'
    elif hour == 15:
        BODY = 'Koniec pracy 15:00'
    else:
        BODY = 'TEST'

    # send_email_smtp(
    #     smtp_host=SMTP_HOST,
    #     smtp_port=SMTP_PORT,
    #     username=USERNAME,
    #     app_password=APP_PASSWORD,
    #     from_email=FROM_EMAIL,
    #     to_emails=TO_LIST,
    #     subject=SUBJECT,
    #     body_text=BODY,
    # )


if __name__ == '__main__':
    main()
