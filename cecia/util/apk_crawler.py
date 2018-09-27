''' 
  / _ \
\_\(_)/_/
 _//"\\_  
  /   \
 '''
import numpy as np
from bs4 import BeautifulSoup
import urllib
import codecs
import json 
import requests
import os
import re

''' questa funzione effettua una ricerca su Apkpure e ritorna un insieme con il nome delle prime 'n' applicazioni trovate con dimensione <= 'size' ( in MB)
della categoria 'topic'
'''
def search_by_size(size,n,topic):
    app_set = set() 
    session = requests.Session()
    x=1 # contatore di pagine
    while  len(app_set) < n: # finche' non trovo n elementi
        print len(app_set),n
        category_link = 'https://apkpure.com/it/'+topic+'?page='+str(x) # ottengo la pagina in analisi
        r = session.get(category_link)
        soup = BeautifulSoup(r.content, 'html.parser')
        tot_app = soup.find_all("a",{"rel":"nofollow","class":""},href=re.compile("download\?from"))
        if len(tot_app) == 0: break # se sono finite le pagine (brutta cosa)
        for app_finder in tot_app:
            r = session.get('https://apkpure.com'+app_finder['href']) #link della pagina del download
            soup_size = BeautifulSoup(r.content, 'html.parser')
            size_APK = soup_size.find("span",{"class":"fsize"})
            if size_APK == None: continue # brutta cosa
            misure = size_APK.text[-3:-1] # MB o KB
            number = float(size_APK.text[1:-3])
            if misure == "KB":
                print 'KB file trovato'
                number = number/1000
            if misure == "GB":
                number = number*1000
            print number
            if number <= size:
                nome_finder= soup_size.find("div",{"class":"main page-q","data-type":"pkg"})
                nome_app = nome_finder['data-pkg']
                print nome_app
                app_set.add(nome_app)
            if len(app_set) >= n: # sto per fare  una cosa molto brutta
                break # fatta
        x+=1
    #print len(app_set) , n
    return app_set
            
        

        

''' ritorna un insieme con gli id delle 30 app piu popolari su play store di ogni categoria'''
def Popular_app():
    app_set = set()
    path= r'C:\Users\barfo\Desktop\prog\utili\parseHTML\playstore_home_en.html'
    f=codecs.open(path, 'r')
    soup = BeautifulSoup(f.read(), 'html.parser')
    c = soup.find_all("a",{"class":"child-submenu-link"})
    for sub in c:
        sub_link = sub['href']
        if sub_link != '/store/apps/category/FAMILY?age=AGE_RANGE1' and sub_link != '/store/apps/category/FAMILY?age=AGE_RANGE2' and sub_link != '/store/apps/category/FAMILY?age=AGE_RANGE3' :
            #print sub_link.split('/')[4] # stampo la categoria
            link = 'https://play.google.com'+sub_link+'/collection/topselling_free?hl=en'
            f = urllib.urlopen(link)
            soup2 = BeautifulSoup(f.read(), 'html.parser')
            targets = soup2.findAll("a",{"class":"title"})
            for target in targets:
                app_name = target.contents[0].encode("utf-8") ## nome app
                serial_number = int(app_name.split('.')[0]) # numero dell'app
                if serial_number <= 30: # se il numero dell'app e' <=30
                    #print app_name # la stampo
                    id_app = target['href'].split('?')[1][3:] # recupero l' id dell' app dal link
                    app_set.add(id_app) # aggiungo l'app al set
    return app_set

''' esporta le 30 app piu popolari di ogni categoria in un file json '''
def export_idapp_to_file():
    apps = Popular_app()
    with open('appList.json','w') as fp:    
        json.dump(list(apps),fp)


''' data una lista di (id di)app in input questa funzione scarica dal sito Apkpure ogni app presente nella lista'''
def download_from_apkpure(app_list):
    for app in app_list:
        print app
        search_link = 'https://apkpure.com/it/search?q='+app
        session = requests.Session()
        r = session.get(search_link)
        soup = BeautifulSoup(r.content, 'html.parser')
        first = soup.find("dl",{"class":"search-dl"})
        if first != None: # prendo il primo risultato della ricerca
            second = first.find('a') # link dell' app
            r = session.get('https://apkpure.com'+second['href']) # accedo al link dell app
            soup2 = BeautifulSoup(r.content, 'html.parser')
            check = soup2.find("div",{"class":"main page-q","data-type":"pkg"})
            if check != None:
                if check['data-pkg'] == app: # se l'app e' effettivamente quella che cerco
                    dt = soup2.find("a",{"class":" da"}) #provo ad ottenere un link per la pagina del download
                    if dt != None: # se esiste il link per la pagina del download
                        if "Scarica XAPK" in dt.text: # se e' un link di un xapk ( che non vogliamo )
                            dt = soup2.find("a",href=re.compile("download(.*?)-APK\?")) # cerco un link secondario situato piu in basso
                        if dt != None: # se e' presente almeno un link apk
                            link='https://apkpure.com'+dt['href'] # scarico l'app
                            r = session.get(link)
                            soup3 = BeautifulSoup(r.content, 'html.parser')
                            first = soup3.find("a",{"id":"download_link"})
                            if first != None: # se e' presente il link del download
                                print first['href']
                                r = session.get(first['href'])
                                if(len(r.content)) > 170:  # se e' 170 e' un bad gateway ( not found )
                                    path= r'C:\Users\barfo\Desktop\apktool\benevole\\'+app+'.apk'
                                    with open(path, 'wb') as local_file:
                                            local_file.write(r.content)