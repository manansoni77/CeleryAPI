import httplib2
import base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
from worker import worker
from email_cred import get_credentials

@worker.task(name='sendGmail')
def SendGmail(sender, to, subject, message, attachments):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message1 = CreateGmail(sender, to, subject, message, attachments)
    SendGmailInternal(service, "me", message1)

def SendGmailInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def CreateGmail(sender, to, subject, message, attachments):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
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