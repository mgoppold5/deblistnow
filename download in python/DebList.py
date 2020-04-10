#
# Copyright (c) 2020 Mike Goppold von Lobsdorf
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

#
# This is a program with commands to handle file lists,
# for debian repositories.
#
# Once it has a list of new update files,
# it can download them.
# The downloaded files are not crypto checked,
# but are mostly good enough to be imported,
# by the popular jigdo tool.
#

import os
import sys

QUOTE = "\""
NEWLINE = "\n"

#
# General string related functions
#

class CompareResult:
	def __init__(self):
		self.less = False
		self.greater = False
	
def strRange(theStr, start, theLen):
	i = 0
	s = ""
	while(i < theLen):
		s += theStr[start + i]
		i += 1
	return s

def getSepListLength(path, sep):
	commaCount = 0
	i = 0
	strLen = len(path)
	while(i < strLen):
		if(path[i] == sep):
			commaCount += 1
		i += 1
	return commaCount

def getSepListItem(path, itemIndex, sep):
	commaCount = 0
	i = 0
	startIndex = 0
	pastIndex = 0
	strLen = len(path)
	while(i < strLen):
		if(path[i] == sep):
			commaCount += 1

			if(commaCount == itemIndex):
				startIndex = i + 1
			if(commaCount == itemIndex + 1):
				pastIndex = i
		i += 1

	commaCount += 1

	if(commaCount == itemIndex):
		startIndex = i + 1
	if(commaCount == itemIndex + 1):
		pastIndex = i

	if(startIndex > pastIndex): return None
	return strRange(path, startIndex, pastIndex - startIndex)

def compareStrings(compRes, str1, str2):
	compRes.less = False
	compRes.greater = False
	
	len3 = len(str1)
	if(len(str2) < len3): len3 = len(str2)
	
	i = 0
	while(i < len3):
		if(str1[i] < str2[i]):
			compRes.less = True
			return

		if(str1[i] > str2[i]):
			compRes.greater = True
			return
		
		i += 1
	
	if(len(str1) < len(str2)):
		compRes.less = True
		return

	if(len(str1) > len(str2)):
		compRes.greater = True
		return
		
	return

def compareStrings2(compRes, str1, str2):
	compareStrings(compRes, str1, str2)
	myStr = "cmp"
	if(compRes.less): myStr += "less"
	if(compRes.greater): myStr += "greater"
	print(str1 + "," + str2 + "," + myStr + ",")

#
# General helper functions
#

def printRaw(theStr):
	s2 = str(theStr)
	sys.stdout.write(s2)
	sys.stdout.flush()

#
# General directory helper functions
#
	
def pathCombine(path1, path2, sep):
	if(path1 == None): return path2
	if(path2 == None): return path1
	return path1 + sep + path2

def pathCombine2(path1, path2):
	return pathCombine(path1, path2, "/")

def dirExists(path1):
	r = (os.path.isdir(path1) and not os.path.islink(path1))
	return r

def dirExists2(path1):
	return os.path.isdir(path1)

def fileExists(path1):
	return os.path.isfile(path1)

def makeDirs(path1):
	if(dirExists2(path1)):
		return
	os.makedirs(path1)
	return

#
# RepoFileSpec list functions
#

class RepoFileSpec:
	def __init__(self):
		self.fileName = None
		self.theDir = None
		self.fileNameMinusPath = None

	def calc(self):
		if(self.fileName == None):
			self.theDir = None
			self.fileNameMinusPath = None
			return
		
		j = 0
		lastSlashIndex = 0
		while(j < len(self.fileName)):
			c = self.fileName[j]

			if(c == '/' or c == '\\'):
				lastSlashIndex = j
			
			j += 1
			
		if(lastSlashIndex == 0):
			raise Exception("file name invalid: " + self.fileName)

		if(lastSlashIndex + 1 >= len(self.fileName)):
			raise Exception("file name invalid: " + self.fileName)
		
		self.theDir = self.fileName[0:lastSlashIndex]
		self.fileNameMinusPath = self.fileName[(lastSlashIndex + 1):]

		return

def sortListSwapAt(myList, i):
	temp = myList[i + 1]
	myList[i + 1] = myList[i]
	myList[i] = temp

