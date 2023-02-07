from tkinter import *
from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline

def clear_window(win):
    for widget in win.winfo_children():
        widget.destroy()

def start():
    root = Tk()
    root.geometry("700x500") 
    global frame
    frame = Frame(root,bd=10)
    frame.grid()

    query_box = Entry(frame)
    query_box.grid(row=0,column=0)
    go_button = Button(frame,text='Go!',command=lambda:go(query_box.get()))
    go_button.grid(row=1,column=0)
    return root

def go(query):
    if '.' not in query and '/' not in query:
        site_select(query)
    else:
        parseLink(query)

def site_select(query):
    clear_window(frame)
    global r
    r = IntVar()
    r.set(1)
    Label(frame,text='Select Website').grid(row=0,column=0)
    Radiobutton(frame,text='comicextra',variable=r,value=1).grid(row=1,column=0,sticky=W)
    Radiobutton(frame,text='comiconlinefree',variable=r,value=2).grid(row=2,column=0,sticky=W)
    Radiobutton(frame,text='readcomiconline',variable=r,value=3).grid(row=3,column=0,sticky=W)
    Button(frame,text='Search',command=lambda:search(query,r.get())).grid(row=4,column=0)


def parseLink(query,r=0):
    if 'comicextra' in query:
        a = comicextra()
    elif 'comiconlinefree' in query:
        a = comiconline()
    elif 'readcomiconline' in query:
        a = readcomiconline()
    
    if a.is_chap_list(query):
        listChapters(a,query)
    else:
        download(a,[query])

def search(query,site):
    if site == 1:
        a = comicextra()
    elif site == 2:
        a = comiconline()
    elif site == 3:
        a = readcomiconline()
    

def listComics():
    pass

def listChapters(a,query):
    soup = a.get_soup(query)
    comics,titles = a.get_chaps(soup)

    clear_window(frame)
    scrollBar = Scrollbar(frame)
    listBox = Listbox(frame,selectmode=EXTENDED,yscrollcommand=scrollBar.set,height=25,width=75)

    for i in range(len(titles)):
        listBox.insert(i,titles[i])

    listBox.grid(row=0,column=0)
    scrollBar.config( command = listBox.yview )
    scrollBar.grid(row=0,column=1,sticky=N+S+E)

    Button(frame,text='Download',command=lambda:downloadChaps(a,comics,listBox.curselection())).grid()

def downloadChaps(a,comics,selection):
    links = []
    for i in selection:
        links.append(comics[i])
    download(a,links)

def download(a,links):
    a.comic_dl(links)
