from tkinter import *
from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline

def clear_window(win):
    for widget in win.winfo_children():
        widget.destroy()

def start():
    root = Tk()
    root.geometry("500x500") 
    frame = Frame(root,bd=10)
    frame.pack(pady=30)
    query_box = Entry(frame)
    query_box.pack()
    search_button = Button(frame,text='Search',command=lambda:search(query_box.get(),frame))
    download_button = Button(frame,text='Download',command=lambda:download(query_box.get(),frame))
    search_button.pack()
    download_button.pack()
    return root,frame


def search(query,frame):
    clear_window(frame)
    global r
    r = StringVar()
    r.set(comicextra)
    Radiobutton(frame,text='comicextra',variable=r,value='comicextra').pack()
    Radiobutton(frame,text='comiconlinefree',variable=r,value='comiconlinefree').pack()
    Radiobutton(frame,text='readcomiconline',variable=r,value='readcomiconline').pack()
    Button(frame,text='Search',command=lambda:download(query,r.get())).pack()

def download(query,site=None):
    if 'comicextra' in query or 'comicextra' in site:
        a = comicextra(query)
    if 'comiconlinefree' in query or 'comiconlinefree' in site:
        a = comiconline(query)
    if 'readcomiconline' in query or 'readcomiconline' in site:
        a = readcomiconline(query)

def listComics():
    pass

def listChapters():
    pass
