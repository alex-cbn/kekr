import imaplib
import importlib
import os
import re
import shutil
import smtplib
import subprocess
import zipfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pyzmail
from pyzmail.parse import get_mail_parts

smtp_server = None
configuration = importlib.import_module('config')
error = importlib.import_module('errors')


def get_mail_server(fromaddr=configuration.EmailAddress, password=configuration.Password):
    try:
        server = smtplib.SMTP(configuration.EmailServerAddress, int(configuration.EmailServerPort))
        server.starttls()
        server.login(fromaddr, password)
    except Exception:
        print(error.ConnectionServerMail)
        exit(-2)
    return server


def send_mail(server, toaddr, subject, body, fromaddr=configuration.EmailAddress):
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    text = msg.as_string()
    try:
        server.sendmail(fromaddr, toaddr, text)
    except:
        print(error.SendEmail + str(toaddr))


def delete_file(filename):
    if os.path.isfile(filename):
        os.remove(filename)


def get_attachment(current_email_parts, extension):
    for part in current_email_parts:
        if part.filename is not None:
            return part.filename, part.get_payload()
        else:
            continue
            # return part.get_filename(), part.get_payload(decode=True)

    return None, None


def fetch_mail(connection, number, typ, data):
    typ = None
    data = None
    typ, data = connection.fetch(number, '(RFC822)')
    return typ, data


def get_messages(servername=configuration.ImapServerAddress, usernm=configuration.EmailAddress,
                 passwd=configuration.Password):
    all_mails = []
    attach_names = []
    attach_contents = []
    conn = imaplib.IMAP4_SSL(servername)
    conn.login(usernm, passwd)
    conn.select('Inbox')
    typ, data = conn.search(None, '(UNSEEN)', '(SUBJECT' + configuration.Subject + ')')  # SUBJECT "%s")' % subject)
    for num in data[0].split():
        typ = ""
        data = ""
        typ, data = conn.fetch(num, '(RFC822)')
        # fetchThread = threading.Thread(target=fetch_mail, args=(conn, num, typ, data))
        # fetchThread.start()
        # fetchThread.join(timeout=40.0)
        if typ is None and data is None:
            continue
        current_mail_bytes = data[0][1]
        current_mail = pyzmail.message_from_bytes(current_mail_bytes)
        typ, data = conn.store(num, '+FLAGS', '\\Seen')
        current_mail_parts = get_mail_parts(current_mail)
        attach_name, attach_content = get_attachment(current_mail_parts, '.zip')
        all_mails.append(current_mail)
        attach_names.append(attach_name)
        attach_contents.append(attach_content)
    return all_mails, attach_names, attach_contents


def check_rules(msg, attach_name):  # TODO actually send errors
    reg_email_archive = re.compile(configuration.ZipFormat)
    reg_email_subject = re.compile(configuration.Subject)

    if not (reg_email_subject.match(msg["Subject"])):
        send_mail(smtp_server, msg["From"], error.EmailSubject, error.WrongSubject)
        return False

    if attach_name is None:
        send_mail(smtp_server, msg["From"], error.EmailSubject, error.MissingArchive)
        return False

    if not (reg_email_archive.match(attach_name)):
        send_mail(smtp_server, msg["From"], error.EmailSubject, error.WrongZipName)
        return False

    return True


def save_file(attach_name, attach_content):
    # create necessary paths
    student_zip_file_name = configuration.AbsolutePath + configuration.RelativeDownloadPath + "zipped\\" + attach_name
    student_current_dir = configuration.AbsolutePath + configuration.RelativeDownloadPath + "unzipped\\" + \
                          os.path.splitext(attach_name)[0].replace('.', '_') + "\\"

    # delete zip if already exists
    if os.path.exists(student_zip_file_name):
        os.remove(student_zip_file_name)

    if os.path.exists(student_current_dir):
        shutil.rmtree(student_current_dir)

    os.makedirs(student_current_dir)

    # write down the zip file from the student
    open(student_zip_file_name, 'wb').write(attach_content)
    open(student_current_dir + attach_name, 'wb').write(attach_content)

    # extract it into the student specific dir
    try:
        zip_ref = zipfile.ZipFile(student_zip_file_name, 'r')
        zip_ref.extractall(student_current_dir)
    except Exception:
        print(error.ZipExtract)
    zip_ref.close()


def save_archive_to_checker(attach_name, attach_content):
    # delete all zip files from the checker folder
    filelist = [f for f in os.listdir(os.path.join(".", configuration.RelativeCheckerPath)) if f.endswith(".zip")]
    for f in filelist:
        os.remove(os.path.join(".", configuration.RelativeCheckerPath, f))

    open(os.path.join(".", configuration.RelativeCheckerPath, attach_name), 'wb').write(attach_content)


def run_checker(attach_name, msg):
    student_email = msg["From"]
    student_email = student_email.split('<')[1]
    student_email = student_email.split('>')[0]
    cmd_string = "cd " + configuration.RelativeCheckerPath + " && python checker.py zip " + attach_name + " " + student_email
    checker_process = subprocess.Popen(cmd_string, shell=True)
    checker_process.wait(timeout=50)
    os.system("cd ..")  # TODO


def do_everything():
    logfile = open(configuration.AbsolutePath + "log.txt", "a+")
    smtp_server = get_mail_server()
    print("Looking for Attachments...")
    all_msg, all_attachments_name, all_attachments = get_messages()  # sa nu mergi!
    if len(all_msg) == 0:
        print("Nothing found :(")
    else:
        print("Done Fetching Attachments!")
    for msg, attach_name, attach_content in zip(all_msg, all_attachments_name, all_attachments):

        if check_rules(msg, attach_name):

            save_file(attach_name, attach_content)

            save_archive_to_checker(attach_name, attach_content)

            run_checker(attach_name, msg)

        else:
            print(error.Reported + msg["From"])
            send_mail(smtp_server, msg['From'].split('<')[1].split('>')[0], 'Eroare la tema',
                      error.NotRan)
            logfile.write("EROARE pentru " + msg["From"] + "\n")

    smtp_server.quit()


# def configure():
#     # sys.path.insert(0, '../')
#     global configuration
#     global error
#     configuration = importlib.import_module('config')
#     error = importlib.import_module('config')


if __name__ == '__main__':
    print(configuration.EmailAddress)
    do_everything()
