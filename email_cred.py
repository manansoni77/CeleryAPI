import os
import oauth2client
from oauth2client import client, tools, file
import json

CLIENT_SECRET_FILE = 'secret.json'
CREDENTIAL_FILE = 'email_credential.json'
SCOPES = 'https://www.googleapis.com/auth/gmail.send'
APPLICATION_NAME = 'email_app_python'


with open(CREDENTIAL_FILE, 'w') as f:
    f.write(json.dumps(json.loads(os.environ.get('EMAIL_CREDENTIAL'))))

credential_dir = os.path.curdir
credential_path = os.path.join(credential_dir, CREDENTIAL_FILE)
store = oauth2client.file.Storage(credential_path)

def create_credentials():
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    flow.user_agent = APPLICATION_NAME
    tools.run_flow(flow, store)

def get_credentials():
    credentials = store.get()
    if not credentials or credentials.invalid:
        create_credentials()
        print('Updating credentials in ' + credential_path)
    return credentials

if __name__ == '__main__':
    with open(CLIENT_SECRET_FILE, 'w') as f:
        f.write(json.dumps(json.loads(os.environ.get('EMAIL_SECRET'))))
    create_credentials()
    print('Credentials stored at ' + credential_path)

