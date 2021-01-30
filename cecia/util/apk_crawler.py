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
    """
    this function does a search on Apkpure and find the first n application of the given category
    :param size: maximum size of the app
    :param n: number of applications to find
    :param topic: ctegory of the application
    :return:
    """
    app_set = set() 
    session = requests.Session()
    x=1
    while  len(app_set) < n:
        print len(app_set),n
        category_link = 'https://apkpure.com/it/'+topic+'?page='+str(x)
        r = session.get(category_link)
        soup = BeautifulSoup(r.content, 'html.parser')
        tot_app = soup.find_all("a",{"rel":"nofollow","class":""},href=re.compile("download\?from"))
        if len(tot_app) == 0: break
        for app_finder in tot_app:
            r = session.get('https://apkpure.com'+app_finder['href'])
            soup_size = BeautifulSoup(r.content, 'html.parser')
            size_APK = soup_size.find("span",{"class":"fsize"})
            if size_APK == None: continue
            misure = size_APK.text[-3:-1]
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
            if len(app_set) >= n:
                break
        x+=1
    return app_set
            
        

        

def Popular_app(source_path):
    """
    :param source_path: source_path
    :return: the set of the most popular app.
    """
    app_set = set()
    path = source_path
    f=codecs.open(path, 'r')
    soup = BeautifulSoup(f.read(), 'html.parser')
    c = soup.find_all("a",{"class":"child-submenu-link"})
    for sub in c:
        sub_link = sub['href']
        if sub_link != '/store/apps/category/FAMILY?age=AGE_RANGE1'\
                and sub_link != '/store/apps/category/FAMILY?age=AGE_RANGE2' \
                and sub_link != '/store/apps/category/FAMILY?age=AGE_RANGE3':
            link = 'https://play.google.com'+sub_link+'/collection/topselling_free?hl=en'
            f = urllib.urlopen(link)
            soup2 = BeautifulSoup(f.read(), 'html.parser')
            targets = soup2.findAll("a",{"class":"title"})
            for target in targets:
                app_name = target.contents[0].encode("utf-8")
                serial_number = int(app_name.split('.')[0])
                if serial_number <= 30:
                    id_app = target['href'].split('?')[1][3:]
                    app_set.add(id_app)
    return app_set

def export_idapp_to_file():
    """
    export the most 30 popular app of each category in a json file
    :return: None
    """
    apps = Popular_app()
    with open('appList.json','w') as fp:    
        json.dump(list(apps),fp)


def download_from_apkpure(app_list, save_path):
    """
    given a list of id of apps, for each id donwload the corrispective app on Apkpure and store in save_path
    :param app_list: list of id
    :param save_path: path when store the app
    :return: None
    """

    for app in app_list:
        print app
        search_link = 'https://apkpure.com/it/search?q='+app
        session = requests.Session()
        r = session.get(search_link)
        soup = BeautifulSoup(r.content, 'html.parser')
        first = soup.find("dl",{"class":"search-dl"})
        if first != None:
            second = first.find('a')
            r = session.get('https://apkpure.com'+second['href'])
            soup2 = BeautifulSoup(r.content, 'html.parser')
            check = soup2.find("div",{"class":"main page-q","data-type":"pkg"})
            if check != None:
                if check['data-pkg'] == app:
                    dt = soup2.find("a",{"class":" da"})
                    if dt != None:
                        if "Scarica XAPK" in dt.text:
                            dt = soup2.find("a",href=re.compile("download(.*?)-APK\?"))
                        if dt != None:
                            link='https://apkpure.com'+dt['href']
                            r = session.get(link)
                            soup3 = BeautifulSoup(r.content, 'html.parser')
                            first = soup3.find("a",{"id":"download_link"})
                            if first != None:
                                print first['href']
                                r = session.get(first['href'])
                                if(len(r.content)) > 170:
                                    path= save_path+app+'.apk'
                                    with open(path, 'wb') as local_file:
                                            local_file.write(r.content)