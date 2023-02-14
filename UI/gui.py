from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from PyQt6.QtWidgets import *
import PyQt6.QtGui as qtg
from PyQt6 import uic,QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import urllib.parse

class startFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('Dev_tools/UI/start.ui',self)

class chaptersFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('Dev_tools/UI/ChaptersView.ui',self)

class searchFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('Dev_tools/UI/searchResults.ui',self)

class downloadsFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('Dev_tools/UI/download.ui',self)

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    
    def download(self):
        a = self.a
        link = self.link
        a.comic_dl(link,self.progress)
        self.finished.emit()
    
    def lastPage(self):
        self.a.get_last_page(self.a.query)
        self.finished.emit()
    
    def search(self):
        pass



class MainWindow(QMainWindow):
    n = 1
    def __init__(self):
        super(MainWindow,self).__init__()
        uic.loadUi('Dev_tools/UI/stack.ui',self)

        self.startFrame = startFrame()
        self.chaptersFrame = chaptersFrame()
        self.searchFrame = searchFrame()
        self.downloadsFrame = downloadsFrame()

        self.mainStack.addWidget(self.startFrame)
        self.mainStack.addWidget(self.chaptersFrame)
        self.mainStack.addWidget(self.searchFrame)
        self.mainStack.addWidget(self.downloadsFrame)
        self.show()  
    
    def start(self):
        self.startFrame.siteSelector.hide()
        self.startFrame.goButton.clicked.connect(self.go)

    def go(self):
        query = self.startFrame.queryField.text()
        if '.' not in query or '/' not in query:
            self.startFrame.queryField.setDisabled(True)
            self.startFrame.startLabel.setText('Select a website')
            self.startFrame.siteSelector.show()
            self.startFrame.goButton.clicked.connect(lambda:self.search(query))
        else:
            self.parseLink(query)


    def parseLink(self,query):
        if 'comicextra' in query:
            self.a = comicextra(query)
        elif 'comiconlinefree' in query:
            self.a = comiconline(query)
        elif 'readcomiconline' in query:
            self.a = readcomiconline(query)
        
        if self.a.is_chap_list(query):
            self.listChapters(query)
        else:

            pBar = self.addPBar('name')
            pBar.setValue(0)
            self.mainStack.setCurrentIndex(3)
        
            self.createThread(1)
            self.worker.a = self.a
            self.worker.link = query
            self.thread.started.connect(self.worker.download)
            self.worker.progress.connect(lambda a:pBar.setValue(a))
            self.thread.start()


    def createThread(self,n):
        print(f'Thread {n} created')
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.delete)
    
    def delete(self):
        print('Thread Deleted')
        self.thread.deleteLater()


    def listChapters(self,link,back=False,x=None):
        print('Test')
        self.mainStack.setCurrentIndex(1)
        a = self.a
        if back == False:
            self.chaptersFrame.backButton.setDisabled(True)
            self.chaptersFrame.backButton.hide()
        else:
            self.chaptersFrame.backButton.clicked.connect(lambda:self.mainStack.setCurrentIndex(2))

        name,chapters,titles = a.get_chaps(link)
        self.chaptersFrame.coverImageLabel.setPixmap(qtg.QPixmap("downloads/temp/cover.jpg").scaled(self.chaptersFrame.coverImageLabel.size(),QtCore.Qt.AspectRatioMode.KeepAspectRatio,QtCore.Qt.TransformationMode.SmoothTransformation))
        self.chaptersFrame.comicNameLabel.setText(urllib.parse.unquote(name))

        font = qtg.QFont()
        font.setPointSize(12)
        self.chaptersFrame.chapterList.setFont(font)
        if self.n == 1:
            self.chaptersFrame.downChapButton.clicked.connect(self.test)
        if self.n == 2:
            self.chaptersFrame.downChapButton.clicked.connect(self.test2)
        self.n += 1
        for i in range(len(titles)):
            item = QListWidgetItem()
            item.setText(titles[i])
            item.setData(3,chapters[i])
            self.chaptersFrame.chapterList.addItem(item)
        
    
    def test(self,a):
        print('Test Hello')
    def test2(self,a):
        print('Test Hello 2')
    
    def selectedChapters(self):
        
        titles = [i.text() for i in self.chaptersFrame.chapterList.selectedItems()]
        links = [i.data(3) for i in self.chaptersFrame.chapterList.selectedItems()]
        self.mainStack.setCurrentIndex(3)
        self.downloadChaps(links,titles,0)
    
    def downloadChaps(self,links,titles,n):
        pBar = self.addPBar(titles[n])
        self.createThread(2)
        self.worker.a = self.a
        self.worker.link = links[n]
        self.thread.started.connect(self.worker.download)
        self.worker.progress.connect(lambda a:pBar.setValue(a))
        if n < len(links)-1:
            self.thread.finished.connect(lambda:self.downloadChaps(links,titles,n+1))
        self.thread.start()

        
    def addPBar(self,name):
        horizontalLayout = QHBoxLayout()
        label = QLabel(parent=self.downloadsFrame.scrollAreaWidgetContents)
        label.setObjectName(name)
        label.setMinimumSize(QtCore.QSize(200, 25))
        label.setMaximumSize(QtCore.QSize(16777215, 25))
        label.setText(name)
        label.setWordWrap(True)
        horizontalLayout.addWidget(label)
        progressBar = QProgressBar(parent=self.downloadsFrame.scrollAreaWidgetContents,value=0)
        progressBar.setMinimumSize(QtCore.QSize(0, 25))
        progressBar.setMaximumSize(QtCore.QSize(16777215, 25))
        horizontalLayout.addWidget(progressBar)
        self.downloadsFrame.verticalLayout.addLayout(horizontalLayout)
        return progressBar


    def search(self,query):
        site = self.startFrame.siteSelector.currentIndex()
        if site == 0:
            self.a = readcomiconline(query)
        elif site == 1:
            self.a = comicextra(query)
        elif site == 2:
            self.a = comiconline(query)
        self.listResults(1)
        
    
    def listResults(self,page):
        try:
            for i in self.navButtons:
                self.searchFrame.horizontalLayout_2.removeWidget(i)
        except AttributeError:
            pass
        
        font = qtg.QFont()
        font.setPointSize(12)
        self.searchFrame.resultsList.setFont(font)
        self.navButtons = []
        self.createThread(4)
        self.worker.a = self.a
        self.thread.started.connect(self.worker.lastPage)
        self.thread.finished.connect(lambda:self.showPage(1))
        self.thread.start()
            

    def showPage(self,page):
        """if self.a.lPage == 0:
            QtCore.QCoreApplication.instance().quit()"""
        self.mainStack.setCurrentIndex(2)
        self.searchFrame.resultsList.clear()
        lPage = self.a.lPage
        minPage = page-2 if (page-2)>0 else 1
        maxPage = minPage+4 if minPage+4<=lPage else lPage
        
        for i in self.navButtons:
            self.searchFrame.horizontalLayout_2.removeWidget(i)
        
        self.navButtons = []
        
        navButton = QPushButton(parent = self.searchFrame.navBar)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.setText('<<')
        if page==1:
            navButton.setDisabled(True)
        navButton.clicked.connect(lambda :self.showPage(1))
        self.navButtons.append(navButton)
        self.searchFrame.horizontalLayout_2.addWidget(navButton)
        
        for i in range(minPage,maxPage+1):
            
            navButton = QPushButton(parent = self.searchFrame.navBar)
            
            navButton.setMinimumSize(QtCore.QSize(30,30))
            navButton.setMaximumSize(QtCore.QSize(30,30))
            navButton.setText(str(i))
            if i==page:
                navButton.setDisabled(True)
            self.searchFrame.horizontalLayout_2.addWidget(navButton)
            self.navButtons.append(navButton)
            navButton.clicked.connect(lambda state ,m = i:self.showPage(m))
        
        navButton = QPushButton(parent = self.searchFrame.navBar)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.setText('>>')
        navButton.clicked.connect(lambda :self.showPage(lPage))
        if page==lPage:
            navButton.setDisabled(True)
        self.searchFrame.horizontalLayout_2.addWidget(navButton)
        self.navButtons.append(navButton)

        if page not in self.a.searchResults.keys():
            self.a.get_search_titles(page)

        

        for n,comic in enumerate(self.a.searchResults[page]):
            if page not in self.a.imagePages:
                self.a.imagePages[page]=[]
            
            if n not in self.a.imagePages[page]:
                #elf.a.img_download(comic[2],f'{page}_{n}','downloads/temp/')
                self.a.imagePages[page].append(n)
            item = QListWidgetItem()
            icon = qtg.QIcon()
            icon.addPixmap(qtg.QPixmap(f"downloads/temp/{page}_{n}.jpg"), qtg.QIcon.Mode.Active, qtg.QIcon.State.On)
            item.setIcon(icon)
            size = QtCore.QSize(100,100)
            self.searchFrame.resultsList.setIconSize(size)
            item.setText(comic[1])
            item.setData(3,comic[0])
            self.searchFrame.resultsList.addItem(item)

        self.searchFrame.resultsList.itemClicked.connect(self.comicSelected)

    def comicSelected(self,clickedItem):
        self.listChapters(clickedItem.data(3),back=True)
