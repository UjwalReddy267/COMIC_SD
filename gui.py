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
    global frame
    frame = Frame(root,bd=10)
    frame.grid()

    query_box = Entry(frame)
    query_box.grid(row=0,column=0)
    go_button = Button(frame,text='Go!',command=lambda:go(query_box.get()))
    go_button.grid(row=1,column=0)
    return root,frame

def go(query):
    if '.' not in query and '/' not in query:
        site_select(query)
    else:
        download(query)

def site_select(query):
    clear_window(frame)
    global r
    r = IntVar()
    r.set(1)
    Label(frame,text='Select Website').grid(row=0,column=0)
    Radiobutton(frame,text='comicextra',variable=r,value=1).grid(row=1,column=0,sticky=W)
    Radiobutton(frame,text='comiconlinefree',variable=r,value=2).grid(row=2,column=0,sticky=W)
    Radiobutton(frame,text='readcomiconline',variable=r,value=3).grid(row=3,column=0,sticky=W)
    Button(frame,text='Search',command=lambda:download(query,r.get())).grid(row=4,column=0)


def download(query,r=0):
    if 'comicextra' in query or r==1:
        a = comicextra(query)
    if 'comiconlinefree' in query or r==2:
        a = comiconline(query)
    if 'readcomiconline' in query or r==3:
        a = readcomiconline(query)

def listComics():
    pass

def listChapters():
    pass