def sortList(myList):
	# On a list of 50000, this takes 5 hours
	
	myComp = CompareResult()
	
	while(True):
		didSwap = False
		
		i = 0
		while(i < len(myList)):
			if(i + 1 >= len(myList)): break
			
			compareStrings(myComp,
				myList[i].theDir,
				myList[i + 1].theDir)

			if(not myComp.less and not myComp.greater):
				compareStrings(myComp,
					myList[i].fileNameMinusPath,
					myList[i + 1].fileNameMinusPath)
			
			if(myComp.greater):
				sortListSwapAt(myList, i)
				didSwap = True
				
			if(not myComp.less and not myComp.greater):
				#spec = myList[i]
				#print("removing duplicate: " + spec.theDir + "," + spec.fileNameMinusPath)
				del myList[i]
				continue
			
			i += 1
		
		if(not didSwap): break
	
		#print("doing again")
		continue
	return

def sortList2(myList):
	# On a list of 50000, this takes 15 seconds

	myComp = CompareResult()
	myList2 = []
	
	print("Sorting list...")
	
	
	myLen = len(myList)

	if(myLen == 0):
		print()
		return myList2
	
	i = 0
	lastProgress100 = 0
	while(i < myLen):
		progress100 = int(i * 100 / myLen)
		if(lastProgress100 + 2 < progress100):
			printRaw(" " + str(progress100) + "%")
			lastProgress100 = progress100
		
		spec = myList[i]
		
		insertMax = len(myList2)
		insertMin = 0
		
		while(True):
			inBetween = int((insertMax + insertMin) / 2)
			
			if(insertMin == insertMax):
				myList2.insert(inBetween, spec)
				break

			if(inBetween >= len(myList2)):
				myList2.insert(inBetween, spec)
				break
			
			compareStrings(myComp,
				spec.theDir,
				myList2[inBetween].theDir)
			
			if(not myComp.less and not myComp.greater):
				compareStrings(myComp,
					spec.fileNameMinusPath,
					myList2[inBetween].fileNameMinusPath)
				
			if(myComp.greater):
				insertMin = inBetween + 1
				continue
			
			if(myComp.less):
				insertMax = inBetween
				continue
			
			# remove duplicate from final list
			#print("removing duplicate: " + spec.theDir + "," + spec.fileNameMinusPath)
			break
		
		i += 1
		#print("doing again")
		continue
	
	printRaw(NEWLINE)
	return myList2

def dumpList(myList):
	i = 0
	while(i < len(myList)):
		spec = myList[i]
		print(spec.theDir + "," + spec.fileNameMinusPath)
		
		i += 1

def writeListToFile(fileObj, myList):
	for spec in myList:
		fileObj.write("DictBegin" + NEWLINE)
		fileObj.write(
			"Type/String"
			+ "," + "type"
			+ "," + "RepoFileSpec" + NEWLINE)
		
		fileObj.write(
			"Type/String"
			+ "," + "theDir"
			+ "," + spec.theDir + NEWLINE)
		fileObj.write(
			"Type/String"
			+ "," + "fileNameMinusPath"
			+ "," + spec.fileNameMinusPath + NEWLINE)
		
		fileObj.write("DictEnd" + NEWLINE)

def addDictValue(spec, propertyName, valueStr, lineStr, lineNum):
	#print("spec: " + str(propertyName) + "," + str(valueStr))
	if(propertyName == "theDir"):
		if(spec.theDir != None):
			print("Line Number: " + str(lineNum))
			raise Exception("dict property set twice: " + "theDir")
		spec.theDir = valueStr
		return

	if(propertyName == "fileNameMinusPath"):
		if(spec.fileNameMinusPath != None):
			print("Line Number: " + str(lineNum))
			raise Exception("dict property set twice: " + "fileNameMinusPath")
		spec.fileNameMinusPath = valueStr
		return

	print("lineNum: " + str(lineNum))
	raise Exception("line not recognized: " + lineStr)
	return

