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
import random

QUOTE = "\""

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

class CompareResult:
	def __init__(self):
		self.less = False
		self.greater = False
		
class DebianFileSpec:
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

			if(c == '/'):
				lastSlashIndex = j
			
			j += 1
			
		if(lastSlashIndex == 0):
			raise Exception("file name invalid: " + self.fileName)

		if(lastSlashIndex + 1 >= len(self.fileName)):
			raise Exception("file name invalid: " + self.fileName)
		
		self.theDir = self.fileName[0:lastSlashIndex]
		self.fileNameMinusPath = self.fileName[(lastSlashIndex + 1):]

		return

def printRaw(theStr):
	s2 = str(theStr)
	sys.stdout.write(s2)
	sys.stdout.flush()

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

def getListFromMirror(outputDir, mirror, archInfo):
	if(dirExists(outputDir)):
		raise Exception("output dir already exists: " + outputDir)

	relDir = os.getcwd()
	
	makeDirs(outputDir)
	os.chdir(outputDir)
	# https://mirrors.xmission.com/debian/dists/testing/main/
	r = os.system(
		"wget -c"
		+ " " + "https://"
		+ mirror
		+ "/" + "debian/dists/bullseye/main"
		+ "/" + archInfo.longName
		+ "/" + archInfo.listName + ".gz"
		)
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
	
	os.chdir(outputDir)
	
	r = os.system("gunzip"
		+ " --keep"
		+ " " + archInfo.listName + ".gz")
	if(r != 0):
		raise Exception("unzip error: " + archInfo.listName + ".gz")
	
	pkgList = []
	
	print("Reading list from mirror list...")
	
	f1 = open(archInfo.listName, "r")
	s1 = "\n"
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

			if(s1 == "\n"):
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
					#print("WHAT")
					if(c == ' '):
						# value continuation
						
						addPropertyLine(pkg, labelStr, s1[(i + 1):].strip(), lineNum)
						
						s1 = f1.readline()
						lineNum += 1
						break
					
					if(c == 13):
						#print("UMM")
						# ignore line
						s1 = f1.readline()
						lineNum += 1
						break

					if(c == 10):
						#print("BUG")
						# ignore line
						s1 = f1.readline()
						lineNum += 1
						break
					
					if(c == '\n'):
						#print("TRIP")
						# ignore line
						s1 = f1.readline()
						lineNum += 1
						break

					if(i == 0):
						#print("YO!")
						labelStr = None
						break
				
				print("i: " + str(i))
				print("Label: " + labelStr)
				print("Line Number: " + str(lineNum))
				raise Exception("unexpected char: " + c)
			
			pass
			continue

		# havePackage is false
		
		if(s1 == "\n"):
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
	
	printRaw("\n")
	os.chdir(relDir)
	return pkgList

def makeRegularListFromPackageList(pkgList):
	i = 0
	pLen = len(pkgList)
	myList = []
	while(i < pLen):
		pkg = pkgList[i]

		if(pkg.fileName != None):
			spec = DebianFileSpec()
			spec.fileName = pkg.fileName
			spec.calc()
			
			myList.append(spec)
			
			i += 1
			continue
		
		if(pkg.theDir != None):
			for fName in pkg.files:
				spec = DebianFileSpec()
				spec.fileNameMinusPath = fName
				spec.theDir = pkg.theDir
				spec.fileName = pathCombine2(spec.theDir, spec.fileNameMinusPath)
				
				myList.append(spec)
			
			i += 1
			continue
		
		raise Exception("pkg not valid")
	
	return myList

def sortListSwapAt(myList, i):
	temp = myList[i + 1]
	myList[i + 1] = myList[i]
	myList[i] = temp

def sortList(myList):
	myComp = CompareResult()
	
	while(True):
		didSwap = False
		
		i = 0
		while(i < len(myList)):
			if(i + 1 >= len(myList)): break
			
			compareStrings(myComp,
				myList[i].theDir,
				myList[i + 1].theDir)

			if((not myComp.less) and (not myComp.greater)):
				compareStrings(myComp,
					myList[i].fileNameMinusPath,
					myList[i + 1].fileNameMinusPath)
			
			if(myComp.greater):
				sortListSwapAt(myList, i)
				didSwap = True
				
			if((not myComp.less) and (not myComp.greater)):
				del myList[i]
				continue
			
			i += 1
		
		if(not didSwap): break
	
		#print("doing again")
		continue
	return

