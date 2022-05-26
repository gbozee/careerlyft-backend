from __future__ import print_function
import io
import os
import pathlib
import threading
from queue import Queue

import httplib2
from apiclient import discovery, errors
from googleapiclient.http import MediaIoBaseDownload
from oauth2client import client, tools
from oauth2client.file import Storage
from .constants import BASE_DIR
import time


def timeme(method):
    def wrapper(*args, **kw):
        startTime = int(round(time.time() * 1000))
        result = method(*args, **kw)
        endTime = int(round(time.time() * 1000))

        print(endTime - startTime, "ms")
        return result

    return wrapper

# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
#     flags = None

# BASE_DIR = os.path.dirname(os.path.abspath(__name__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, '..', 'client_secret.json')
APPLICATION_NAME = 'Drive API Python Quickstart'
SCOPES = ('https://www.googleapis.com/auth/drive.metadata.readonly '
          'https://www.googleapis.com/auth/drive '
          'https://www.googleapis.com/auth/drive.appdata '
          'https://www.googleapis.com/auth/drive.apps.readonly '
          'https://www.googleapis.com/auth/drive.file '
          'https://www.googleapis.com/auth/drive.metadata')


def get_credentials(flags):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

@timeme
def main(flags):
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = get_credentials(flags)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    items = fetch_all_files(service)
    # results = service.files().list(
    #     pageSize=10,fields="nextPageToken, files(id, name)").execute()
    # items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            # print(item)
            print('{0} ({1})'.format(item['name'], item['id']))
        download(service, items)


def fetch_all_files(service):
    result = []
    page_token = None
    while True:
        try:
            param = {
                'q': "'1tzXXT9Mo54O4yrc0y4V1DR41I0J0Acgp' in parents"
            }
            files = service.files().list(**param).execute()
            result.extend([dict(id=x['id'], name=x['name'])
                           for x in files['files']])
            page_token = files.get('nextPageToken')
            if not page_token:
                break
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            break
    return result


def download(service, files, numthreads=4, directory="cv_files"):
    new_dir = os.path.join(BASE_DIR, directory)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    for url in files:
        download_file(service, url, new_dir)


def download_file(service, ff, directory):
    request = service.files().export_media(fileId=ff['id'],
                                           mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    with open(os.path.join(directory, f"{ff['name']}.xlsx"), "wb") as oo:
        oo.write(request.execute())


# def sync_get_transfers_with_filters(self, **kwargs):
#     loop = asyncio.get_event_loop()
#     future = asyncio.ensure_future(self.get_transfers_with_filters(**kwargs))
#     result = loop.run_until_complete(future)
#     empty_list = [x for x in result if len(x) > 0]
#     return [a for b in empty_list for a in b]