def parseListFromFile(fileObj):
	myList = []
	
	print("Reading list from file...")
	
	haveDict = False
	haveSpec = False
	lineNum = 0
	spec = None
	s1 = fileObj.readline()
	lastSpecCount = 0
	while(True):
		if(lastSpecCount + 1000 < len(myList)):
			printRaw(" .")
			lastSpecCount = len(myList)
			continue

		if(s1 == NEWLINE):
			lineNum += 1
			s1 = fileObj.readline()
			continue
		
		if(s1 == ""):
			break
	
		line = s1.strip()
		
		if(not haveDict):
			lineLen = getSepListLength(line, ',')
			#print(lineLen)
			if(lineLen == 0):
				csvType = getSepListItem(line, 0, ',')
				if(csvType == "DictBegin"):
					haveDict = True
					s1 = fileObj.readline()
					lineNum += 1
					continue
			
			print("lineNum: " + str(lineNum))
			raise Exception("line not recognized: " + line)
		
		if(haveDict and not haveSpec):
			lineLen = getSepListLength(line, ',')
			if(lineLen == 2):
				i = 0
				while(i < 3):
					if(i == 0):
						csvType = getSepListItem(line, i, ',')
						if(csvType == "Type/String"):
							i += 1
							continue
					if(i == 1):
						csvField = getSepListItem(line, i, ',')
						if(csvField == "type"):
							i += 1
							continue
					if(i == 2):
						csvValue = getSepListItem(line, i, ',')
						if(csvValue == "RepoFileSpec"):
							i += 1
							continue
					
					print("lineNum: " + str(lineNum))
					raise Exception("line not recognized: " + line)
					
				haveSpec = True
				spec = RepoFileSpec()
				s1 = fileObj.readline()
				lineNum += 1
				continue

			print("lineNum: " + str(lineNum))
			raise Exception("line not recognized: " + line)
						
		if(haveDict and haveSpec):
			lineLen = getSepListLength(line, ',')
			if(lineLen == 2):
				i = 0
				while(i < 3):
					if(i == 0):
						csvType = getSepListItem(line, i, ',')
						if(csvType == "Type/String"):
							i += 1
							continue
						
						print("lineNum: " + str(lineNum))
						raise Exception("line not recognized: " + line)
						
								
					if(i == 1):
						addDictValue(
							spec,
							getSepListItem(line, 1, ','),
							getSepListItem(line, 2, ','),
							line,
							lineNum)
						break
						
					print("lineNum: " + str(lineNum))
					raise Exception("line not recognized: " + line)

				s1 = fileObj.readline()
				lineNum += 1
				continue
			
			if(lineLen == 0):
				i = 0
				while(i < 3):
					if(i == 0):
						csvType = getSepListItem(line, i, ',')
						if(csvType == "DictEnd"):
							if(spec.theDir == None
								or spec.fileNameMinusPath == None):
								
								print("lineNum: " + str(lineNum))
								raise Exception("dict not valid: " + line)
							
							myList.append(spec)
							break
						
					print("lineNum: " + str(lineNum))
					raise Exception("line not recognized: " + line)

				spec = None
				haveDict = False
				haveSpec = False
				s1 = fileObj.readline()
				lineNum += 1
				continue
		print("lineNum: " + str(lineNum))
		raise Exception("line not recognized: " + line)
		continue
	printRaw(NEWLINE)
	return myList

#
# Simple file list functions,
# that relate to Debian cd-s and repositories
#

def getFileList(theDir):
	localList1 = []
	
	if(not dirExists2(theDir)):
		return myList1
	
	localList2 = os.listdir(theDir)
	if(localList2 == None):
		return localList1
	
	i = 0
	while(i < len(localList2)):
		entry = localList2[i]
		
		if(entry == "." or entry == ".."):
			i += 1
			continue
		
		if(entry == None or entry == ""):
			i += 1
			continue
		
		if(fileExists(pathCombine2(theDir, entry))):
			localList1.append(pathCombine2(theDir, entry))
			i += 1
			continue

		if(dirExists2(pathCombine2(theDir, entry))):
			if(len(entry) == 1):
				if(entry[0] >= '0' and entry[0] <= '9'):
					localList1.extend(getFileList(pathCombine2(theDir, entry)))
					i += 1
					continue

		if(dirExists(pathCombine2(theDir, entry))):
			localList1.extend(getFileList(pathCombine2(theDir, entry)))
			i += 1
			continue
		
		# otherwise, ignore path
		i += 1
	
	return localList1

