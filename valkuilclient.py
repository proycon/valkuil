#!/usr/bin/env python
#-*- coding:utf-8 -*-

###############################################################
# -- CLAM Client for Valkuil webservice --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#       
#       Licensed under GPLv3
#
###############################################################

import sys
import os
import time
import glob
import random
import codecs

#Import the CLAM Client API and CLAM Data API and other dependencies
# You can obtain CLAM from https://github.com/proycon/clam
from clam.common.client import *
from clam.common.data import *
from clam.common.formats import *
import clam.common.status

#Import FoLiA library
# You can obtain pynlpl from https://github.com/proycon/pynlpl
from pynlpl.formats import folia

url = 'http://webservices-lst.science.ru.nl/valkuil/'
sensitivity=0.95
donate = False

username = None
password = None


files = []
#Process arguments and parameters:
for arg in sys.argv[1:]:
    if arg[:7] == "--user=":
        username = arg[7:]
    elif arg[:7] == "--pass=":
        password = arg[7:]
    elif os.path.isfile(arg):
        files.append(arg)
    elif os.path.isdir(arg):
        files += [ x for x in glob.glob(arg + '/*') if x[0] != '.' ]
    else:
        print >>sys.stderr, "ERROR: Unknown argument, or file/directory does not exist: " + arg
        print >>sys.stderr, "Syntax: valkuilclient.py TEXTFILES"
        sys.exit(2)

if not files:
    print >>sys.stderr, "Syntax: valkuilclient.py TEXTFILES"
    print >>sys.stderr, "Options: --username=   --password="
    sys.exit(1)    


print "Connecting to server..."

        
#create client, connect to server, url is the full URL to the base of your webservice.
if username and password: 
    clamclient = CLAMClient(url,  username, password)
else:
    clamclient = CLAMClient(url)

print "Creating project..."
   
#this is the name of our project, it consists in part of randomly generated bits (so multiple clients don't use the same project and can run similtaneously)

#CLAM works with 'projects', for automated clients it usually suffices to create a temporary project,
#which we explicitly delete when we're all done. Each client obviously needs its own project, so we 
#create a project with a random name:
project = "valkuilclient" + str(random.getrandbits(64))

#Now we call the webservice and create the project
clamclient.create(project)

#get project status and specification

data = clamclient.get(project)


print "Uploading Files..."

#Upload the files (names were passed on the command line) to the webservice, always indicating
#the format.
for f in files:
    print "\tUploading " + f + " to webservice..."
    #This invokes the actual upload
    clamclient.addinputfile(project, data.inputtemplate('textinput'), f)



print "Starting..."

#Now we invoke the webservice, effectively
#starting the project. The start() method takes a project name and a set of keyword arguments, the keywords here
#correspond with the parameter IDs defined by your webservice.
data = clamclient.start(project, sensitivity=sensitivity, donate=donate) #start the process with the specified parameters

#Always check for parameter errors! Don't just assume everything went well! Use startsafe instead of start
#to simply raise exceptions on parameter errors.
if data.errors:
    print >>sys.stderr,"An error occured: " + data.errormsg
    for parametergroup, paramlist in data.parameters:
        for parameter in paramlist:
            if parameter.error:
                print >>sys.stderr,"Error in parameter " + parameter.id + ": " + parameter.error
    clamclient.delete(project) #delete our project (remember, it was temporary, otherwise clients would leave a mess)
    sys.exit(1)

#If everything went well, the system is now running, we simply wait until it is done and retrieve the status in the meantime
while data.status != clam.common.status.DONE:
    time.sleep(5) #wait 5 seconds before polling status
    data = clamclient.get(project) #get status again
    print "\tPROJECT IS RUNNING: " + str(data.completion) + '% -- ' + data.statusmessage


#Download all output files to current directory
for outputfile in data.output:
    if str(outputfile)[-4:] == '.xml':
        try:
            outputfile.loadmetadata()
        except:
            continue            
        if outputfile.metadata.provenance.outputtemplate_id == 'foliaoutput':
            print "\tDownloading " + str(outputfile) + " ..."
            targetfile = os.path.basename(str(outputfile))
            outputfile.copy(targetfile)
    
#delete our project (remember, it was temporary, otherwise clients would leave a mess)
clamclient.delete(project)

print "All done! Have a nice day!"
