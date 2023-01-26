from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from datetime import datetime
import os

start = datetime.now()
if not os.path.exists('./downloads'):
    os.mkdir('downloads')
with open('log.txt','a') as log:
    log.write(str(datetime.now())+'\n')

print("1)comicextra.com \n2)comiconlinefree.net\n3)readcomiconline.li")
query = input('Select website to search or enter comic link: ')
if 'comicextra' in query or query == '1':
    a = comicextra(query)
    pass
elif 'comiconlinefree' in query or query == '2':
    a = comiconline(query)
elif 'readcomiconline' in query or query == '3':
    a = readcomiconline(query)

print(datetime.now()-start)