from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from datetime import datetime
import os
from tkinter import *
from gui import gui

import shutil  

if not os.path.exists('./downloads'):
    os.mkdir('downloads')
if not os.path.exists('./downloads/temp'):
    os.mkdir('downloads/temp')
with open('log.txt','a') as log:
    log.write(str(datetime.now())+'\n')

root = gui()
root.start()


mainloop()

input()
shutil.rmtree('downloads/temp')