def replaceBackslash(localFiles):
	print("Replacing backslashes in filenames in list...")
	i = 0
	while(i < len(localFiles)):
		fileStr = localFiles[i]
		j = 0
		while(j < len(fileStr)):
			if(fileStr[j] == '\\'):
				fileStr[j] = '/'
			j += 1
		i += 1
	return
	
def rebaseIfPathFound(path1, innerPath):
	if(innerPath == None or innerPath == ""):
		return None
	
	i = 0
	path1Len = len(path1)
	possibleMatchIndex = 0
	isPossibleMatch = False
	j = 0
	while(i < path1Len):
		c = path1[i]
		if(not isPossibleMatch):
			if(i == 0):
				if(c != '/'
					and c != '\\'
					and c == innerPath[0]):
					
					possibleMatchIndex = i
					i = 1
					j = 1
					isPossibleMatch = True
					continue
			
			if(path1[i] == '/' or path1[i] == '\\'):
				j = 0
				i += 1
				isPossibleMatch = True
				possibleMatchIndex = i
				continue
		
		if(isPossibleMatch):
			if(j < len(innerPath)):
				if(path1[i] != innerPath[j]):
					isPossibleMatch = False
					continue
				
				i += 1
				j += 1
				continue
			
			if(path1[i] == '/' or path1[i] == '\\'): break
			
			isPossibleMatch = False
			continue
			
		i += 1
		
	if(isPossibleMatch):
		return path1[possibleMatchIndex:]
	
	return None

def removeNonRepoFiles(localList):
	print("Removing non repository files in list...")
	i = 0
	while(i < len(localList)):
		path1 = localList[i]
		
		path2 = rebaseIfPathFound(path1, "pool/main")
		if(path2 != None):
			path2 = rebaseIfPathFound(path2, "main")
			if(path2 != None):
				localList[i] = path2
				i += 1
				continue
		
		path2 = rebaseIfPathFound(path1, "pool/contrib")
		if(path2 != None):
			path2 = rebaseIfPathFound(path2, "contrib")
			if(path2 != None):
				localList[i] = path2
				i += 1
				continue
		
		path2 = rebaseIfPathFound(path1, "pool/non-free")
		if(path2 != None):
			path2 = rebaseIfPathFound(path2, "non-free")
			if(path2 != None):
				localList[i] = path2
				i += 1
				continue
		
		localList.pop(i)
		continue
	return

#
# Debian formatted list functions
#

class PackageInfo:
	def __init__(self):
		self.pkgName = None
		self.fileName = None
		self.files = []
		self.theDir = None

class ArchInfo:
	def __init__(self):
		self.name = None
		self.longName = None
		self.listName = None
		
def getListFromMirror(outputDir, mirror, distName, archInfo):
	if(dirExists(outputDir)):
		raise Exception("output dir already exists: " + outputDir)

	relDir = os.getcwd()
	
	print("Downloading arch based list...")
	
	makeDirs(outputDir)
	os.chdir(outputDir)
	
	webPath = ("https://"
		+ mirror
		+ "/" + "debian"
		+ "/" + "dists" + "/" + distName
		+ "/" + "main"
		+ "/" + archInfo.longName
		+ "/" + archInfo.listName + ".gz")
	# Example: https://mirrors.xmission.com/debian/dists/testing/main/Packages.gz
	print("Web path: " + webPath)
	
	r = os.system(
		"wget"
		+ " --quiet --show-progress --progress=bar"
		+ " " + webPath)
	if(r != 0):
		raise Exception("getting list from mirror failed with error number: " + str(r))
	
	os.chdir(relDir)
	return

def addPropertyLine(pkg, labelStr, lineStr, lineNum):
	if(labelStr == "Filename"):
		if(pkg.fileName != None):
			print("Line Number: " + str(lineNum))
			raise Exception("property set twice: " + "Filename")
		pkg.fileName = lineStr
		return

	if(labelStr == "Directory"):
		if(pkg.theDir != None):
			print("Line Number: " + str(lineNum))
			raise Exception("property set twice: " + "Directory")
		pkg.theDir = lineStr
		return

	if(labelStr == "Files"):
		spaceCount = getSepListLength(lineStr, ' ')
		if(spaceCount != 2):
			print("Line Number: " + str(lineNum))
			raise Exception("property malformed: " + "Files")
		pkg.files.append(getSepListItem(lineStr, 2, ' '))
		return

