import importlib
import os
import re
import sys
import zipfile

sys.path.insert(0, '../')
configuration = importlib.import_module('config')
error = importlib.import_module('errors')
status = importlib.import_module('status')

Tema1_cmds = [
    " ./Tema1/in/1_in.txt ./Tema1/out/1_out.txt",
    " ./Tema1/in/2_in.txt ./Tema1/out/2_out.txt",
    " ./Tema1/in/3_in.txt ./Tema1/out/3_out.txt",
    " ./Tema1/in/4_in.txt ./Tema1/out/4_out.txt",
    " ./Tema1/in/5_in.txt ./Tema1/out/5_out.txt"
]


def change_text_color(status, string):
    attr = []
    if status == "green":
        attr.append('32')
    else:
        attr.append('31')
        attr.append('1')

    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)


def report_error(err_string):
    coloured_string = change_text_color("red", err_string)
    print(coloured_string)
    exit(-1)


def unzip_file(zip_name):
    os.system("RMDIR .\\Proiect /s /q ")
    zip_ref = zipfile.ZipFile(zip_name, 'r')
    zip_ref.extractall(".\\Proiect")
    zip_ref.close()


def check_zip_name(zip_name):
    zip_name_regex = re.compile(configuration.ZipFormat)
    if not zip_name_regex.match(zip_name):
        report_error(error.WrongZipName)


def build_source():
    delete_file(configuration.ExeFilename)
    cmd = configuration.BuildString
    os.system(cmd)


def get_student_name(zip_filename):
    return " ".join(zip_filename.split('.')[1:3])


def clear_output_files(homework):
    path = homework + "/out/"
    filelist = [f for f in os.listdir(path) if f.endswith(".txt")]
    for f in filelist:
        os.remove(path + f)


def print_test_result(index, value):
    string = "TEST " + str(index + 1).rjust(3) + "........ " + str(value)

    # change text colour for succes/fail
    if value == 10:
        coloured_string = change_text_color("green", string)
    else:
        coloured_string = change_text_color("red", string)

    print(coloured_string)


def load_public_tests(homework):
    return Tema1_cmds


def delete_file(filename):
    if os.path.isfile(filename):
        os.remove(filename)


def clear_on_exit(mode):
    if mode == "source":  # sterg executabilul generat
        delete_file(configuration.ExeFilename)

    if mode == "zip":  # sterg toate fisierele din arhiva + exe generat
        os.system("RMDIR .\\Proiect /s /q ")
        delete_file(configuration.ExeFilename)
