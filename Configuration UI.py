import re
import smtplib

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from argparse import Namespace

import os
import wx
import wx.lib.scrolledpanel as LibScrolledPanel


def list_to_string(list):
    result = ""
    for element in list:
        result = result + '\"' + element + '\"' + ", "
    result = result[:len(result) - 2]
    result = '[' + result + ']'
    result = result.replace('\\', "\\\\")
    return result


def InfoBox(parent, message, caption='Insert program title'):
    dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()


def WarnBox(parent, message, caption='Warning!'):
    dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_WARNING)
    dlg.ShowModal()
    dlg.Destroy()


class StaticConfiguration:
    def __init__(self):

        self.OpenedConfigPath = ""
        self.ConfigurationDictionary = dict()

    def UpdateConfiguration(self):
        for item in self.ConfigurationDictionary.keys():
            var_name = item
            var_name = var_name.replace(' ', '_')
            var_name = var_name.lower()
            var_name = 'self.text_' + var_name
            command = 'self.ConfigurationDictionary.update({\'' + item + '\':' + var_name + '.GetValue()})'
            exec(command)

    def WriteConfiguration(self, filename):
        try:
            with open(filename, 'w') as file:
                for item in self.ConfigurationDictionary.keys():
                    if item == "In Files" or item == "Out Files" or item == "Reference Files":
                        line = item.replace(' ', '') + ' = '
                        right = self.ConfigurationDictionary[item]
                        right = right.replace('[', '')
                        right = right.replace(']', '')
                        line = line + "[" + right + "]\n"
                    else:
                        line = item.replace(' ', '') + ' = ' + '\'' + self.ConfigurationDictionary[item] + '\'\n'
                    line = line.replace('\\', '\\\\')
                    file.write(line)
        except IOError:
            wx.LogError('Fak')
            print('Fakk')

    def LoadConfiguration(self):
        for item in self.ConfigurationDictionary.keys():
            var_name = item
            var_name = var_name.replace(' ', '_')
            var_name = var_name.lower()
            var_name = 'self.text_' + var_name
            itemvalue = self.ConfigurationDictionary[item]
            if itemvalue == " ":
                itemvalue = ""
            command = var_name + '.SetValue(\'' + itemvalue + '\')'
            exec(command)

    def ReadConfiguration(self, filename):
        try:
            with open(filename, 'r') as file:
                line = file.readline()
                while line:
                    if line != "":
                        left = line.split('=')[0]
                        right = line.split('=')[1]
                        left = left.strip()
                        right = right.strip()
                        if left == "InFiles" or left == "OutFiles" or left == "ReferenceFiles":
                            right = right
                        else:
                            right = right.replace('\'', "")
                        left = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", left)
                        self.ConfigurationDictionary.update({left: right})
                    line = file.readline()
        except IOError:
            wx.LogError('Fak')


class SheetsTest:
    def get_credentials(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        file_name = self.SheetsApplicationName + '.json'
        credential_path = os.path.join(credential_dir, file_name)

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.SheetsSecretFile, self.SheetsScopes)
            flow.user_agent = self.SheetsApplicationName
            if self.flags:
                credentials = tools.run_flow(flow, store, self.flags)
            print('Storing credentials to ' + credential_path)
        return credentials

    def __init__(self, Secret, Id, Scopes, Key, ApplicationName):
        self.flags = Namespace(auth_host_name='localhost',
                               auth_host_port=[8080, 8090],
                               logging_level='ERROR',
                               noauth_local_webserver=False)
        self.SheetsSecretFile = Secret
        self.SheetsScopes = Scopes
        self.SheetsKey = Key
        self.Id = Id
        self.SheetsApplicationName = ApplicationName
        self.credentials = self.get_credentials()
        http = self.credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.service = discovery.build('sheets', 'v4', http=http,
                                       discoveryServiceUrl=discoveryUrl)
        result = self.service.spreadsheets().values().get(spreadsheetId=self.Id, range='A1',
                                                          key=self.SheetsKey).execute()
        values = result.get('values', [])
        if len(values) == 0:
            self.exa1 = ""
        else:
            self.exa1 = values[0][0]
        testword = 'Works'
        append_values = [
            [
                testword
            ]
        ]
        body = {
            'values': append_values,
            'majorDimension': 'ROWS'
        }
        result = self.service.spreadsheets().values().update(spreadsheetId=self.Id, range='A1',
                                                             key=self.SheetsKey,
                                                             body=body, valueInputOption="RAW").execute()
        result = self.service.spreadsheets().values().get(spreadsheetId=self.Id, range='A1',
                                                          key=self.SheetsKey).execute()
        self.Success = False
        values = result.get('values', [])
        if values[0][0] == testword:
            self.Success = True

    def Restore(self):
        append_values = [
            [
                self.exa1
            ]
        ]
        body = {
            'values': append_values,
            'majorDimension': 'ROWS'
        }
        result = self.service.spreadsheets().values().update(spreadsheetId=self.Id, range='A1',
                                                             key=self.SheetsKey,
                                                             body=body, valueInputOption="RAW").execute()


