import os
from shutil import copy2
import logging as log
import click
from rich.progress import Progress
import datetime
import pandas as pd
import pyodbc

# TODO: Rekursion bei der Hierarichie
#       Level einstellbar?
#       upper und trim pfad
#       Wildcard im Pfad
#       copy
#       sftp
#       copy string generieren
#       access abhaken
#       Zuweisung Datei-Kategorie
#       Umbenennung mit Datum

@click.command()
@click.option('-p', '--path', default="", help='Verzeichnis, das durchsucht werden soll. Alles wird ausgegeben. Bsp: -p C:\\test')
@click.option('-e', '--extension', default="", help='Datei-Endung, die gefiltert werden soll. Ordner werden weiterhin mit ausgegeben. Bsp: -e .txt')
@click.option('-ed', '--emptydir', is_flag=True, help='Aktiviere nur die Ausgabe von leeren Verzeichnissen. Bsp: -ed')
@click.option('-o', '--outputpath', default="", help='Ausgabe-Pfad für Ergebnis-Datei festlegen. Bsp: -o C:\\test')
@click.option('-x', '--toexcel', is_flag=True, help='Excel-Datei aus Ausgabe-Format festlegen. Bsp: -o C:\\test -x')
@click.option('-d', '--donefilespath', default="", help='Gibt schon bearbeitete Pfade nicht mehr aus, die in angegebener Liste stehen. Bsp: -d C:\\test\\liste.txt')
@click.option('-ccs', '--createcopyscript', is_flag=True, help='Copy-Script wird beim setzen dieses Flags erzeugt. Bsp: -p C:\\test -o C:\\test -ccs')
@click.option('-c1', '--copystartfolder', default="", help='Pfad der die zu kopierenden Dokumente enthält. Bsp: -c1 C:\\test')
@click.option('-c2', '--copytofolder', default="", help='Pfad in den die Dokumente kopiert werden sollen. Bsp: -c2 C:\\test')
def main(path, extension, emptydir, outputpath, toexcel, donefilespath, createcopyscript, copystartfolder, copytofolder):
    if not path:
        #path = "/Users/superdanyo/Documents/Skripte/test"
        path = os.path.join("C:", os.environ['HOMEPATH'], "Downloads")
    if not outputpath:
        outputpath = path
    if not os.path.exists(path) or not os.path.exists(outputpath):
        print("Ordner nicht gefunden...")
        quit()
    
    # COPYSCRIPT #############
    if(createcopyscript):
        createCopyScript(path, outputpath, createcopyscript)
        quit()
    ####################    
    # COPY #############
    if(copystartfolder):
        copyfilesToCorrektFolder(copystartfolder, copytofolder, extension)
        quit()
    ####################

    log.basicConfig(level=log.INFO)
    listOfFiles = []
    tag = ""
    countElements = 0
    
    print("Scan started...")

    #TODO: Hier Wildcard zusammenbauen
    level1 = folder_objects(path, extension, emptydir)

    listOfFiles.extend(level1)
    # Für Status-Bar, wenn emptydir 1
    countLevel1 = len(level1)
    countElements += countLevel1
    if(countLevel1 == 0):
        countLevel1 = 1

    with Progress() as progress:
        task1 = progress.add_task("[red]Scanning:", total=countLevel1)
        for itemLevel1 in level1:
            level2 = folder_objects(itemLevel1, extension, emptydir)
            listOfFiles.extend(level2)
            progress.update(task1, advance=1)
            #time.sleep(0.1)
            for itemLevel2 in level2:
                level3 = folder_objects(itemLevel2, extension, emptydir)
                listOfFiles.extend(level3)
                for itemLevel3 in level3:
                    level4 = folder_objects(itemLevel3, extension, emptydir)
                    listOfFiles.extend(level4)
                    for itemLevel4 in level4:
                        level5 = folder_objects(itemLevel4, extension, emptydir)
                        listOfFiles.extend(level5)

    # Schon bearbeitete Datei entfernen
    if(donefilespath):
        listOfFiles = deleteDoneFiles(listOfFiles, donefilespath)

    # TAG zuordnen
    if(extension != ""):
        tag = extension
    elif(emptydir):
        tag = "Empty-Dir"
    else:
        tag = "All"

    # Erstellt Ausgabe-Datei
    listOfFiles.sort()
    createOutputFile(outputpath, toexcel, listOfFiles, tag)