def sortList2(myList):
	myComp = CompareResult()
	
	myList2 = []
	
	print("Sorting list...")
	
	lastProgress100 = 0
	
	myLen = len(myList)
	i = 0

	if(myLen == 0):
		print()
		return myList2
	
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
			
			if((not myComp.less) and (not myComp.greater)):
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
	
	printRaw("\n")
	return myList2

def dumpList(myList):
	i = 0
	while(i < len(myList)):
		spec = myList[i]
		print(spec.theDir + "," + spec.fileNameMinusPath)
		
		i += 1
	
def getFileList(theDir):
	myList1 = []
	
	if(not dirExists(theDir)):
		return myList1
	
	myList2 = os.listdir(theDir)
	if(myList2 == None):
		return myList1
	
	i = 0
	while(i < len(myList2)):
		entry = myList2[i]
		
		if(entry == "." or entry == ".."):
			i += 1
			continue
		
		if(entry == None or entry == ""):
			i += 1
			continue
		
		if(fileExists(pathCombine2(theDir, entry))):
			myList1.append(pathCombine2(theDir, entry))
			i += 1
			continue

		if(dirExists2(pathCombine2(theDir, entry))):
			if(len(entry) == 1):
				if(entry[0] >= '0' and entry[0] <= '9'):
					myList1.extend(getFileList(pathCombine2(theDir, entry)))
					i += 1
					continue

		if(dirExists(pathCombine2(theDir, entry))):
			myList1.extend(getFileList(pathCombine2(theDir, entry)))
			i += 1
			continue
		
		# otherwise, ignore path
		i += 1
	
	return myList1

def rebaseIfPathFound(path1, innerPath):
	i = 0
	path1Len = len(path1)
	possibleMatchIndex = 0
	isPossibleMatch = False
	j = 0
	while(i < path1Len):
		if(not isPossibleMatch):
			if(i == 0 and path1[0] != '/'):
				j = 0
				isPossibleMatch = True
				possibleMatchIndex = i
				continue
			
			if(path1[i] == '/'):
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
			
			if(path1[i] == '/'):
				return path1[possibleMatchIndex:]
				
			
			isPossibleMatch = False
			continue
			
		i += 1
		
	if(isPossibleMatch):
		return path1[possibleMatchIndex:]
	
	return None

def removeNonRepoFiles(localList):
	i = 0
	while(i < len(localList)):
		path1 = localList[i]
		
		path2 = rebaseIfPathFound(path1, "pool/non-free")
		if(path2 != None):
			path2 = rebaseIfPathFound(path1, "non-free")
			if(path2 != None):
				localList[i] = path2
				i += 1
				continue
		
		path2 = rebaseIfPathFound(path1, "pool/main")
		if(path2 != None):
			path2 = rebaseIfPathFound(path1, "main")
			if(path2 != None):
				localList[i] = path2
				i += 1
				continue

		path2 = rebaseIfPathFound(path1, "pool/contrib")
		if(path2 != None):
			path2 = rebaseIfPathFound(path1, "contrib")
			if(path2 != None):
				localList[i] = path2
				i += 1
				continue
		
		del localList[i]
		continue

def makeRegularListFromSimpleFileList(localFiles):
	myList = []
	i = 0
	fLen = len(localFiles)
	while(i < fLen):
		spec = DebianFileSpec()
		spec.fileName = localFiles[i]
		spec.calc()
		
		myList.append(spec)
		
		i += 1
		
	return myList

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

def main():
	mirror = "mirrors.xmission.com"
	#mirror = "cdimage.debian.org"

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
		
		if(arg == "--get-list-from-mirror"): getList1 = True
		if(arg == "--get-list-from-cd-mount"): getList2 = True
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

		getListFromMirror(outputDir, mirror, archInfo)
		
		pkgList = parseMirrorList(outputDir, archInfo)
		print("Package count: " + str(len(pkgList)))
		
		myList = makeRegularListFromPackageList(pkgList)
		myList = sortList2(myList)
		print("List length: " + str(len(myList)))

	if(getList2):
		os.chdir(relDir1)

		if(inputDir == None):
			raise Exception("with --get-list-from-cd-mount, --input-dir must be set")
		if(not dirExists2(inputDir)):
			raise Exception("--input-dir does not exist")
		if(dirExists2(outputDir)):
			raise Exception("--output-dir already exists")

		localList = getFileList(inputDir)
		removeNonRepoFiles(localList)
		myList = makeRegularListFromSimpleFileList(localList)
		myList = sortList2(myList)
		print("List length: " + str(len(myList)))
		
	#downloadFilesMaybe(earlyDownloadDir, mirror, oldRepoPath, pkgList, localList)

	print("DONE.")

main()

