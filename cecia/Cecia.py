import re
import os
import fnmatch
import json
import subprocess
import csv
import pandas as pd
import sys
from pyfiglet import Figlet
import pickle
import shutil
import time
f = Figlet(font='slant')
bigName = f.renderText('Cecia')
usage = bigName+'\n A tool for static analysis on Android ransomware, Copyright (c) Francesco Fornasieri \n version:1.0 \n \n Usage: Cecia.py [APK-FILE-NAME]'

''' Questa casse permette di effettuare parsing di 1 file apk decompilato con apktool - fase di FeatureExtraction'''
class SmaliParser(object):
    def __init__(self, file):
        """
        :param file: directory del file da analizzare
        """
        with open('appdict.json', 'r') as fp:
            self.allCall = json.load(fp)
        with open (r'C:\Users\barfo\Desktop\prog\cecia\tabella.csv') as csvfile:
            csv_reader = csv.reader(csvfile)
            self.csv_colonne = next(csv_reader)
        self.pattern_method_data = re.compile(ur'^\.method.+?\ (.+?(?=\())\((.*?)\)(.*?$)(.*?(?=\.end\ method))', re.MULTILINE | re.DOTALL)
        self.pattern_called_methods = re.compile(ur'invoke-.*?\ {(.*?)}, (.+?(?=;))\;\-\>(.+?(?=\())\((.*?)\)(.*?)(?=$|;)', re.MULTILINE | re.DOTALL)
        self.pattern_move_result = re.compile(ur'move-result.+?(.*?)$', re.MULTILINE | re.DOTALL)
        self.pattern_class_name = re.compile(ur'^\.class.*\ (.+(?=\;))', re.MULTILINE)
        self.file = file
   
    def get_class_name(self, content):
        """
        gets the class name of a single smali file content
        :param content: contenuto del file smali
        :return: nome della classe
        """
        data = re.findall(self.pattern_class_name, content)
        return data[0]

    def get_methods(self, content):
        """
        prende tutti i metodi in un file smali
        :param content: contenuto del file smali
        :rtype: list of lists
        :return: [0] - nome del metodo
                 [1] - parametri del metodo
                 [2] - valore di ritorno del metodo
                 [3] - dati del metdo
        """
        data = re.findall(self.pattern_method_data, content)
        return data

    def get_called_methods(self, content):
        """
        gets all the method called inside a smali method data. works just fine with a single smali line
        :param content: content of the smali data to be parsed
        :rtype: list of lists
        :return: [0] - called method parameters
                 [1] - called method object type
                 [2] - called method name
                 [3] - called method parameters object type
                 [4] - called method return object type
        """
        data = re.findall(self.pattern_called_methods, content)
        return data
    
                    
    
    def countCallFilesRec(self):
        for root, dirnames, filenames in os.walk(self.file):
            for filename in fnmatch.filter(filenames, '*.smali'):
                filepath = os.path.join(root, filename)
                try: # in caso ci siano bad path
                    with open(filepath, 'r') as smali_file:
                        content = smali_file.read()
                        self.countCallFile(content)
                except (IOError ,IndexError) as e:
                    print str(e)
                    return -1 # errore
        self.aggiornaCSV()
        return 0

    
 
    def countCallFile(self, content):
        class_name = self.get_class_name(content=content)
        methods = self.get_methods(content=content)
        # add methods to db
        for method in methods:
            method_data = method[3]
            called_methods = self.get_called_methods(content=method_data)
            for called_method in called_methods:
                self.updateDict(called_method[1]) # aggiorno il dizionario(eventualmente)
                    
               
    def updateDict(self,package):
        package = package.replace("/",".") 
        package = package[1:] #levo il primo carttere, ovvero 'L' 
        #print package
        if package in self.allCall and package != "type":
            self.allCall[package] += 1
    
    def aggiornaCSV(self):
        newline=[]
        for col in self.csv_colonne:
            newline.append(self.allCall[col]) # costruisco la successiva riga
        with open(r'C:\Users\barfo\Desktop\prog\cecia\tabella.csv','a') as fd:
            wr = csv.writer(fd)
            wr.writerow(newline)

def decompile_apk(path):
    devnull = open(os.devnull, 'wb') 
    bashCommand= 'apktool d '+path
    process = subprocess.Popen(bashCommand, shell=True,stdout=devnull,stderr = devnull)
    output, error = process.communicate()

def predict_result(diz):

    data = pd.read_csv(r'C:\Users\barfo\Desktop\prog\cecia\tabella.csv') #estraggo la colonna nomi con pandas
    model_path = os.getcwd()+'\\classificator.sav' # path del classificatore
    loaded_model = pickle.load(open(model_path, 'rb')) # lo carico
    predicted = loaded_model.predict(data.values)
    print predicted
    return predicted
            
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print usage
    else:
        decompile_apk(sys.argv[1])
        nameDir = os.path.basename(sys.argv[1])[:-4]
        fullPathDir = os.getcwd()+'\\'+nameDir
        data = SmaliParser(fullPathDir)
        data.countCallFilesRec()
        result = predict_result(data.allCall)
        if result == 0:
            print "Trusted file"
        else: print "Ransomware!"
        while os.path.exists(fullPathDir):
            shutil.rmtree(fullPathDir,ignore_errors=True)
        os.remove(r'C:\Users\barfo\Desktop\prog\cecia\tabella.csv')
        with open(r'C:\Users\barfo\Desktop\prog\cecia\tabella.csv','a') as fd:
            wr = csv.writer(fd)
            wr.writerow(data.csv_colonne)
        
    
