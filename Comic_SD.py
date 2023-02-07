from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from datetime import datetime
import os
from tkinter import *
import gui

if not os.path.exists('./downloads'):
    os.mkdir('downloads')
with open('log.txt','a') as log:
    log.write(str(datetime.now())+'\n')

root = gui.start()

root.mainloop()

input()