class ConfigurationTab(wx.lib.scrolledpanel.ScrolledPanel):

    def list_to_string(self, list):
        result = ""
        for element in list:
            result = result + '\"' + element + '\"' + ", "
        result = result[:len(result) - 2]
        result = '[' + result + ']'
        result = result.replace('\\', "\\\\")
        return result

    def add_field_parent(self, name, parent):  # syntactic sugar here
        name_with_spaces = name
        name = name.strip()
        name = name.replace(' ', '_')
        setattr(self, 'label_' + name.lower(), wx.StaticText(self, label=name_with_spaces))
        setattr(self, 'text_' + name.lower(), wx.TextCtrl(self))
        cmd = parent + ".Add(self.label_" + name.lower() + ", pos=(" + \
              str(self.counter) + ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)"
        exec(cmd)
        cmd = parent + ".Add(self.text_" + name.lower() + ', pos=(' + str(
            self.counter) + ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)'
        exec(cmd)
        self.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def add_simple_field(self, name):  # syntactic sugar here
        name = name.replace(' ', '_')
        setattr(self, 'label_' + name.lower(), wx.StaticText(self, label=name.replace('_', ' ')))
        setattr(self, 'text_' + name.lower(), wx.TextCtrl(self))
        exec(
            "self.sizer.Add(self.label_" + name.lower() + ", pos=(" + str(self.counter) +
            ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)")
        exec(
            'self.sizer.Add(self.text_' + name.lower() + ', pos=(' + str(self.counter) +
            ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)')
        self.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def InitStarter(self):
        self.StarterOptionBox = wx.StaticBox(self, label="Starter Options")
        self.StarterOptionBoxSizer = wx.StaticBoxSizer(self.StarterOptionBox, wx.VERTICAL)
        self.StarterGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Timeout                              ', 'self.StarterGrid')

        self.StarterGrid.AddGrowableCol(1)
        self.StarterOptionBoxSizer.Add(self.StarterGrid, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM)
        self.sizer.Add(self.StarterOptionBoxSizer, pos=(0, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=5)

    def InitEmail(self):
        self.EmailOptionBox = wx.StaticBox(self, label="Email Options")
        self.EmailOptionBoxSizer = wx.StaticBoxSizer(self.EmailOptionBox, wx.VERTICAL)
        self.EmailGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Email Address', 'self.EmailGrid')

        self.label_password = wx.StaticText(self, label="Password")
        self.EmailGrid.Add(self.label_password, pos=(self.counter, 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM,
                           border=5)
        self.text_password = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.EmailGrid.Add(self.text_password, pos=(self.counter, 1), span=(1, 4),
                           flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP,
                           border=5)
        self.ConfigurationDictionary.update({'Password': ''})
        self.counter = self.counter + 1

        self.add_field_parent('Email Server Address', 'self.EmailGrid')
        self.add_field_parent('Email Server Port', 'self.EmailGrid')
        self.add_field_parent('Imap Server Address', 'self.EmailGrid')
        self.add_field_parent('Subject', 'self.EmailGrid')
        self.add_field_parent('Zip Format', 'self.EmailGrid')
        self.add_field_parent('Grade Email Subject', 'self.EmailGrid')
        self.add_field_parent('Grade Email Body              ', 'self.EmailGrid')

        self.EmailGrid.AddGrowableCol(1)
        self.EmailOptionBoxSizer.Add(self.EmailGrid, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM)
        self.sizer.Add(self.EmailOptionBoxSizer, pos=(1, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

    def InitSheets(self):
        self.SheetsOptionBox = wx.StaticBox(self, label="Sheets Options")
        self.SheetsOptionBoxSizer = wx.StaticBoxSizer(self.SheetsOptionBox, wx.VERTICAL)
        self.SheetsGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Sheets Secret File', 'self.SheetsGrid')
        self.button_secret_file = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnSecretFileBrowser, self.button_secret_file)
        self.SheetsGrid.Add(self.button_secret_file, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT,
                            border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Sheets Scopes', 'self.SheetsGrid')
        self.add_field_parent('Sheets Application Name ', 'self.SheetsGrid')
        self.add_field_parent('Sheets Key', 'self.SheetsGrid')
        self.add_field_parent('Sheets Id', 'self.SheetsGrid')

        self.SheetsGrid.AddGrowableCol(1)
        self.SheetsOptionBoxSizer.Add(self.SheetsGrid, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        self.sizer.Add(self.SheetsOptionBoxSizer, pos=(2, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

    def InitHomework(self):
        self.HomeworkOptionBox = wx.StaticBox(self, label="Homework Options")
        self.HomeworkOptionBoxSizer = wx.StaticBoxSizer(self.HomeworkOptionBox, wx.VERTICAL)
        self.HomeworkGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Build String', 'self.HomeworkGrid')
        self.add_field_parent('Exe Filename', 'self.HomeworkGrid')
        self.add_field_parent('Homework', 'self.HomeworkGrid')
        self.add_field_parent('Absolute Path', 'self.HomeworkGrid')

        self.button_checker_path = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnCheckerPathBrowse, self.button_checker_path)
        self.HomeworkGrid.Add(self.button_checker_path, pos=(self.counter, 4), span=(1, 1), flag=wx.RIGHT | wx.EXPAND,
                              border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Relative Download Path   ', 'self.HomeworkGrid')
        self.add_field_parent('Relative Checker Path', 'self.HomeworkGrid')

        self.HomeworkGrid.AddGrowableCol(1)
        self.HomeworkOptionBoxSizer.Add(self.HomeworkGrid, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        self.sizer.Add(self.HomeworkOptionBoxSizer, pos=(3, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

    def InitTest(self):
        self.TestOptionBox = wx.StaticBox(self, label="Tests Options")
        self.TestOptionBoxSizer = wx.StaticBoxSizer(self.TestOptionBox, wx.VERTICAL)
        self.TestGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('In Files                                ', 'self.TestGrid')
        self.button_in_files = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnInFilesBrowser, self.button_in_files)
        self.TestGrid.Add(self.button_in_files, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Out Files', 'self.TestGrid')
        self.button_out_files = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnOutFilesBrowser, self.button_out_files)
        self.TestGrid.Add(self.button_out_files, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT,
                          border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Reference Files', 'self.TestGrid')
        self.button_reference_files = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnReferenceFilesBrowser, self.button_reference_files)
        self.TestGrid.Add(self.button_reference_files, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT,
                          border=5)
        self.counter = self.counter + 1

        self.TestGrid.AddGrowableCol(1)
        self.TestOptionBoxSizer.Add(self.TestGrid, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM)
        self.sizer.Add(self.TestOptionBoxSizer, pos=(4, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

    def __init__(self, parent):
        super(ConfigurationTab, self).__init__(parent, -1, style=wx.TAB_TRAVERSAL, name='Panel')

        self.ConfigurationDictionary = dict()
        self.OpenedConfigPath = ""

        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.InitStarter()
        self.InitEmail()
        self.InitSheets()
        self.InitHomework()
        self.InitTest()

        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.sizer)

    def OnCheckerPathBrowse(self, e):
        dialog_checker_path = wx.DirDialog(self, "Choose Checker Path", "",
                                           wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog_checker_path.ShowModal() == wx.ID_OK:
            chosen_path = dialog_checker_path.GetPath()
            self.text_absolute_path.SetValue(chosen_path)

    def OnSecretFileBrowser(self, e):
        dialog_secret_file = wx.FileDialog(self, "Choose Secret File", "", "", "Json file (*.json)|*.json",
                                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog_secret_file.ShowModal() == wx.ID_OK:
            secret_path = dialog_secret_file.GetPath()
            self.text_sheets_secret_file.SetValue(secret_path)

    def OnInFilesBrowser(self, e):
        dialog_in_files = wx.FileDialog(self, "Choose Input Files", "", "", "All files (*.*)|*.*",
                                        wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if (dialog_in_files.ShowModal() == wx.ID_OK):
            all_files_path = dialog_in_files.GetPaths()
            self.text_in_files.SetValue(self.list_to_string(all_files_path))

    def OnOutFilesBrowser(self, e):
        dialog_out_files = wx.FileDialog(self, "Choose Output Files", "", "", "All files (*.*)|*.*",
                                         wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if (dialog_out_files.ShowModal() == wx.ID_OK):
            all_files_path = dialog_out_files.GetPaths()
            self.text_out_files.SetValue(self.list_to_string(all_files_path))

    def OnReferenceFilesBrowser(self, e):
        dialog_reference_files = wx.FileDialog(self, "Choose Reference Files", "", "", "All files (*.*)|*.*",
                                               wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dialog_reference_files.ShowModal() == wx.ID_OK:
            all_files_path = dialog_reference_files.GetPaths()
            self.text_reference_files.SetValue(self.list_to_string(all_files_path))

    def UpdateConfiguration(self):
        for item in self.ConfigurationDictionary.keys():
            var_name = item
            var_name = var_name.replace(' ', '_')
            var_name = var_name.lower()
            var_name = 'self.text_' + var_name
            command = 'self.ConfigurationDictionary.update({\'' + item + '\':' + var_name + '.GetValue()})'
            exec(command)

    def WriteConfiguration(self, filename):
        try:
            with open(filename, 'w') as file:
                for item in self.ConfigurationDictionary.keys():
                    if item == "In Files" or item == "Out Files" or item == "Reference Files":
                        line = item.replace(' ', '') + ' = '
                        right = self.ConfigurationDictionary[item]
                        right = right.replace('[', '')
                        right = right.replace(']', '')
                        line = line + "[" + right + "]\n"
                    else:
                        line = item.replace(' ', '') + ' = ' + '\'' + self.ConfigurationDictionary[item] + '\'\n'
                    line = line.replace('\\', '\\\\')
                    file.write(line)
        except IOError:
            wx.LogError('Fak')
            print('Fakk')

    def LoadConfiguration(self):
        for item in self.ConfigurationDictionary.keys():
            var_name = item
            var_name = var_name.replace(' ', '_')
            var_name = var_name.lower()
            var_name = 'self.text_' + var_name
            itemvalue = self.ConfigurationDictionary[item]
            if itemvalue == " ":
                itemvalue = ""
            command = var_name + '.SetValue(\'' + itemvalue + '\')'
            exec(command)

    def ReadConfiguration(self, filename):
        try:
            with open(filename, 'r') as file:
                line = file.readline()
                while line:
                    if line != "":
                        left = line.split('=')[0]
                        right = line.split('=')[1]
                        left = left.strip()
                        right = right.strip()
                        if left == "InFiles" or left == "OutFiles" or left == "ReferenceFiles":
                            right = right
                        else:
                            right = right.replace('\'', "")
                        left = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", left)
                        self.ConfigurationDictionary.update({left: right})
                    line = file.readline()
        except IOError:
            wx.LogError('Fak')


class StarterTab(wx.lib.scrolledpanel.ScrolledPanel):

    def add_field_parent(self, name, parent):  # syntactic sugar here
        name_with_spaces = name
        name = name.strip()
        name = name.replace(' ', '_')
        setattr(Configuration, 'label_' + name.lower(), wx.StaticText(self, label=name_with_spaces))
        setattr(Configuration, 'text_' + name.lower(), wx.TextCtrl(self))
        cmd = parent + ".Add(Configuration.label_" + name.lower() + ", pos=(" + \
              str(self.counter) + ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)"
        exec(cmd)
        cmd = parent + ".Add(Configuration.text_" + name.lower() + ', pos=(' + str(
            self.counter) + ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)'
        exec(cmd)
        Configuration.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def __init__(self, parent):
        super(StarterTab, self).__init__(parent, -1, style=wx.TAB_TRAVERSAL, name='Panel')

        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.StarterOptionBox = wx.StaticBox(self, label="Starter Options")
        self.StarterOptionBoxSizer = wx.StaticBoxSizer(self.StarterOptionBox, wx.VERTICAL)
        self.StarterGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Timeout', 'self.StarterGrid')

        self.StarterGrid.AddGrowableCol(1)
        self.StarterOptionBoxSizer.Add(self.StarterGrid, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM)
        self.sizer.Add(self.StarterOptionBoxSizer, pos=(0, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=5)

        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.sizer)


class EmailTab(wx.lib.scrolledpanel.ScrolledPanel):

    def add_field_parent(self, name, parent):  # syntactic sugar here
        name_with_spaces = name
        name = name.strip()
        name = name.replace(' ', '_')
        setattr(Configuration, 'label_' + name.lower(), wx.StaticText(self, label=name_with_spaces))
        setattr(Configuration, 'text_' + name.lower(), wx.TextCtrl(self))
        cmd = parent + ".Add(Configuration.label_" + name.lower() + ", pos=(" + \
              str(self.counter) + ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)"
        exec(cmd)
        cmd = parent + ".Add(Configuration.text_" + name.lower() + ', pos=(' + str(
            self.counter) + ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)'
        exec(cmd)
        Configuration.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def __init__(self, parent):
        super(EmailTab, self).__init__(parent, -1, style=wx.TAB_TRAVERSAL, name='Panel')

        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.EmailOptionBox = wx.StaticBox(self, label="Email Options")
        self.EmailOptionBoxSizer = wx.StaticBoxSizer(self.EmailOptionBox, wx.VERTICAL)
        self.EmailGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Email Address', 'self.EmailGrid')

        setattr(Configuration, 'label_password', None)
        setattr(Configuration, 'text_password', None)
        Configuration.label_password = wx.StaticText(self, label="Password")
        self.EmailGrid.Add(Configuration.label_password, pos=(self.counter, 0), span=(1, 1),
                           flag=wx.TOP | wx.LEFT | wx.BOTTOM,
                           border=5)
        Configuration.text_password = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.EmailGrid.Add(Configuration.text_password, pos=(self.counter, 1), span=(1, 4),
                           flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP,
                           border=5)
        Configuration.ConfigurationDictionary.update({'Password': ''})
        self.counter = self.counter + 1

        self.add_field_parent('Email Server Address', 'self.EmailGrid')
        self.add_field_parent('Email Server Port', 'self.EmailGrid')
        self.add_field_parent('Imap Server Address', 'self.EmailGrid')
        self.add_field_parent('Subject', 'self.EmailGrid')
        self.add_field_parent('Zip Format', 'self.EmailGrid')
        self.add_field_parent('Grade Email Subject', 'self.EmailGrid')
        self.add_field_parent('Grade Email Body', 'self.EmailGrid')

        self.EmailGrid.AddGrowableCol(1)
        self.EmailOptionBoxSizer.Add(self.EmailGrid, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT | wx.BOTTOM)
        self.sizer.Add(self.EmailOptionBoxSizer, pos=(0, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.sizer)
        # StaticConfiguration.text_email_address.Bind(wx.EVT_KILL_FOCUS, self.AutoFillEmail)
        #
        #
        # def AutoFillEmail(self, e):
        #     if 'gmail' in StaticConfiguration.text_email_address.GetValue():
        #         StaticConfiguration.text_email_server_address.SetValue('smtp.google.com')
        #         StaticConfiguration.text_imap_server_address.SetValue('imap.google.com')
        #         StaticConfiguration.text_email_server_port.SetValue('587')


class SheetsTab(wx.lib.scrolledpanel.ScrolledPanel):

    def add_field_parent(self, name, parent):  # syntactic sugar here
        name_with_spaces = name
        name = name.strip()
        name = name.replace(' ', '_')
        setattr(Configuration, 'label_' + name.lower(), wx.StaticText(self, label=name_with_spaces))
        setattr(Configuration, 'text_' + name.lower(), wx.TextCtrl(self))
        cmd = parent + ".Add(Configuration.label_" + name.lower() + ", pos=(" + \
              str(self.counter) + ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)"
        exec(cmd)
        cmd = parent + ".Add(Configuration.text_" + name.lower() + ', pos=(' + str(
            self.counter) + ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)'
        exec(cmd)
        Configuration.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def __init__(self, parent):
        super(SheetsTab, self).__init__(parent, -1, style=wx.TAB_TRAVERSAL, name='Panel')

        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.SheetsOptionBox = wx.StaticBox(self, label="Sheets Options")
        self.SheetsOptionBoxSizer = wx.StaticBoxSizer(self.SheetsOptionBox, wx.VERTICAL)
        self.SheetsGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Sheets Secret File', 'self.SheetsGrid')
        self.button_secret_file = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnSecretFileBrowser, self.button_secret_file)
        self.SheetsGrid.Add(self.button_secret_file, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT,
                            border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Sheets Scopes', 'self.SheetsGrid')
        self.add_field_parent('Sheets Application Name ', 'self.SheetsGrid')
        self.add_field_parent('Sheets Key', 'self.SheetsGrid')
        self.add_field_parent('Sheets Id', 'self.SheetsGrid')

        self.SheetsGrid.AddGrowableCol(1)
        self.SheetsOptionBoxSizer.Add(self.SheetsGrid, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        self.sizer.Add(self.SheetsOptionBoxSizer, pos=(0, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.sizer)

    def OnSecretFileBrowser(self, e):
        dialog_secret_file = wx.FileDialog(self, "Choose Secret File", "", "", "Json file (*.json)|*.json",
                                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog_secret_file.ShowModal() == wx.ID_OK:
            secret_path = dialog_secret_file.GetPath()
            Configuration.text_sheets_secret_file.SetValue(secret_path)


class HomeworkTab(wx.lib.scrolledpanel.ScrolledPanel):

    def add_field_parent(self, name, parent):  # syntactic sugar here
        name_with_spaces = name
        name = name.strip()
        name = name.replace(' ', '_')
        setattr(Configuration, 'label_' + name.lower(), wx.StaticText(self, label=name_with_spaces))
        setattr(Configuration, 'text_' + name.lower(), wx.TextCtrl(self))
        cmd = parent + ".Add(Configuration.label_" + name.lower() + ", pos=(" + \
              str(self.counter) + ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)"
        exec(cmd)
        cmd = parent + ".Add(Configuration.text_" + name.lower() + ', pos=(' + str(
            self.counter) + ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)'
        exec(cmd)
        Configuration.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def __init__(self, parent):
        super(HomeworkTab, self).__init__(parent, -1, style=wx.TAB_TRAVERSAL, name='Panel')

        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.HomeworkOptionBox = wx.StaticBox(self, label="Homework Options")
        self.HomeworkOptionBoxSizer = wx.StaticBoxSizer(self.HomeworkOptionBox, wx.VERTICAL)
        self.HomeworkGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('Build String', 'self.HomeworkGrid')
        self.add_field_parent('Exe Filename', 'self.HomeworkGrid')
        self.add_field_parent('Homework', 'self.HomeworkGrid')
        self.add_field_parent('Absolute Path', 'self.HomeworkGrid')

        self.button_checker_path = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnCheckerPathBrowse, self.button_checker_path)
        self.HomeworkGrid.Add(self.button_checker_path, pos=(self.counter, 4), span=(1, 1), flag=wx.RIGHT | wx.EXPAND,
                              border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Relative Download Path', 'self.HomeworkGrid')
        self.add_field_parent('Relative Checker Path', 'self.HomeworkGrid')

        self.HomeworkGrid.AddGrowableCol(1)
        self.HomeworkOptionBoxSizer.Add(self.HomeworkGrid, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        self.sizer.Add(self.HomeworkOptionBoxSizer, pos=(0, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.sizer)

    def OnCheckerPathBrowse(self, e):
        dialog_checker_path = wx.DirDialog(self, "Choose Checker Path", "",
                                           wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog_checker_path.ShowModal() == wx.ID_OK:
            chosen_path = dialog_checker_path.GetPath()
            Configuration.text_absolute_path.SetValue(chosen_path)


class TestsTab(wx.lib.scrolledpanel.ScrolledPanel):

    def add_field_parent(self, name, parent):  # syntactic sugar here
        name_with_spaces = name
        name = name.strip()
        name = name.replace(' ', '_')
        setattr(Configuration, 'label_' + name.lower(), wx.StaticText(self, label=name_with_spaces))
        setattr(Configuration, 'text_' + name.lower(), wx.TextCtrl(self))
        cmd = parent + ".Add(Configuration.label_" + name.lower() + ", pos=(" + \
              str(self.counter) + ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)"
        exec(cmd)
        cmd = parent + ".Add(Configuration.text_" + name.lower() + ', pos=(' + str(
            self.counter) + ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)'
        exec(cmd)
        Configuration.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def __init__(self, parent):
        super(TestsTab, self).__init__(parent, -1, style=wx.TAB_TRAVERSAL, name='Panel')

        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.TestOptionBox = wx.StaticBox(self, label="Tests Options")
        self.TestOptionBoxSizer = wx.StaticBoxSizer(self.TestOptionBox, wx.VERTICAL)
        self.TestGrid = wx.GridBagSizer(5, 5)
        self.counter = 0

        self.add_field_parent('In Files', 'self.TestGrid')
        self.button_in_files = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnInFilesBrowser, self.button_in_files)
        self.TestGrid.Add(self.button_in_files, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Out Files', 'self.TestGrid')
        self.button_out_files = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnOutFilesBrowser, self.button_out_files)
        self.TestGrid.Add(self.button_out_files, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT,
                          border=5)
        self.counter = self.counter + 1

        self.add_field_parent('Reference Files', 'self.TestGrid')
        self.button_reference_files = wx.Button(self, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnReferenceFilesBrowser, self.button_reference_files)
        self.TestGrid.Add(self.button_reference_files, pos=(self.counter, 4), span=(1, 1), flag=wx.EXPAND | wx.RIGHT,
                          border=5)
        self.counter = self.counter + 1

        self.TestGrid.AddGrowableCol(1)
        self.TestOptionBoxSizer.Add(self.TestGrid, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM)
        self.sizer.Add(self.TestOptionBoxSizer, pos=(0, 0), span=(1, 5),
                       flag=wx.TOP | wx.LEFT | wx.EXPAND | wx.BOTTOM, border=5)

        self.sizer.AddGrowableCol(1)
        self.SetSizerAndFit(self.sizer)

    def OnInFilesBrowser(self, e):
        dialog_in_files = wx.FileDialog(self, "Choose Input Files", "", "", "All files (*.*)|*.*",
                                        wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if (dialog_in_files.ShowModal() == wx.ID_OK):
            all_files_path = dialog_in_files.GetPaths()
            Configuration.text_in_files.SetValue(list_to_string(all_files_path))

    def OnOutFilesBrowser(self, e):
        dialog_out_files = wx.FileDialog(self, "Choose Output Files", "", "", "All files (*.*)|*.*",
                                         wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dialog_out_files.ShowModal() == wx.ID_OK:
            all_files_path = dialog_out_files.GetPaths()
            Configuration.text_out_files.SetValue(list_to_string(all_files_path))

    def OnReferenceFilesBrowser(self, e):
        dialog_reference_files = wx.FileDialog(self, "Choose Reference Files", "", "", "All files (*.*)|*.*",
                                               wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dialog_reference_files.ShowModal() == wx.ID_OK:
            all_files_path = dialog_reference_files.GetPaths()
            Configuration.text_reference_files.SetValue(list_to_string(all_files_path))


class MainWindowTabbed(wx.Frame):

    def __init__(self, parent, title):
        super(MainWindowTabbed, self).__init__(parent, title=title, size=(550, 400))

        # Create MenuBar
        menu_bar = wx.MenuBar()

        # Create File Menu Entry in MenuBar
        file_menu = wx.Menu()

        # Creating File Menu Entries
        file_menu_new = wx.MenuItem(file_menu, wx.ID_NEW, '&New')
        file_menu_open = wx.MenuItem(file_menu, wx.ID_OPEN, '&Open')
        file_menu_save = wx.MenuItem(file_menu, wx.ID_SAVE, '&Save')
        file_menu_save_as = wx.MenuItem(file_menu, wx.ID_SAVEAS, 'Save &As')

        # Adding File Menu Entries that we just created
        file_menu.Append(file_menu_new)
        file_menu.Append(file_menu_open)
        file_menu.Append(file_menu_save)
        file_menu.Append(file_menu_save_as)

        # Adding a Separator in File Menu
        file_menu.AppendSeparator()

        # Adding exit entry
        file_menu_exit = wx.MenuItem(file_menu, wx.ID_EXIT, 'E&xit\tCtrl+X')
        # Appending exit entry
        file_menu.Append(file_menu_exit)

        test_menu = wx.Menu()

        test_menu_sheets = wx.MenuItem(test_menu, wx.ID_ANY, '&Sheets')
        test_menu_email = wx.MenuItem(test_menu, wx.ID_ANY, '&Email')

        test_menu.Append(test_menu_sheets)
        test_menu.Append(test_menu_email)

        help_menu = wx.Menu()

        help_menu_help = wx.MenuItem(help_menu, wx.ID_ANY, '&Help')
        help_menu_about = wx.MenuItem(help_menu, wx.ID_ANY, '&About')

        help_menu.Append(help_menu_help)

        help_menu.AppendSeparator()

        help_menu.Append(help_menu_about)

        self.Bind(wx.EVT_MENU, self.OnQuit, file_menu_exit)
        self.Bind(wx.EVT_MENU, self.OnNew, file_menu_new)
        self.Bind(wx.EVT_MENU, self.OnOpen, file_menu_open)
        self.Bind(wx.EVT_MENU, self.OnSave, file_menu_save)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, file_menu_save_as)
        self.Bind(wx.EVT_MENU, self.OnHelp, help_menu_help)
        self.Bind(wx.EVT_MENU, self.OnAbout, help_menu_about)
        self.Bind(wx.EVT_MENU, self.OnTestEmail, test_menu_email)
        self.Bind(wx.EVT_MENU, self.OnTestSheets, test_menu_sheets)

        menu_bar.Append(file_menu, '&File')
        menu_bar.Append(test_menu, '&Test')
        menu_bar.Append(help_menu, 'Hel&p')

        self.SetMenuBar(menu_bar)

        self.main_panel = wx.Panel(self)
        self.notebook = wx.Notebook(self.main_panel)

        self.tab_1 = StarterTab(self.notebook)
        self.tab_2 = EmailTab(self.notebook)
        self.tab_3 = SheetsTab(self.notebook)
        self.tab_4 = HomeworkTab(self.notebook)
        self.tab_5 = TestsTab(self.notebook)

        self.notebook.AddPage(self.tab_1, "Starter")
        self.notebook.AddPage(self.tab_2, "Email")
        self.notebook.AddPage(self.tab_3, "Sheets")
        self.notebook.AddPage(self.tab_4, "Homework")
        self.notebook.AddPage(self.tab_5, "Tests")

        # sizer = wx.GridBagSizer(1, 1)
        # sizer.Add(self.notebook, pos=(0, 0), span=(1, 1), flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        # sizer.AddGrowableCol(0)
        # sizer.AddGrowableRow(0)

        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.notebook, wx.EXPAND)

        self.main_panel.SetSizer(self.sizer)

        self.icon = wx.Icon()
        self.icon.CopyFromBitmap(wx.Bitmap('icon.ico', wx.BITMAP_TYPE_ANY))
        self.SetIcon(self.icon)

        self.Center()
        self.Show()

        self.notebook.ChangeSelection(1)  # fixes a black square bug that appeared
        self.notebook.ChangeSelection(0)  # fix the symptoms not the cause

    def OnQuit(self, e):
        self.Close()

    def OnNew(self, e):
        Configuration.OpenedConfigPath = ""
        for item in Configuration.ConfigurationDictionary:
            Configuration.ConfigurationDictionary.update({item: ' '})
        Configuration.LoadConfiguration()

    def OnOpen(self, e):
        dialog_open = wx.FileDialog(self, "Import Configuration", "", "", "Python Configuration (*.py)|*.py",
                                    wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog_open.ShowModal() == wx.ID_OK:
            Configuration.OpenedConfigPath = dialog_open.GetPath()
            Configuration.ReadConfiguration(Configuration.OpenedConfigPath)
            Configuration.LoadConfiguration()

    def OnSave(self, e):
        if Configuration.OpenedConfigPath == "":
            self.OnSaveAs(e)
        else:
            Configuration.UpdateConfiguration()
            Configuration.WriteConfiguration(Configuration.OpenedConfigPath)

    def OnSaveAs(self, e):
        dialog_save = wx.FileDialog(self, "Save Configuration", wildcard=".py files (*.py)|*.py",
                                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog_save.ShowModal() == wx.ID_CANCEL:
            return
        pathname = dialog_save.GetPath()
        Configuration.UpdateConfiguration()
        Configuration.WriteConfiguration(pathname)
        Configuration.OpenedConfigPath = pathname

    def OnHelp(self, e):
        help_window = HelpWindow(self)

    def OnAbout(self, e):
        about_window = AboutWindow(self)

    def OnTestSheets(self, e):
        SheetsSecretFile = Configuration.ConfigurationDictionary['Sheets Secret File']
        SheetsScopes = Configuration.ConfigurationDictionary['Sheets Scopes']
        SheetsApplicationName = Configuration.ConfigurationDictionary['Sheets Application Name']
        SheetsKey = Configuration.ConfigurationDictionary['Sheets Key']
        SheetsId = Configuration.ConfigurationDictionary['Sheets Id']
        SheetsTester = SheetsTest(SheetsSecretFile, SheetsId, SheetsScopes, SheetsKey, SheetsApplicationName)
        if SheetsTester.Success:
            InfoBox(self,
                    'Connection to the specified Spreadsheet was possible.\n The word \'Works\' has been written in A1',
                    'Success')
            SheetsTester.Restore()
        else:
            WarnBox(self, 'Connection to the specified Spreadsheet could not be established', 'Connection Failed')

    def OnTestEmail(self, e):
        EmailAddress = Configuration.ConfigurationDictionary['Email Address']
        Password = Configuration.ConfigurationDictionary['Password']
        EmailServerAddress = Configuration.ConfigurationDictionary['Email Server Address']
        EmailServerPort = Configuration.ConfigurationDictionary['Email Server Port']
        try:
            server = smtplib.SMTP(EmailServerAddress, int(EmailServerPort))
            server.starttls()
            server.login(EmailAddress, Password)
        except Exception:
            WarnBox(self, 'Connection to the email server has failed', 'Connection Failed')
            return
        InfoBox(self, 'Connection to the email server was SUCCESSFUL', 'Success')
        server.close()


class MainWindow(wx.Frame):

    def list_to_string(self, list):
        result = ""
        for element in list:
            result = result + '\'' + element + '\'' + ", "
        result = result[:len(result) - 2]
        result = '[' + result + ']'
        result = result.replace('\\', "\\\\")
        return result

    def add_simple_field(self, name):  # syntactic sugar here
        name = name.replace(' ', '_')
        setattr(self, 'label_' + name.lower(), wx.StaticText(self.panel, label=name.replace('_', ' ')))
        setattr(self, 'text_' + name.lower(), wx.TextCtrl(self.panel))
        exec(
            "self.sizer.Add(self.label_" + name.lower() + ", pos=(" + str(self.counter) +
            ", 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)")
        exec(
            'self.sizer.Add(self.text_' + name.lower() + ', pos=(' + str(self.counter) +
            ', 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)')
        self.ConfigurationDictionary.update({name.replace('_', ' '): ''})
        self.counter = self.counter + 1

    def add_line(self, label, text, position):
        self.sizer.Add(label, pos=(position, 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
        self.sizer.Add(text, pos=(position, 1), span=(1, 1), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=5)

    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title, size=(550, 400))

        self.ConfigurationDictionary = dict()
        self.OpenedConfigPath = ""

        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu_new = wx.MenuItem(file_menu, wx.ID_NEW, '&New')
        file_menu_open = wx.MenuItem(file_menu, wx.ID_OPEN, '&Open')
        file_menu_save = wx.MenuItem(file_menu, wx.ID_SAVE, '&Save')
        file_menu_save_as = wx.MenuItem(file_menu, wx.ID_SAVEAS, 'Save &As')
        file_menu.Append(file_menu_new)
        file_menu.Append(file_menu_open)
        file_menu.Append(file_menu_save)
        file_menu.Append(file_menu_save_as)
        file_menu_exit = wx.MenuItem(file_menu, wx.ID_EXIT, 'E&xit\tCtrl+X')
        file_menu.Append(file_menu_exit)
        self.Bind(wx.EVT_MENU, self.OnQuit, file_menu_exit)
        self.Bind(wx.EVT_MENU, self.OnNew, file_menu_new)
        self.Bind(wx.EVT_MENU, self.OnOpen, file_menu_open)
        self.Bind(wx.EVT_MENU, self.OnSave, file_menu_save)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, file_menu_save_as)
        menu_bar.Append(file_menu, '&File')
        self.SetMenuBar(menu_bar)

        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1, style=wx.TAB_TRAVERSAL, name='Panel')
        self.panel.SetAutoLayout(1)
        self.panel.SetupScrolling()
        self.sizer = wx.GridBagSizer(5, 5)

        self.counter = 0

        self.add_simple_field('Timeout')
        self.add_simple_field('Homework')
        self.add_simple_field('Email Address')

        self.label_password = wx.StaticText(self.panel, label="Password")
        self.sizer.Add(self.label_password, pos=(3, 0), span=(1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
        self.text_password = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.sizer.Add(self.text_password, pos=(3, 1), span=(1, 4), flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP,
                       border=5)
        self.counter = self.counter + 1  # password field
        self.ConfigurationDictionary.update({'Password': ''})

        self.add_simple_field('Email Server Address')
        self.add_simple_field('Email Server Port')
        self.add_simple_field('Imap Server Address')
        self.add_simple_field('Subject')
        self.add_simple_field('Zip Format')
        self.add_simple_field('Grade Email Subject')
        self.add_simple_field('Grade Email Body')

        self.add_simple_field('Sheets Secret File')
        self.button_secret_file = wx.Button(self.panel, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnSecretFileBrowser, self.button_secret_file)
        self.sizer.Add(self.button_secret_file, pos=(self.counter, 4), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.add_simple_field('Sheets Scopes')
        self.add_simple_field('Sheets Application Name')
        self.add_simple_field('Sheets Key')
        self.add_simple_field('Sheets Id')
        self.add_simple_field('Build String')
        self.add_simple_field('Exe Filename')
        self.add_simple_field('Absolute Path')

        self.button_checker_path = wx.Button(self.panel, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnCheckerPathBrowse, self.button_checker_path)
        self.sizer.Add(self.button_checker_path, pos=(self.counter, 4), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.add_simple_field('Relative Download Path')
        self.add_simple_field('Relative Checker Path')

        self.add_simple_field('In Files')
        self.button_in_files = wx.Button(self.panel, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnInFilesBrowser, self.button_in_files)
        self.sizer.Add(self.button_in_files, pos=(self.counter, 4), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.add_simple_field('Out Files')
        self.button_out_files = wx.Button(self.panel, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnOutFilesBrowser, self.button_out_files)
        self.sizer.Add(self.button_out_files, pos=(self.counter, 4), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.add_simple_field('Reference Files')
        self.button_reference_files = wx.Button(self.panel, label="Browse...", size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnReferenceFilesBrowser, self.button_reference_files)
        self.sizer.Add(self.button_reference_files, pos=(self.counter, 4), flag=wx.EXPAND | wx.RIGHT, border=5)
        self.counter = self.counter + 1

        self.sizer.AddGrowableCol(1)

        self.icon = wx.Icon()
        self.icon.CopyFromBitmap(wx.Bitmap('icon.ico', wx.BITMAP_TYPE_ANY))
        self.SetIcon(self.icon)

        self.panel.SetSizerAndFit(self.sizer)
        self.Center()
        self.Show()

    def OnCheckerPathBrowse(self, e):
        dialog_checker_path = wx.DirDialog(self.panel, "Choose Checker Path", "",
                                           wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog_checker_path.ShowModal() == wx.ID_OK:
            chosen_path = dialog_checker_path.GetPath()
            self.text_absolute_path.SetValue(chosen_path)

    def OnSecretFileBrowser(self, e):
        dialog_secret_file = wx.FileDialog(self.panel, "Choose Secret File", "", "", "Json file (*.json)|*.json",
                                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog_secret_file.ShowModal() == wx.ID_OK:
            secret_path = dialog_secret_file.GetPath()
            self.text_sheets_secret.SetValue(secret_path)

    def OnInFilesBrowser(self, e):
        dialog_in_files = wx.FileDialog(self.panel, "Choose Input Files", "", "", "All files (*.*)|*.*",
                                        wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if (dialog_in_files.ShowModal() == wx.ID_OK):
            all_files_path = dialog_in_files.GetPaths()
            self.text_input_files.SetValue(self.list_to_string(all_files_path))

    def OnOutFilesBrowser(self, e):
        dialog_out_files = wx.FileDialog(self.panel, "Choose Output Files", "", "", "All files (*.*)|*.*",
                                         wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if (dialog_out_files.ShowModal() == wx.ID_OK):
            all_files_path = dialog_out_files.GetPaths()
            self.text_output_files.SetValue(self.list_to_string(all_files_path))

    def OnReferenceFilesBrowser(self, e):
        dialog_reference_files = wx.FileDialog(self.panel, "Choose Reference Files", "", "", "All files (*.*)|*.*",
                                               wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dialog_reference_files.ShowModal() == wx.ID_OK:
            all_files_path = dialog_reference_files.GetPaths()
            self.text_reference_files.SetValue(self.list_to_string(all_files_path))

    def OnQuit(self, e):
        self.Close()

    def OnNew(self, e):
        self.OpenedConfigPath = ""
        for item in self.ConfigurationDictionary:
            self.ConfigurationDictionary.update({item: ' '})
        self.LoadConfiguration()

    def OnOpen(self, e):
        dialog_open = wx.FileDialog(self.panel, "Import Configuration", "", "", "Python Configuration (*.py)|*.py",
                                    wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog_open.ShowModal() == wx.ID_OK:
            self.OpenedConfigPath = dialog_open.GetPath()
            self.ReadConfiguration(self.OpenedConfigPath)
            self.LoadConfiguration()

    def OnSave(self, e):
        if self.OpenedConfigPath == "":
            self.OnSaveAs(e)
        else:
            self.UpdateConfiguration()
            self.WriteConfiguration(self.OpenedConfigPath)

    def OnSaveAs(self, e):
        dialog_save = wx.FileDialog(self.panel, "Save Configuration", wildcard=".py files (*.py)|*.py",
                                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog_save.ShowModal() == wx.ID_CANCEL:
            return
        pathname = dialog_save.GetPath()
        self.UpdateConfiguration()
        self.WriteConfiguration(pathname)
        self.OpenedConfigPath = pathname

    def UpdateConfiguration(self):
        for item in self.ConfigurationDictionary.keys():
            var_name = item
            var_name = var_name.replace(' ', '_')
            var_name = var_name.lower()
            var_name = 'self.text_' + var_name
            command = 'self.ConfigurationDictionary.update({\'' + item + '\':' + var_name + '.GetValue()})'
            exec(command)

    def WriteConfiguration(self, filename):
        try:
            with open(filename, 'w') as file:
                for item in self.ConfigurationDictionary.keys():
                    line = item.replace(' ', '') + ' = ' + '\"' + self.ConfigurationDictionary[item] + '\"\n'
                    file.write(line)
        except IOError:
            wx.LogError('Fak')

    def LoadConfiguration(self):
        for item in self.ConfigurationDictionary.keys():
            var_name = item
            var_name = var_name.replace(' ', '_')
            var_name = var_name.lower()
            var_name = 'self.text_' + var_name
            itemvalue = self.ConfigurationDictionary[item]
            if itemvalue == " ":
                itemvalue = ""
            command = var_name + '.SetValue(\'' + itemvalue + '\')'
            exec(command)

    def ReadConfiguration(self, filename):
        try:
            with open(filename, 'r') as file:
                line = file.readline()
                while line:
                    if line != "":
                        left = line.split('=')[0]
                        right = line.split('=')[1]
                        left = left.strip()
                        right = right.strip()
                        right = right.replace('\"', "")
                        left = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", left)
                        self.ConfigurationDictionary.update({left: right})
                    line = file.readline()
        except IOError:
            wx.LogError('Fak')


class AboutWindow(wx.Frame):

    def __init__(self, parent):
        super(AboutWindow, self).__init__(parent=parent, title='About', size=(250, 200))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, id=wx.ID_ANY,
                              label="\n\n\n   Developed by yours truly...\n   Alex Ciobanu 2017")
        sizer.Add(label)
        panel.SetSizer(sizer)
        self.Center()
        self.Show()


class HelpWindow(wx.Frame):

    def __init__(self, parent):
        super(HelpWindow, self).__init__(parent=parent, title='Help', size=(250, 200))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, id=wx.ID_ANY,
                              label="\n\n\n   Please Consider reading the readme first...\n   Much appreciated")
        sizer.Add(label)
        panel.SetSizer(sizer)
        self.Center()
        self.Show()


if __name__ == '__main__':
    print("Here it goes")
    Configuration = StaticConfiguration()
    app = wx.App()
    MainWindowTabbed(None, 'Checker Configurator')
    app.MainLoop()
