import subprocess
import time
import config as configuration
if __name__ == '__main__':
    while True:
        print("Launching a new instance")
        mainProcess = subprocess.Popen("python main.py", shell=True)
        mainProcess.wait()
        time.sleep(int(configuration.Timeout))
