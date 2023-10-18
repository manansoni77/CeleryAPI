from jinja2 import Environment, FileSystemLoader
import httplib2
import base64
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
from worker import worker
from email_cred import get_credentials

templateLoader = FileSystemLoader(searchpath="./activity_tracker_v2/templates")
templateEnv = Environment(loader=templateLoader)
SENDER = os.environ.get('EMAIL_SENDER')

@worker.task(name='sendGmail')
def SendGmail(to, subject, message, attachments = []):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message1 = CreateGmail(to, subject, message, attachments)
    SendGmailInternal(service, "me", message1)

def SendGmailInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def CreateGmail(to, subject, message, attachments):
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

@worker.task(name='welcomeMail')
def send_welcome_email(username, email_id):
    template = templateEnv.get_template('welcome.html')
    message = template.render(username=username)
    worker.send_task('sendGmail', (email_id, 'Welcome to Todo App!', message))
