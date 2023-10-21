import io
import os
import base64
import httplib2
from datetime import datetime
from flask_restful import marshal
from jinja2 import Environment, FileSystemLoader
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import pandas
from activity_tracker_v2.model import Credentials, Logs, Trackers, User, log_resource_fields, tracker_resource_fields
from activity_tracker_v2.plot import save_plot
from email_cred import get_credentials
from worker import worker

templateLoader = FileSystemLoader(searchpath="./activity_tracker_v2/templates")
templateEnv = Environment(loader=templateLoader)
SENDER = os.environ.get('EMAIL_SENDER')

@worker.task(name='sendGmail')
def send_gmail(to, subject, message, attachments = []):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message1 = create_gmail(to, subject, message, attachments)
    send_gmail_interval(service, "me", message1)

def send_gmail_interval(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def create_gmail(to, subject, message, attachments):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = to
    msg.attach(MIMEText(message, 'html'))

    for (file, name) in attachments:
        file.seek(0)
        part = MIMEApplication(file.read(), name=name)
        part['Content-Disposition'] = f'attachment; filename="{name}"'
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}
    return body

@worker.task(name='sendWelcomeMail')
def send_welcome_email(username, email_id):
    template = templateEnv.get_template('welcome.html')
    message = template.render(username=username)
    send_gmail(email_id, 'Welcome to Todo App!', message)

@worker.task(name='sendDailyReminder')
def send_daily_reminder():
    creds = Credentials.query.all()
    today = datetime.utcnow().date()
    for cred in creds:
        if cred.last_login.date() == today:
            pass
        user = User.query.filter_by(user_id = cred.user_id).first()
        username = f'{user.first_name} {user.last_name}'
        template = templateEnv.get_template('daily_reminder.html')
        message = template.render(username=username)
        send_gmail(cred.email_id, 'Daily Reminder!', message)

@worker.task(name='sendMonthlyReport')
def send_monthly_report():
    creds = Credentials.query.all()
    for cred in creds:
        user = User.query.filter_by(user_id=cred.user_id).first()
        username = f'{user.first_name} {user.last_name}'
        trackers = Trackers.query.filter_by(user_id=user.user_id).all()
        tracker_data = [marshal(x, tracker_resource_fields) for x in trackers]
        for i, tracker in enumerate(trackers):
            logs = Logs.query.filter_by(track_id=tracker.track_id).all()
            tracker_data[i]['logs'] = [marshal(x, log_resource_fields) for x in logs]
            tracker_data[i]['plot'] = save_plot(tracker, logs)
        template = templateEnv.get_template('monthly_report_message.html')
        message = template.render(username=username)
        template = templateEnv.get_template('monthly_report.html')
        report = template.render(username = username, tracker_data = tracker_data)
        report_name = f'{user.first_name}_{user.last_name}-monthly_report.html'
        report = io.BytesIO(bytes(report, 'utf-8'))
        send_gmail(cred.email_id, 'Monthly Report', message, [(report, report_name)])

@worker.task(name='sendTrackerReport')
def send_tracker_report(user_id, track_id):
    cred = Credentials.query.filter_by(user_id=user_id).first()
    user = User.query.filter_by(user_id=user_id).first()
    track = Trackers.query.filter_by(track_id=track_id).first()
    tracker_logs = Logs.query.filter_by(track_id=track_id).all()
    val = []
    time = []
    for log in tracker_logs:
        val.append(log.info)
        time.append(log.time)
    df = pandas.DataFrame({'time':time,'val':val})
    csvfile = io.BytesIO()
    df.to_csv(csvfile)
    csvfile_name = f'{user.first_name}_{user.last_name}-{track.track_name}.csv'
    username = f'{user.first_name} {user.last_name}'
    template = templateEnv.get_template('monthly_report_message.html')
    message = template.render(username=username, trackername=track.track_name)
    send_gmail(cred.email_id,f'{track.track_name} Logs Summary', message, [(csvfile, csvfile_name)])