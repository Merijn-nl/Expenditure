##################################
# 
#  Financial insights script v0.2
#   in Python 3
#
#  Reads data from ING CSV files
#  Assigns them a category
#  And aggregates the amounts 
#  
#  Merijn de Haen
#  July - August 2016
#
#  TODO:
#  * Get script to be smart about dates -- detect when a month has ended and a new one has begun and start the aggregation process anew
#  * Get a file selection dialogue for new financial files
#  * Get script to recognize the 'usual suspects' by string fragment
# 
##################################

import sys
import os
import re 
from Tkinter import *
import datetime
import json

dir = os.path.dirname(__file__)

finCategories = []
finLibraryArray = []
fileContents = []
dialogResult = ""
JSON_index = 0

def readCategoriesFile():                                 # load categories
    fileName = os.path.join(dir, 'display/app/files/categories.txt')
    with open(fileName , "r") as categoriesRead:
        finCategories = categoriesRead.read().splitlines()
        
    return finCategories

    
def readLibraryFile():                                    # load library
    fileName = os.path.join(dir, 'display/app/files/library.txt')
    with open(fileName , "r") as libraryRead:
        finLibrary = libraryRead.readlines()
            
    finLibraryArray = [i.split(',' , 1) for i in finLibrary]
    
    for x in range(0 , len(finLibraryArray)):            # combine library and categories
    
        catIndex = int(finLibraryArray[x][1])
        catName = finCategories[catIndex]
        finLibraryArray[x][1] = catName    
        
    return finLibraryArray


def appendLibraryFile(newPost , newCategory):
    newCategoryIndex = 6
    for xxx in range(0 , len(finCategories)):
        if all(s in finCategories[xxx] for s in newCategory):
            newCategoryIndex = xxx
            break

#     print(newCategoryIndex , newPost)
    
    fileName = os.path.join(dir, 'display/app/files/library.txt')

    with open(fileName , "a") as libraryAppend:
        libraryAppend.write(newPost)
        libraryAppend.write(",")
        libraryAppend.write(str(newCategoryIndex))
        libraryAppend.write("\n")
        libraryAppend.close

    return    


# load financial file (prompt filename) & save contents to array                                                                                                            
# ToDo: write file selection dialog
def openFinancialFile(file):
    with open(file , "r") as f:
        fileContents = f.readlines()
        
    fileContents.pop(0)
    
    return fileContents


def openHistoryFile():                                    # load history file                                    
    fileName = os.path.join(dir, 'display/app/data/history_json.json')
    with open(fileName , "r") as f:
        fileContents = f.read()
        
    return fileContents


def appendHistoryFile(catValues):                    # append history file
    monthData = {}
    monthData["index"] = JSON_index
    monthData["maand"] = fileContents[0][0]
    monthData.update(catValues)

    monthData = json.dumps(monthData, ensure_ascii=False)
    monthData = re.sub(r'\.0' , '' , monthData)
    
    oldData = openHistoryFile();
    oldData = re.sub(r'[\[\]]' , '' , oldData)
        
    fileName = os.path.join(dir, 'display/app/data/history_json.json')
    with open(fileName , "w") as historyAppend:
        historyAppend.write("[")
        if oldData:
           historyAppend.write(oldData)
           historyAppend.write(",")
        historyAppend.write(monthData)
        historyAppend.write("]")

    return


def cleanArray(array):                                    # do some cleaning on the financial file
    result = array.split(',')
    for x in range(2,5):
        result.pop(2)
    for x in range(5,6):
        result.pop(5)
    for x in range(3,5):
        result[x] = re.sub(r'^"|"$', '', result[x])
    result[3] = round((float(int(result[3])) + float(int(result[4])) / 100) , 2)
    result.pop(4)

    return result