def parseMirrorList(outputDir, archInfo):
	if(not dirExists(outputDir)):
		raise Exception("working dir does not exist: " + outputDir)

	relDir = os.getcwd()

	print("Unzipping arch list...")
	
	os.chdir(outputDir)
	
	r = os.system("gunzip"
		+ " --keep"
		+ " " + archInfo.listName + ".gz")
	if(r != 0):
		raise Exception("unzip error: " + archInfo.listName + ".gz")
	
	pkgList = []
	
	print("Loading arch list...")
	
	f1 = open(archInfo.listName, "r")
	s1 = NEWLINE
	havePackage = False
	pkgName = None
	lineNum = 0
	pkg = None
	labelStr = None
	lastPkgCount = 0
	while(s1 != None):
		if(lastPkgCount + 1000 < len(pkgList)):
			printRaw(" .")
			lastPkgCount = len(pkgList)
			continue
		
		if(havePackage):
			if(s1 == ""):
				havePackage = False
				print("Done with package")
				pkgList.append(pkg)
				pkg = None
				s1 = f1.readline()
				lineNum += 1
				continue

			if(s1 == NEWLINE):
				havePackage = False
				#print("Done with package, lineNo=" + str(lineNum))
				pkgList.append(pkg)
				pkg = None
				s1 = f1.readline()
				lineNum += 1
				continue
			
			i = 0
			while(True):
				if(i >= len(s1)):
					# ignore string
					s1 = f1.readline()
					lineNum += 1
					break

				c = s1[i]
				#print("Eating char: " + c)
				
				if(labelStr == None):
					if(i > 0 and c == ':'):
						labelStr = s1[0:i]
						#print("Label=" + labelStr)
						
						i += 1
						continue
					
					if(c >= 'A' and c <= 'Z'):
						i += 1
						continue

					if(c >= 'a' and c <= 'z'):
						i += 1
						continue

					if(c >= '0' and c <= '9'):
						i += 1
						continue

					if(c == '-'):
						i += 1
						continue

				if(labelStr != None):
					if(c == ' '):
						# value continuation
						
						addPropertyLine(pkg, labelStr, s1[(i + 1):].strip(), lineNum)
						
						s1 = f1.readline()
						lineNum += 1
						break
					
					if(c == 13):
						# ignore line
						s1 = f1.readline()
						lineNum += 1
						break

					if(c == 10):
						# ignore line
						s1 = f1.readline()
						lineNum += 1
						break
					
					if(c == '\n'):
						# ignore line
						s1 = f1.readline()
						lineNum += 1
						break

					if(i == 0):
						labelStr = None
						break
				
				print("i: " + str(i))
				print("Label: " + labelStr)
				print("Line Number: " + str(lineNum))
				raise Exception("unexpected char: " + c)
			
			pass
			continue

		# havePackage is false
		
		if(s1 == NEWLINE):
			s1 = f1.readline()
			lineNum += 1
			continue
		
		if(s1.startswith("Package: ")):
			pkgName = s1[len("Package: "):].strip()
			#print("Package: " + pkgName)
			havePackage = True
			pkg = PackageInfo()
			pkg.pkgName = pkgName
			s1 = f1.readline()
			lineNum += 1
			continue
		
		if(s1 == "" or s1 == None): break
		
		print("Line Number: " + str(lineNum))
		raise Exception("invalid line: " + s1)
	
	printRaw(NEWLINE)
	os.chdir(relDir)
	return pkgList

#
# Cross logic functions 1
#

def makeSimpleFileListFromPackageList(pkgList):
	print("Working on list...")

	i = 0
	pLen = len(pkgList)
	localFiles = []
	while(i < pLen):
		pkg = pkgList[i]

		if(pkg.fileName != None):
			localFiles.append(pkg.fileName)
			
			i += 1
			continue
		
		if(pkg.theDir != None):
			for fName in pkg.files:
				localFiles.append(pathCombine2(pkg.theDir, fName))
			
			i += 1
			continue
		
		raise Exception("pkg not valid")
	
	return localFiles