def test():
    levelNext = ""
    level = ""
    for i in range(10):
        level = levelNext  
        for itemLevel in level:
            levelNext = folder_objects(itemLevel, extension, emptydir)
            # listOfFiles.extend(levelNext)

def folder_objects(path, extension, emptydir, otype = "all"):
    try:    
        if (os.path.exists(path) == False or
            os.path.isdir(path) == False or
            os.access(path, os.R_OK) == False):
            return []
        else:
            objects = os.listdir(path)
            result = []
            for objectname in objects:
                objectpath = os.path.join(path, objectname)
                if (otype == "all" or
                    (otype == "dir"  and os.path.isdir(objectpath)  == True) or
                    (otype == "file" and os.path.isfile(objectpath) == True)):
                    # Leere Verzeichnisse suchen
                    if(emptydir):
                        if(os.path.isdir(objectpath) and len(os.listdir(objectpath)) == 0):
                            result.append(objectpath)
                    else:
                        # Prüfung Extension-Filter
                        if(os.path.isdir(objectpath) or extension == "" or os.path.splitext(objectpath)[1] == extension):
                            result.append(objectpath)
            return result
    except Exception as e:
        print("")
        print("SKIP-DIR: " + path)
        #log.info("SKIP-DIR: " + path)
        return []

def createOutputFile(outputpath, toexcel, listOfFiles, tag):
    filePath = ""
    dateTime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")
    countElements = len(listOfFiles)
    if(toexcel):
        filePath = os.path.join(outputpath, "Directory-Scan-" + tag + "_" + dateTime + ".csv")
        data = convertListOfFilesToDataFrame(listOfFiles, countElements)
        df = pd.DataFrame(data=data)
        try:
            df.to_csv(filePath, sep=';', index=False, encoding='utf-8-sig')
        except Exception as e:
            print("")
            print("Error during creating file: " + filePath)
    else:        
        filePath = os.path.join(outputpath, "Directory-Scan-" + tag + "_" + dateTime + ".txt")
        with open(filePath, "w", encoding='utf8') as f:
            f.write('\n'.join(listOfFiles)) #.encode('utf8'))

    print("Anzahl: " + str(countElements) + " - Output-File created -> " + filePath)

def deleteDoneFiles(listOfFiles, donefilespath):
    with open(donefilespath, encoding='utf8') as f:
        listOfDoneFiles = f.read().splitlines()
        result = list(set(listOfFiles) - set(listOfDoneFiles))
        #for path in listOfDoneFiles:
        #    if path in listOfFiles:
        #        listOfFiles.remove(path)
        #print(listOfFiles)
        return result
    return []

def convertListOfFilesToDataFrame(listOfFiles, countElements):
    with Progress() as progress:
        task2 = progress.add_task("[green]Convert: ", total=countElements)
        data = []
        for path in listOfFiles:
            progress.update(task2, advance=1)
            splitedPathList = path.split('\\')
            data.append(splitedPathList)
        return data

# CREATE-COPY-SCRIPT ###################################################
def createCopyScript(path, outputpath, createcopyscript):
    print("geht noch nicht... was soll dein copy script nochmal können?")

