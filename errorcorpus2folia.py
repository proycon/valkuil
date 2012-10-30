#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import glob
import os

try:
    dcoixsl = sys.argv[1]
    errorcorpusxsl = sys.argv[2]
    sourcedir = sys.argv[3]
    inputoutputdir = sys.argv[4]
    refoutputdir = sys.argv[5]
    tmpdir = '/tmp/'    
except:
    print >>sys.stderr ,"Usage: errorcorpus2folia.py dcoi2folia.xsl errorcorpus2folia.xsl sourcedir inputoutputdir refoutputdir"
    sys.exit(2)
    
    
for inputfilename in glob.glob(sourcedir + '/*.xml'):     
    print >>sys.stderr, "Processing " + inputfilename
    
    #default namespace got thrashed! restore
    tmpfilename = tmpdir + os.path.basename(inputfilename)
    os.system("sed 's/<DCOI /<DCOI xmlns=\"http:\\/\\/lands.let.ru.nl\\/projects\\/d-coi\\/ns\\/1.0\" /g' " + inputfilename + ' > ' + tmpfilename) 
    
    
    inputoutputfilename = inputoutputdir + os.path.basename(inputfilename)
    refoutputfilename = refoutputdir + os.path.basename(inputfilename)
    os.system('xsltproc ' + dcoixsl + ' ' + tmpfilename + ' > ' + inputoutputfilename)
    os.system('xsltproc ' + errorcorpusxsl + ' ' + tmpfilename + ' > ' + refoutputfilename)
    os.unlink(tmpfilename)
    
