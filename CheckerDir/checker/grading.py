import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from argparse import Namespace
from time import localtime, strftime
import importlib
import  googleapiclient
import  apiclient

sys.path.insert(0, '../')
configuration = importlib.import_module('config')
error = importlib.import_module('errors')
status = importlib.import_module('status')



def update_grade(name, surname, new_grade):
    _result = service.spreadsheets().values().get(spreadsheetId=configuration.SheetsId, range='A2:D', key=configuration.SheetsKey).execute()
    _values = _result.get('values', [])
    for row in _values:
        if row[0] == name and row[1] == surname:
            row[3] = new_grade
            break
    _body = {
        'values': _values,
        'majorDimension': 'ROWS'
    }
    _result = service.spreadsheets().values().update(spreadsheetId=configuration.SheetsId, range='A2:D', valueInputOption="RAW",
                                                     body=_body).execute()


def student_has_grade(name, surname):
    _result = service.spreadsheets().values().get(spreadsheetId=configuration.SheetsId, range='A2:D', key=configuration.SheetsKey).execute()
    _values = _result.get('values', [])
    for row in _values:
        if row[0] == name and row[1] == surname:
            return True
    return False


def add_student_grade(name, surname, new_grade):
    _append_values = [
        [
            name, surname, "", new_grade
        ]
    ]
    _body = {
        'values': _append_values,
        'majorDimension': 'ROWS'
    }
    result = service.spreadsheets().values().append(spreadsheetId=configuration.SheetsId, range='Foaie1', key=configuration.SheetsKey,
                                                    body=_body, valueInputOption="RAW").execute()


def handle_student(name, surname, new_grade):
    if student_has_grade(name, surname):
        update_grade(name, surname, new_grade)
    else:
        add_student_grade(name, surname, new_grade)


def fast_handle_student(name, surname, new_grade, group):
    student_exists = False
    _result = service.spreadsheets().values().get(spreadsheetId=configuration.SheetsId, range='A2:E', key=configuration.SheetsKey).execute()
    _values = _result.get('values', [])
    for row in _values:
        if row[0] == name and row[1] == surname and row[2] == group:
            row[3] = new_grade
            row[4] = strftime("%d/%m/%Y %H:%M:%S", localtime())
            student_exists = True
            break
    if student_exists:
        _body = {
            'values': _values,
            'majorDimension': 'ROWS'
        }
        _result = service.spreadsheets().values().update(spreadsheetId=configuration.SheetsId, range='A2:F', valueInputOption="RAW",
                                                         body=_body).execute()
    else:
        _append_values = [
            [
                name, surname, group, new_grade, strftime("%d/%m/%Y %H:%M:%S", localtime())
            ]
        ]
        _body = {
            'values': _append_values,
            'majorDimension': 'ROWS'
        }
        result = service.spreadsheets().values().append(spreadsheetId=configuration.SheetsId, range='Foaie1', key=configuration.SheetsKey,
                                                        body=_body, valueInputOption="RAW").execute()


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    file_name = configuration.SheetsApplicationName + '.json'
    credential_path = os.path.join(credential_dir, file_name)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(configuration.SheetsSecretFile, configuration.SheetsScopes)
        flow.user_agent = configuration.SheetsApplicationName
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials


if __name__ == '__main__':
    flags = Namespace(auth_host_name='localhost',
                      auth_host_port=[8080, 8090],
                      logging_level='ERROR',
                      noauth_local_webserver=False)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    name = sys.argv[1]
    surname = sys.argv[2]
    grade = sys.argv[3]
    group = sys.argv[4]
    fast_handle_student(name, surname, grade, group)
    print(status.GradeSubmitSuccess)
