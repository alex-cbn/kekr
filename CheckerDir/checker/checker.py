import importlib
import os
import smtplib
import subprocess as sub
import sys
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import groupby

import utils

sys.path.insert(0, '../')
configuration = importlib.import_module('config')
error = importlib.import_module('errors')
status = importlib.import_module('status')
first_param_list = ["exe", "zip", "source"]


def compare_files(file_path1, file_path2):
    reference_file = open(file_path1, 'r')
    test_file = open(file_path2, 'r')
    reference_text = reference_file.readlines()
    test_text = test_file.readlines()
    reference_text = [s.strip() for s in reference_text]
    test_text = [s.strip() for s in test_text]
    test_text = list(dict.fromkeys(test_text))
    reference_text = list(dict.fromkeys(reference_text))
    if str(reference_text) == str(test_text):
        return True
    else:
        return False


def prepare_file(file_path):
    file = open(file_path, 'r')
    text = file.readlines()
    text = [(s.strip()).replace(' ', '') for s in text]
    text = list(x[0] for x in groupby(text))
    return text


def split_in_tasks(file_content):
    the_list = list()
    try:
        while True:
            _index = file_content.index("")
            the_list.append(file_content[:_index])
            file_content = file_content[_index + 1:]
    except:
        the_list.append(file_content)
        return the_list


def unsafe_split_in_tasks(file_content):
    file_content = '`'.join(str(e) for e in file_content)
    list_o_strings = file_content.split("``")
    the_list = list()
    for _list in list_o_strings:
        _list = _list.split("`")
        the_list.append(_list)
    return the_list


def output_grade(file_reference, file_test):
    text_test = prepare_file(file_test)
    text_reference = prepare_file(file_reference)
    tasks_test = split_in_tasks(text_test)
    tasks_reference = split_in_tasks(text_reference)
    tests_passed = 0
    for task_index in range(len(tasks_reference)):
        if task_index >= len(tasks_test):
            return grade_steps[tests_passed]
        if str(tasks_reference[task_index]) == str(tasks_test[task_index]):
            tests_passed = tests_passed + 1
    return 10 * tests_passed/len(tasks_reference)


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
    print(student_name + " has been notified on email!\n")


def check_parameters():
    if len(sys.argv) != 4:
        utils.report_error(error.WrongArgumentCount)

    if sys.argv[1] not in first_param_list:
        utils.report_error(error.WrongMode)

    if not os.path.isfile(sys.argv[2]):
        utils.report_error(error.WrongFile)


def run_test(index):
    os.system("cd .")
    args_string = configuration.InFiles[index] + " " + configuration.OutFiles[index]
    p = sub.Popen(executable=configuration.ExeFilename,
                  args=[' ', configuration.InFiles[index], configuration.OutFiles[index]])
    try:
        p.wait(4)
    except:
        return 0
    if not os.path.isfile(configuration.OutFiles[index]):
        return 0
    grade = output_grade(configuration.ReferenceFiles[index], configuration.OutFiles[index])
    return grade


if __name__ == '__main__':

    student_name = "<necunoscut>"
    check_parameters()
    print(status.DoneCheckParameters)
    mode = sys.argv[1]
    homework = configuration.Homework  # TODO I tell no lies
    filename = sys.argv[2]
    destination_address = sys.argv[3]
    exe_filename = configuration.ExeFilename

    if mode == "zip":
        utils.check_zip_name(filename)
        utils.unzip_file(filename)

        student_name = utils.get_student_name(filename)

        print(status.DoneUnzipping)

    if mode == "zip" or mode == "source":
        build_thread = threading.Thread(target=utils.build_source)
        build_thread.start()
        build_thread.join()
        if not os.path.isfile(configuration.ExeFilename):
            email_server = get_mail_server()
            send_mail(email_server, destination_address, "Eroare",
                      error.NotCompiled)
            email_server.close()
            utils.report_error(error.BuildFailed)
        print(status.DoneCompiling)

    if mode == "exe":
        exe_filename = filename

    print(status.BeginningCheck + student_name)

    utils.clear_output_files(homework)

    score = 0
    number_of_tests = len(configuration.InFiles)
    one_test_ponder = 10 / number_of_tests

    for test_index in range(number_of_tests):
        test_result = run_test(test_index)
        utils.print_test_result(test_index, test_result)
        score += test_result
    score = score / (number_of_tests * 10)
    score = score * 100
    score = int(score)
    score = score / 100
    os.system("taskkill /f /im " + configuration.ExeFilename)
    print("Nota obtinuta este: " + str(score) + " din 10")
    nume = student_name.split(' ')[0]
    prenume = student_name.split(' ')[1]
    students_group = filename.split('.')[0]
    grading_process = sub.Popen(["python", "grading.py", nume, prenume, str(score), students_group])
    grading_process.wait(timeout=20)
    email_server = get_mail_server()
    send_mail(email_server, destination_address, configuration.GradeEmailSubject,
              configuration.GradeEmailBody + str(score))
    email_server.quit()
    utils.clear_on_exit(mode)
