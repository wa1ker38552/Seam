import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import json

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me").execute()
    messages = results.get("messages", [])

    links = []
    for i, message in enumerate(messages):
        msg = service.users().messages().get(userId="me", id=message['id']).execute()
        headers = msg['payload']['headers']
        
        sender = next(header['value'] for header in headers if header['name'] == 'From')
        receiver = next(header['value'] for header in headers if header['name'] == 'To')
        
        if sender == 'Coresignal <noreply@coresignal.com>':
            print(f'{i+1}/{len(messages)}')
            if receiver.startswith('coresignal'):
                route = int(receiver.split('@')[1].split('.')[0].replace('mailroute', ''))
                if route >= 17: # 17 is the start of the automated ones
                    # target.append(msg)
                    part = msg['payload'].get('parts', [])[0]
                    if part['mimeType'] == 'text/plain':
                        body = part['body']['data']
                        content = base64.urlsafe_b64decode(body).decode('utf-8')
                        link = content.split('( ')[1].split(' )')[0]
                        links.append(link)

    with open('coresignal_verification_links.json', 'w') as file:
       file.write(json.dumps(links, indent=2))

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()