def newLibraryDialog(finData):                    # opens a dialog to categorize unknown post

    def select():
        global dialogResult
        dialogResult = dialogVariable.get()
        root.destroy()
        
    def skip():
        global dialogResult
        dialogResult = categoryChoices[6]
        root.destroy()

    root = Tk()
    
    # use width x height + x_offset + y_offset (no spaces!)
    root.geometry("%dx%d+%d+%d" % (400, 100, 500, 500))
    root.title("%s %s %s categoriseren?" % (finData[1] , finData[2] , finData[3]))

    dialogVariable = StringVar(root)
    
    categoryChoices = finCategories

    dialogVariable.set(categoryChoices[3])

    option = OptionMenu(root , dialogVariable , *categoryChoices)
    option.pack(side = 'top' , padx = 10 , pady = 10)

    buttonSkip = Button(root , text = "Overslaan" , default = "active" , command = skip)
    buttonSkip.pack(side = 'left' , padx = 10 , pady = 10)

    buttonSelect = Button(root , text = "Selecteren" , command = select)
    buttonSelect.pack(side = 'right' , padx = 10 , pady = 10)

    root.mainloop()

    return dialogResult


# parses posts into categories
def parseCategory(finData):
    fileEntryPost = re.sub(r'^"|"$', '', finData[1])

    global finLibraryArray
    lengthArray = len(finLibraryArray)    
    setCategory = 0
    
    # test whether post is known        
    for x in range(0 , lengthArray):    
#         if all(s in finLibraryArray[x][0] for s in fileEntryPost):
        if (fileEntryPost == finLibraryArray[x][0]):
            setCategory = finLibraryArray[x][1]            
            print(fileEntryPost , setCategory)
            return setCategory
            break

    # populate and show dialog box w skip option
    newLibraryItem = newLibraryDialog(finData)
    
    # save new library item to library.txt
    appendLibraryFile(fileEntryPost , newLibraryItem)    
    finLibraryArray = readLibraryFile()                 # refresh library
    
    # return category name to main loop
    return newLibraryItem                


def parseDates(d):
    d = re.sub(r'^"|"$', '', d)
    d = re.sub(r'^\'|\'$', '', d)
    dateYear = int(d[0:4])
    dateMonth = int(d[4:6])
    dateDay = int(d[6:8])

    dateParsed = datetime.date(dateYear,dateMonth,dateDay)
    dateParsed = dateParsed.strftime('%b-%y')
#     print(dateParsed)
    return dateParsed

    
def createCleanFile():
    catValues = {}    
    for x in fileContents:

        # Check for empty category and set to 0
        if (x[4] not in catValues):
            catValues[x[4]] = 0

        # Check for occasional return payments and properly handle them
        if (x[2] == '"Bij"' and x[4] != 'bij'):
            catValues[x[4]] -= round(x[3])

        # Add new post's amount to relevant category
        else:             
            catValues[x[4]] += round(x[3])
    
    # write generic uitgaven category
    if 'bij' not in catValues.keys():
        inkomsten = 0
    else:
        inkomsten = catValues['bij']
    uitgaven = 0
    uit = catValues.values()
    for b in range(0 , len(uit)):
        uitgaven += uit[b]            
    uitgaven -= inkomsten
    resultaat = inkomsten - uitgaven
    
    catValues['uitgaven'] = int(uitgaven)
    catValues['resultaat'] = int(resultaat)
    
    # loop through the categories file to identify missing categories and save them to the array
    for x in finCategories:
        if x not in catValues.keys():
            catValues[x] = 0
    
    # save it all to disk
    appendHistoryFile(catValues)
    
    return


# ----------------------------------
# main script loop
# ----------------------------------

# open files
finCategories = readCategoriesFile()
finLibraryArray = readLibraryFile()

# load list of files in folder input - SHOULD BE 'input'
listdir = dir + '/input/'
files = os.listdir(listdir)
print(files)

JSON_index = openHistoryFile()
JSON_index = JSON_index.count('{')

# print("Index: %" % JSON_index)

# loop through financial files to open
for a in range(1 , len(files)):
    JSON_index += 1
    targetFile = listdir + files[a]
    print(targetFile)
    fileContents = openFinancialFile(targetFile)

    # loop through cleaning each financial file, clean the dates and assign each post a category
    numLines = len(fileContents)
    for x in range(0 , numLines):
        fileContents[x] = cleanArray(fileContents[x])        
        fileContents[x][0] = parseDates(fileContents[x][0])
        fileContents[x][4] = parseCategory(fileContents[x])

    # do the aggregating per category and append data to history file
    createCleanFile()