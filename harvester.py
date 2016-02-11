#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#Valkuil harvester

import sys
import os
import glob
import time
import gc
from datetime import datetime
import pynlpl.formats.folia as folia

if len(sys.argv) >= 2:
     DIR = sys.argv[1]
else:
     DIR = "userdocs/"

now = time.time()
if len(sys.argv) >= 3:
     HARVESTTIME = int(sys.argv[2])
else:
     HARVESTTIME = 10800 #three hours after last modification

if len(sys.argv) >= 4:
    DELETE = bool(int(sys.argv[3]))
else:
    DELETE = True

print("Starting harvester",file=sys.stderr)
print("DIR=" + DIR,file=sys.stderr)
print("HARVESTTIME=" + str(HARVESTTIME),file=sys.stderr)
print("DELETE=" + str(DELETE),file=sys.stderr)


MAXFILESIZE = 10 * 1024 * 1025 #10MB

for filepath in glob.glob(DIR + '/*.xml'):
    print(filepath, file=sys.stderr)
    if len(filepath) > 10 and os.path.basename(filepath)[0]== 'D':
        filetime = os.path.getmtime(filepath)
        if now - filetime >= HARVESTTIME and os.path.getsize(filepath) < MAXFILESIZE:
            print("\tLoading",file=sys.stderr)
            filename = os.path.basename(filepath)
            try:
                doc = folia.Document(file=filepath)
            except Exception as e:
                print("Unable to load " + filepath + ": " + str(e), file=sys.stderr)
                continue

            if 'donate' in doc.metadata:
                donate = (doc.metadata['donate'] == 'yes')
            else:
                donate = False

            if donate:
                print("\tdonated..processing",file=sys.stderr)

                for word in doc.words():
                        if word.hasannotation(folia.Correction):
                            for correction in word.annotations(folia.Correction):
                                #data = [ w.text() if isinstance(w, folia.Word) else "NONE" for w  in word.context(3) ]
                                try:
                                    leftcontext = [ w.text() if isinstance(w, folia.Word) else "NONE" for w  in word.leftcontext(3) ]
                                    rightcontext = [ w.text() if isinstance(w, folia.Word) else "NONE" for w  in word.rightcontext(3) ]
                                except folia.NoSuchText:
                                    print("\tError obtaining context for " + correction.id + ". Skipping correction...",file=sys.stderr)
                                    continue

                                suggestions = []

                                if correction.hassuggestions():
                                    for i, suggestion in enumerate(correction.suggestions()):
                                        suggestions.append(suggestion.text())

                                if correction.datetime:
                                    if isinstance(correction.datetime, datetime):
                                        timestamp = correction.datetime.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        timestamp = correction.datetime
                                else:
                                   timestamp = datetime.fromtimestamp(filetime).strftime('%Y-%m-%d %H:%M:%S')

                                if correction.hasnew():
                                    #a correction has been made
                                    correction_text = correction.new(0).text()


                                    found = -2
                                    if correction.hassuggestions():
                                        found = -1
                                        for i, suggestion in enumerate(correction.suggestions()):
                                            if suggestion.text() == correction.text():
                                                found = i

                                    if found == -2:
                                        mode = 'free-correction'
                                        for errordetection in word.select(folia.ErrorDetection):
                                            if errordetection.cls != 'noerror':
                                                mode = 'hinted-correction'
                                    elif found == -1:
                                        mode = 'manual-correction'
                                    else:
                                        mode = 'accepted-correction'

                                    data = [timestamp, doc.id]

                                    if correction.hasoriginal():
                                        data += leftcontext + [correction.original(0).text()] + rightcontext
                                    else:
                                        data += leftcontext + [word.text()] + rightcontext

                                    data.append( mode )
                                    data.append( correction.cls )
                                    data.append( correction.annotator )
                                    if not suggestions: suggestions = ['-']
                                    data.append( "|".join(suggestions) )
                                    data.append( correction_text )
                                else:
                                    mode = 'ignored'
                                    for errordetection in word.select(folia.ErrorDetection):
                                        if errordetection.cls == 'noerror' and errordetection.annotatortype == folia.AnnotatorType.MANUAL:
                                            #actively flagged as not being an error
                                            mode = 'discarded'


                                    data = [timestamp, doc.id] + leftcontext + [word.text()] + rightcontext
                                    data.append( mode )
                                    data.append( correction.cls )
                                    data.append( correction.annotator )
                                    if not suggestions: suggestions = ['-']
                                    data.append( "|".join(suggestions) )
                                    data.append( word.text() ) #original text
                                print(" ".join(data))
                                print("\tHarvested a correction of type '" + mode + "'",file=sys.stderr)
            else:
                print("\tnot donated..skipping",file=sys.stderr)
            del doc
            gc.collect()

            #delete document
            if DELETE:
                print("\tDeleting " + filepath,file=sys.stderr)
                try:
                    os.unlink(filepath)
                except:
                    print("\tERROR: Unable to delete " + filepath + ". Permission denied?",file=sys.stderr)





