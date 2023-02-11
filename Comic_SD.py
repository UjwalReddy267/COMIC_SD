from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from UI.gui import MainWindow
from datetime import datetime
import os
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout

import shutil  


if not os.path.exists('./downloads'):
    os.mkdir('downloads')
if not os.path.exists('./downloads/temp'):
    os.mkdir('downloads/temp')
with open('log.txt','a') as log:
    log.write(str(datetime.now())+'\n')

app = QApplication(sys.argv)
window = MainWindow()
window.start()
app.exec()
shutil.rmtree('downloads/temp')