def makeRegularListFromSimpleFileList(localFiles):
	print("Working on list...")
	myList = []
	i = 0
	fLen = len(localFiles)
	while(i < fLen):
		spec = RepoFileSpec()
		spec.fileName = localFiles[i]
		spec.calc()
		
		myList.append(spec)
		
		i += 1
		
	return myList


#
# Scratch functions from previous versions
#

def downloadFilesMaybe(earlyDownloadDir, mirror, oldRepoPath, pkgList, localList):
	i = 0
	while(i < len(pkgList)):
		pkg = pkgList[i]
				
		if(pkg.fileName != None):
			fs1 = FilePathSplit()
			fs1.fileName = pkg.fileName
			fs1.calc()
			
			j = 0
			isFound = False
			while(j < len(localList)):
				fs2 = FilePathSplit()
				fs2.fileName = localList[j]
				fs2.calc()
				
				if(fs2.theDir.find(fs1.theDir)):
					if(fs1.fileNameMinusPath == fs2.fileNameMinusPath):
						isFound = True
						break
				
				j += 1
			
			if(isFound):
				skipDownloadPackage(earlyDownloadDir, fs1.fileNameMinusPath, fs1.theDir)
			
			if(not isFound):
				downloadPackage(earlyDownloadDir, mirror, fs1.fileNameMinusPath, fs1.theDir)
		
		if(pkg.fileName == None):
			for fName in pkg.files:
				fileNameMinusPath = fName
				theDir = pkg.theDir
				
				j = 0
				isFound = False
				while(j < len(localList)):
					fs2 = FilePathSplit()
					fs2.fileName = localList[j]
					fs2.calc()
					
					if(fs2.theDir.find(theDir)):
						if(fileNameMinusPath == fs2.fileNameMinusPath):
							isFound = True
							break
					
					j += 1
				
				if(isFound):
					skipDownloadPackage(earlyDownloadDir, fileNameMinusPath, theDir)
				
				if(not isFound):
					downloadPackage(earlyDownloadDir, mirror, fileNameMinusPath, theDir)
		
		#if(not fs1.theDir.startswith("pool/main/c/clutter")):
		#	i += 1
		#	continue
		
		
		i += 1

	return

def skipDownloadPackage(earlyDownloadDir, fileNameMinusPath, theDir):
	print("dont need to download: " + fileNameMinusPath)
	return
	

def downloadPackage(earlyDownloadDir, mirror, fileNameMinusPath, theDir):
	
	print("need to download: " + fileNameMinusPath)
	print("thedir: " + theDir)
	
	downPath = pathCombine2(earlyDownloadDir, "repo-new")
	downPath = pathCombine2(downPath, theDir)
	makeDirs(downPath)
	os.chdir(downPath)
	
	r = os.system(
		"wget -c"
		+ " " + "https://"
		+ mirror
		+ "/" + "debian"
		+ "/" + theDir + "/" + fileNameMinusPath
		)
	if(r != 0):
		raise Exception("file download failed: " + fs1.fileNameMinusPath)
	
	return

#
# Command processing functions
#

