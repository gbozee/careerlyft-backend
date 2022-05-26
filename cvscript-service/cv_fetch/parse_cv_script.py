from __future__ import print_function
import httplib2
import os
import io
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors
from googleapiclient.http import MediaIoBaseDownload
import threading
from queue import Queue
import pathlib


class DownloadThread(threading.Thread):
    def __init__(self, queue, service):
        super(DownloadThread, self).__init__()
        self.queue = queue
        self.service = service
        self.daemon = True

    def run(self):
        while True:
            url = self.queue.get()
            try:
                self.download_file(url)
            except errors.HttpError as e:
                print("   Error: %s" % e)
            self.queue.task_done()

    def download_file(self, ff):
        request = self.service.files().export_media(fileId=ff['id'],
                                                    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        with open(f"{ff['name']}.xlsx", "wb") as oo:
            oo.write(request.execute())


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = ('https://www.googleapis.com/auth/drive.metadata.readonly '
          'https://www.googleapis.com/auth/drive '
          'https://www.googleapis.com/auth/drive.appdata '
          'https://www.googleapis.com/auth/drive.apps.readonly '
          'https://www.googleapis.com/auth/drive.file '
          'https://www.googleapis.com/auth/drive.metadata')
CLIENT_SECRET_FILE = os.path.join('..', 'client_secret.json')
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_credentials():
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


def main():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = get_credentials()
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
        # download_file(service, items[0]['id'])
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
            # import pdb; pdb.set_trace()
            result.extend([dict(id=x['id'], name=x['name'])
                           for x in files['files']])
            page_token = files.get('nextPageToken')
            if not page_token:
                break
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            break
    return result


def download_file(drive_service, ff):
    request = drive_service.files().export_media(fileId=ff['id'],
                                                 mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # fh = io.BytesIO()
    # downloader = MediaIoBaseDownload(fh, request)
    # done = False
    # while done is False:
    #     status, done = downloader.next_chunk()
    #     print("Download %d%%." % int(status.progress() * 100))
    with open(f"{ff['name']}.xlsx", "wb") as oo:
        oo.write(request.execute())


def download(service, files, numthreads=4, directory="cv_files"):

    # pathlib.Path('/my/directory').mkdir(parents=True, exist_ok=True)
    if not os.path.exists(directory):
        os.makedirs(directory)
    for url in files:
        download_file(service, url, directory)
    # queue = Queue()
    # for url in files:
    #     queue.put(url)

    # for i in range(numthreads):
    #     t = DownloadThread(queue, service)
    #     t.start()

    # queue.join()


def download_file(service, ff, directory):
    request = service.files().export_media(fileId=ff['id'],
                                           mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    with open(f"{directory}/{ff['name']}.xlsx", "wb") as oo:
        oo.write(request.execute())


if __name__ == '__main__':
    main()
