import os
from shutil import copy2
#import logging as log
import click
from rich.progress import Progress
import time
import pandas as pd

# TODO: Rekursion bei der Hierarichie
#       Level einstellbar?
#       upper/lower?
#       Wildcard im Pfad
#       copy

@click.command()
@click.option('-p', '--path', default="", help='Verzeichnis, das durchsucht werden soll. Alles wird ausgegeben. Bsp: -p C:\\test')
@click.option('-e', '--extension', default="", help='Datei-Endung, die gefiltert werden soll. Ordner werden weiterhin mit ausgegeben. Bsp: -e .txt')
@click.option('-ed', '--emptydir', is_flag=True, help='Aktiviere nur die Ausgabe von leeren Verzeichnissen. Bsp: -ed')
@click.option('-o', '--outputpath', default="", help='Ausgabe-Pfad für Ergebnis-Datei festlegen. Bsp: -o C:\\test')
@click.option('-x', '--toexcel', is_flag=True, help='Excel-Datei aus Ausgabe-Format festlegen. Bsp: -o C:\\test -x')
@click.option('-c1', '--copystartfolder', default="", help='Pfad der die zu kopierenden Dokumente enthält. Bsp: -c1 C:\\test')
@click.option('-c2', '--copytofolder', default="", help='Pfad in den die Dokumente kopiert werden sollen. Bsp: -c2 C:\\test')
def main(path, extension, emptydir, outputpath, toexcel, copystartfolder, copytofolder):
    # COPY #############
    if(copystartfolder):
        copyfilesToCorrektFolder(copystartfolder, copytofolder)
        quit()
    ####################

    #log.basicConfig(level=log.INFO)
    listOfFiles = []
    tag = ""
    countElements = 0

    if not path:
        #path = "/Users/superdanyo/Documents/Skripte/test"
        path = os.path.join("C:", os.environ['HOMEPATH'], "Downloads")

    if not outputpath:
        outputpath = path

    if not os.path.exists(path) or not os.path.exists(outputpath):
        print("Ordner nicht gefunden...")
        quit()
    
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

def createOutputFile(outputpath, toexcel , listOfFiles, tag):
    filePath = ""
    countElements = len(listOfFiles)
    if(toexcel):
        filePath = os.path.join(outputpath, "Directory-Scan-" + tag + ".csv")
        data = convertListOfFilesToDataFrame(listOfFiles, countElements)
        df = pd.DataFrame(data=data)
        df.to_csv(filePath, sep=';', index=False, encoding ='utf8')
    else:        
        filePath = os.path.join(outputpath, "Directory-Scan-" + tag + ".txt")
        f = open(filePath, "w", encoding='utf8')
        #for i in range(10):
        f.write('\n'.join(listOfFiles)) #.encode('utf8'))
        f.close()

    print("Anzahl: " + str(countElements) + " - Output-File created -> " + filePath)

def convertListOfFilesToDataFrame(listOfFiles, countElements):
    with Progress() as progress:
        task2 = progress.add_task("[green]Convert: ", total=countElements)
        data = []
        for path in listOfFiles:
            progress.update(task2, advance=1)
            splitedPathList = path.split('\\')
            data.append(splitedPathList)
        return data

# COPY #################################################################
def copyfilesToCorrektFolder(copystartfolder, copytofolder):
    if(1==1):
        print("noch nicht fertig")
    else:
        #TODO: Ordner prüfen exists
        filesInDir = os.listdir(copystartfolder)
        for f in filesInDir:
            # finde Artikel Ordner
            # finde korrektes Verzeichnis
            # 
            fileWithExt = os.path.basename(f)
            fileWithoutExt = os.path.splitext(fileWithoutExt)[0]
            fileExt = os.path.splitext(fileWithoutExt)[1]
            if(fileExt == ".pdf"):
                artikelFolder = os.path.join(copytofolder, fileWithExt)
                if(os.dir.exists(artikelFolder)):
                    newFile = os.file.exists(os.path.join(artikelFolder, fileWithExt))
                    if(os.file.exists(newFile)):
                        print(newFile + " gibts in dem Ordner schon...")
                    else:
                        copy2(f, os.path.join(copytofolder, fileWithExt))
                else:
                    print(artikelFolder + " existiert nicht...")

if __name__ == '__main__':
    main()