def main():
	mirror = "mirrors.xmission.com"
	#mirror = "cdimage.debian.org"
	
	distName = "testing"

	relDir1 = os.getcwd()

	amd64 = ArchInfo()
	amd64.name = "amd64"
	amd64.longName = "binary-amd64"
	amd64.listName = "Packages"
	
	i386 = ArchInfo()
	i386.name = "i386"
	i386.longName = "binary-i386"
	i386.listName = "Packages"
	
	source = ArchInfo()
	source.name = "source"
	source.longName = "source"
	source.listName = "Sources"
	
	getList1 = False
	getList2 = False
	getList3 = False
	download = False
	compareLists = False
	outputDir = None
	inputDir = None
	arch = None
	listDir1 = None
	listDir2 = None
	
	i = 1
	count = len(sys.argv)
	while(i < count):
		arg = sys.argv[i]		
		nextArg = None
		if(i + 1 < count): nextArg = sys.argv[i + 1]
		
		if(arg == "--get-list-from-cd-mount"): getList1 = True
		if(arg == "--get-list-from-mirror"): getList2 = True
		if(arg == "--get-list-from-dir"): getList3 = True
		if(arg == "--download"): download = True
		
		if(arg == "--compare-lists"):
			nextArg2 = None
			if(i + 2 < count): nextArg2 = sys.argv[i + 2]
			
			if(nextArg == None or nextArg2 == None):
				raise Exception("--compare-lists needs two list directories as params")
			
			if(not existsDir(nextArg) or not existsDir(nextArg2)):
				raise Exception("--compare-lists needs two list directories as params")
			
			listDir1 = nextArg
			listDir2 = nextArg2
			compareLists = True
			i += 3
			continue
			
		if(arg == "--input-dir"):
			if(inputDir != None):
				raise Exception("--input-dir set twice")
			if(not dirExists2(nextArg)):
				raise Exception("--input-dir does not exist: " + nextArg)
			inputDir = nextArg
			i += 2
			continue
		
		if(arg == "--output-dir"):
			if(outputDir != None):
				raise Exception("--output-dir set twice")
			outputDir = nextArg
			i += 2
			continue
		
		if(arg == "--arch"):
			if(arch != None):
				raise Exception("arch cannot be set twice")
			if(nextArg == None):
				raise Exception("--arch param not given")
			if(nextArg == "amd64"): arch = "amd64"
			if(nextArg == "i386"): arch = "i386"
			if(nextArg == "source"): arch = "source"
			if(arch == None):
				raise Exception("unknown --arch param: " + nextArg)
			i += 2
			continue
		
		i += 1

	if(getList1):
		os.chdir(relDir1)

		if(inputDir == None):
			raise Exception("with --get-list-from-cd-mount, --input-dir must be set")
		if(not dirExists2(inputDir)):
			raise Exception("--input-dir does not exist")
		if(outputDir != None):
			if(dirExists2(outputDir)):
				raise Exception("--output-dir already exists")

		localFiles = getFileList(inputDir)
		replaceBackslash(localFiles)
		removeNonRepoFiles(localFiles)
		myList = makeRegularListFromSimpleFileList(localFiles)
		myList = sortList2(myList)
		print("List length: " + str(len(myList)))

		if(outputDir != None):
			makeDirs(outputDir)
			fileObj = open(pathCombine2(outputDir, "list1.csv"), "w")
			fileObj.seek(0, 0)
			writeListToFile(fileObj, myList)
			fileObj.close()

	if(getList2):
		os.chdir(relDir1)
		
		if(arch == None):
			raise Exception("with --get-list-from-mirror, --arch must be set")
		archInfo = None
		if(arch == "amd64"): archInfo = amd64
		if(arch == "i386"): archInfo = i386
		if(arch == "source"): archInfo = source
		
		if(outputDir == None):
			raise Exception("with --get-list-from-mirror, --output-dir must be set")
		if(dirExists2(outputDir)):
			raise Exception("--output-dir already exists")

		getListFromMirror(outputDir, mirror, distName, archInfo)
		
		pkgList = parseMirrorList(outputDir, archInfo)
		print("Package count: " + str(len(pkgList)))
		
		localFiles = makeSimpleFileListFromPackageList(pkgList)
		replaceBackslash(localFiles)
		removeNonRepoFiles(localFiles)
		myList = makeRegularListFromSimpleFileList(localFiles)
		myList = sortList2(myList)
		print("List length: " + str(len(myList)))

	if(getList3):
		os.chdir(relDir1)
		
		if(inputDir == None):
			raise Exception("with --get-list-from-dir, --input-dir must be set")
		if(not dirExists(inputDir)):
			raise Exception("--input-dir does not exist")
		
		fileObj = open(pathCombine2(inputDir, "list1.csv"), "r")
		fileObj.seek(0, 0)
		myList = parseListFromFile(fileObj)
		fileObj.close()
		#dumpList(myList)
		
		myList = sortList2(myList)
		
	#downloadFilesMaybe(earlyDownloadDir, mirror, oldRepoPath, pkgList, localList)

	print("DONE.")

main()