# COPY #################################################################
def copyfilesToCorrektFolder(copystartfolder, copytofolder, extension):
    log.basicConfig(filename=os.path.join(copystartfolder, 'copy.log'), filemode='w', level=log.INFO)
    if 1==1:
        print("noch nicht fertig... müssen wir nochmal besprechen...")
    else:
        if os.dir.exists(copystartfolder):
            try:
                fromShortcut = os.path.dirname(copystartfolder)[:2]
                toShortcut = os.path.dirname(copystartfolder)[6:8]
            except Exception as e:
                print("Abkürzung im Ordnernamen fehlerhaft...")
                quit()
            filesInDir = os.listdir(copystartfolder)
            for f in filesInDir:
                # finde Artikel Ordner
                # finde korrektes Verzeichnis
                # 
                fileWithExt = os.path.basename(f)
                fileWithoutExt = os.path.splitext(fileWithExt)[0]
                fileExt = os.path.splitext(fileWithExt)[1]
                artikelFolderName = fileWithoutExt.split('_')[0]
                #if(fileExt == extension):
                artikelFolderPath = os.path.join(copytofolder, artikelFolderName)
                if os.dir.exists(artikelFolderPath):
                    newFileName = renameFileShortcut(fileWithExt, fromShortcut, toShortcut)
                    if newFileName:
                        newFilePath = getNewFilePath(artikelFolderPath, newFileName, toShortcut)
                        if os.file.exists(newFilePath):
                            log.warning(newFilePath + " gibts in dem Ordner schon...")
                        else:
                            copy2(f, newFilePath)
                            log.info(f + " kopiert nach " newFilePath)
                    else:
                        print("Abkürzungen nicht freigegeben: " + fromShortcut + " - " + toShortcut)
                else:
                    log.warning(artikelFolderPath + " existiert nicht...")
        else:
            print(copystartfolder + " existiert nicht...")
    
def renameFileShortcut(fileName, fromShortcut, toShortcut):
    whitelist = ['bs','bk','bw']
    if fromShortcut in whitelist and toShortcut in whitelist:
        return fileName = fileWithExt.replace(fromShortcut, toShortcut)
    else:
        return ""

def getNewFilePath(artikelFolderPath, newFileName, toShortcut):
    targetFolder = ""
    if toShortcut == "bs":
        targetFolder = os.path.join(artikelFolderPath, "Bilder").join("Shop")
    elif toShortcut == "bw":
        targetFolder = os.path.join(artikelFolderPath, "Bilder").join("Warenwirtschaft")
    return os.path.join(targetFolder, newFileName)

def connectToAccess(accessFile, user='admin', password = '', old_driver=False):
    driver_ver = '*.mdb'
    if not old_driver:
        driver_ver += ', *.accdb'

    odbc_conn_str = ('DRIVER={Microsoft Access Driver (%s)}'
                     ';DBQ=%s;UID=%s;PWD=%s' %
                     (driver_ver, accessFile, user, password))

    return pyodbc.connect(odbc_conn_str)

def getListAndCheckEntrysInAccess(itemsFile, accessFile):
    folderName = os.path.dirname(accessFile)
    log.basicConfig(filename=os.path.join(folderName, 'access.log'), filemode='w', level=log.INFO)
    with open(itemsFile, encoding='utf8') as f:
        listOfItems = f.read().splitlines()   
        fileName = os.path.basename(itemsFile).split('_')
        columnName = fileName[0]
        checkedContent = fileName[1]
        for itemName in listOfItems:
            try:            
                # TODO: Access vorhanden und zugreifbar?
                conn = connectToAccess(accessFile)  # only absolute paths!
                cursor = conn.cursor()
                cursor.execute('UPDATE artikel SET ' + columnName + ' = ' + checkedContent + WHERE Artikel = "' + itemName + '"')
                conn.commit()
                conn.close()
                log.info("Artikel: " + itemName + " in Spalte: " + columnName + " abgehakt")
            except Exception as e:
                conn.rollback()
                conn.close()
                log.error("Fehler bei Arktiel: " + itemName)

if __name__ == '__main__':
    main()
