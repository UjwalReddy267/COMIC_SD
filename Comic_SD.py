import traceback 
from UI.gui import MainWindow
from datetime import datetime
import os
import sys
from PyQt6.QtWidgets import QApplication
import shutil 
try:

    if not os.path.exists('./downloads'):
        os.mkdir('./downloads')
    if not os.path.exists('./downloads/temp'):
        os.mkdir('./downloads/temp')
    with open('log.txt','a') as log:
        log.write(str(datetime.now())+'\n')
    json = None
    if os.path.exists('./colors.json'):
        json = './colors.json'

    app = QApplication(sys.argv)
    window = MainWindow(json)
    window.start()
    app.exec()
    shutil.rmtree('./downloads/temp')

except Exception as e:
    with open('log.txt','a') as f:
        f.write(str(e))
        f.write(traceback.format_exc())
