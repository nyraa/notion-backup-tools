#!/usr/bin/env python

import os
import time
import zipfile

TZ = os.getenv("TZ", "Asia/Taipei")
NOTION_API = os.getenv('NOTION_API', 'https://www.notion.so/api/v3')
EXPORT_FILENAME = os.getenv('EXPORT_FILENAME', 'export.zip')
NOTION_TOKEN_V2 = os.getenv('token_v2')
NOTION_FILE_TOKEN = os.getenv('file_token')
NOTION_SPACE_ID = os.getenv('space_id')

ENQUEUE_TASK_PARAM = {
    "task": {
        "eventName": "exportSpace",
        "request": {
            "spaceId": NOTION_SPACE_ID,
            "exportOptions": {
                'collectionViewExportType': 'all',
                "exportType": "markdown",
                "timeZone": TZ,
                "locale": "en"
            },
            'shouldExportComments': False,
        }
    }
}


import requests

def request(endpoint: str, params: object):
    response = requests.post(
        f'{NOTION_API}/{endpoint}',
        json=params,
        headers={
            'content-type': 'application/json',
        },
        cookies={
            'token_v2': NOTION_TOKEN_V2
        }
    )
    return response.json()

def unzip(source_filename, dest_dir):
    with zipfile.ZipFile(source_filename) as zf:
        zf.extractall(dest_dir)

def unzip_nested(source_filename, dest_dir):
    with zipfile.ZipFile(source_filename) as zf:
        zf.extractall(dest_dir)
    
    for filename in os.listdir(dest_dir):
        if filename.endswith('.zip'):
            unzip(os.path.join(dest_dir, filename), dest_dir)
        os.remove(os.path.join(dest_dir, filename))

def export():
    task_id = request('enqueueTask', ENQUEUE_TASK_PARAM).get('taskId')
    print(f'Enqueued task {task_id}')

    while True:
        time.sleep(2)
        tasks = request("getTasks", {"taskIds": [task_id]}).get('results')
        task = next(t for t in tasks if t.get('id') == task_id)
        if task.get('state') == 'retryable_failure':
            print('Pending...')
            continue
        print(f'\rPages exported: {task.get("status").get("pagesExported")}', end="")

        if task.get('state') == 'success':
            break

    export_url = task.get('status').get('exportURL')
    print(f'\nExport created, downloading: {export_url}')

    res = requests.get(
        export_url,
        cookies={
            'file_token': NOTION_FILE_TOKEN,
        }
    )
    res.raise_for_status()
    with open(EXPORT_FILENAME, 'wb') as f:
        f.write(res.content)
    print(f'\nDownload complete: {EXPORT_FILENAME}')

    print(f'Unzipping {EXPORT_FILENAME}')
    unzip_nested(EXPORT_FILENAME, 'export')
    os.remove(EXPORT_FILENAME)


if __name__ == "__main__":
    export()