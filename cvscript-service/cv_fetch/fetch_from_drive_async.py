from __future__ import print_function
import io
import os
import pathlib
import threading
from queue import Queue
import asyncio
import httplib2
from apiclient import discovery, errors
from googleapiclient.http import MediaIoBaseDownload
from oauth2client import client, tools
from oauth2client.file import Storage
from .constants import BASE_DIR
from asgiref.sync import sync_to_async
import aiofiles

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
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "..", "client_secret.json")
APPLICATION_NAME = "Drive API Python Quickstart"
SCOPES = (
    "https://www.googleapis.com/auth/drive.metadata.readonly "
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/drive.appdata "
    "https://www.googleapis.com/auth/drive.apps.readonly "
    "https://www.googleapis.com/auth/drive.file "
    "https://www.googleapis.com/auth/drive.metadata"
)


@sync_to_async
def get_credentials(flags):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser("~")
    credential_dir = os.path.join(home_dir, ".credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, "drive-python-quickstart.json")

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print("Storing credentials to " + credential_path)
    return credentials


def build_service(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v3", http=http)
    return service


async def main2(flags):
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = await get_credentials(flags)
    items = await fetch_all_files(credentials)
    # results = service.files().list(
    #     pageSize=10,fields="nextPageToken, files(id, name)").execute()
    # items = results.get('files', [])
    if not items:
        print("No files found.")
    else:
        print("Files:")
        for item in items:
            # print(item)
            print("{0} ({1})".format(item["name"], item["id"]))
        await download(credentials, items)

@timeme
def main(flags):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main2(flags))
    result = loop.run_until_complete(future)


@sync_to_async
def fetch_all_files(credentials):
    service = build_service(credentials)
    result = []
    page_token = None
    while True:
        try:
            param = {"q": "'1tzXXT9Mo54O4yrc0y4V1DR41I0J0Acgp' in parents"}
            files = service.files().list(**param).execute()
            result.extend([dict(id=x["id"], name=x["name"]) for x in files["files"]])
            page_token = files.get("nextPageToken")
            if not page_token:
                break
        except errors.HttpError as error:
            print("An error occurred: %s" % error)
            break
    return result


async def download(credentials, files, numthreads=4, directory="cv_files"):
    tasks = []
    new_dir = os.path.join(BASE_DIR, directory)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    for url in files:
        task = asyncio.ensure_future(download_file(credentials, url, new_dir))
        tasks.append(task)
    result = await asyncio.gather(*tasks)
    new_tasks = []
    for t in result:
        request, ff, directory = t
        task = asyncio.ensure_future(await_download_file(request, ff, directory))
        new_tasks.append(task)
        # print(ff["name"])
        # await await_download_file(request, ff, directory)
    result = await asyncio.gather(*new_tasks)
    # return result


async def await_download_file(request, ff, directory):
    # await asyncio.sleep(1)
    print(ff["name"])
    async with aiofiles.open(os.path.join(directory, f"{ff['name']}.xlsx"), "wb") as oo:
        await oo.write(request.execute())
    return "Done"


@sync_to_async
def download_file(credentials, ff, directory):
    service = build_service(credentials)
    request = service.files().export_media(
        fileId=ff["id"],
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return request, ff, directory


# def sync_get_transfers_with_filters(self, **kwargs):
#     loop = asyncio.get_event_loop()
#     future = asyncio.ensure_future(self.get_transfers_with_filters(**kwargs))
#     result = loop.run_until_complete(future)
#     empty_list = [x for x in result if len(x) > 0]
#     return [a for b in empty_list for a in b]
