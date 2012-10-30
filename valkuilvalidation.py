#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import glob
from pynlpl.formats import folia
#from pynlpl.evaluation import ClassEvaluation
import clam.common.client
import os.path
import random
import time
import codecs
from collections import defaultdict

try:
    inputdir = sys.argv[1]
    refdir = sys.argv[2]
    workdir = sys.argv[3]
except:
    print >>sys.stderr,"Usage: valkuilvalidation.py inputdir refdir workdir [SCORE-ONLY=0|1]"
    sys.exit(2)
    
try:
    scoreonly = (sys.argv[4] == '1')
except:
    scoreonly = False

url = 'http://webservices.ticc.uvt.nl/valkuil/'
sensitivity=0.85


print "Connecting to server..."
#create client, connect to server, url is the full URL to the base of your webservice.
if not scoreonly:
    clamclient = clam.common.client.CLAMClient(url)


fsummary = open(workdir + '/overview.score','w')

summarytypes =  set()

#cumulative over all documents:
total_outputinstances = 0
total_refinstances = 0
    
total_detectionmatches = 0
total_detectionmisses = 0
total_detectioncorrect = 0 #detection + correct correction

total_correctionmatches = 0
total_correctionmisses = 0
total_correctionfp = 0
   
total_correctionmatchesbymod = defaultdict(int)
total_correctionmissesbymod = defaultdict(int)
total_correctionfpbymod = defaultdict(int)

total_outputinstancesbymod = defaultdict(int)


for inputfile in glob.glob(inputdir + '/*.xml'):
    print "Processing " + inputfile
    reffile = refdir + '/' + os.path.basename(inputfile)
    workfile = workdir + '/' + os.path.basename(inputfile)
    if not os.path.exists(reffile):
        print >>sys.stderr, "WARNING: No reference file found for " + inputfile + ", expected: " + reffile + "... skipping"
        continue

    try:
        refdoc = folia.Document(file=reffile)
    except:
        print >>sys.stderr, "ERROR: Unable to load FoLiA Document " + reffile        
        continue
        
    if not scoreonly:
 
        project = "valkuilclient" + str(random.getrandbits(64))

        print "\tCreating project (" + project + ")"
        #Now we call the webservice and create the project
        clamclient.create(project)
        
        data = clamclient.get(project)
        
        
        print "\tUploading " + inputfile
        #This invokes the actual upload
        clamclient.addinputfile(project, data.inputtemplate('foliainput'), inputfile)

        print "\tStarting project"
        data = clamclient.start(project,sensitivity=sensitivity) #start the process with the specified parameters

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
            time.sleep(2)
            data = clamclient.get(project) #get status again
            print "\tPROJECT IS RUNNING: " + str(data.completion) + '% -- ' + data.statusmessage
        print
        
        #Download all output files
        for outputfile in data.output:
            if str(outputfile)[-4:] == '.xml':
                try:
                    outputfile.loadmetadata()
                except:
                    continue            
                if outputfile.metadata.provenance.outputtemplate_id == 'foliaoutput':
                    print "\tDownloading " + str(outputfile) + " ..."
                    outputfile.copy(workfile)

        clamclient.delete(project)
    
    #Compare output file with reference file
    try:
        outputdoc = folia.Document(file=workfile)
    except:
        print >>sys.stderr, "ERROR: Unable to load valkuil output file " + workfile
        continue        
        
    
    #goals = []
    #observations = []
    
    match = False
    
    
    outputinstances = 0
    refinstances = 0

    
    detectionmatches = 0
    detectionmisses = 0
    detectioncorrect = 0 #detection + correct correction

    correctionmatches = 0
    correctionmisses = 0
    correctionfp = 0
       
    outputinstancesbymod = defaultdict(int)
    refinstancesbymod = defaultdict(int)
    correctionmatchesbymod = defaultdict(int)
    correctionmissesbymod = defaultdict(int)
    correctionfpbymod = defaultdict(int)
    

    
    f = codecs.open(workfile.replace('.xml','') + '.score','w','utf-8')
    
    fmiss = codecs.open(workfile.replace('.xml','') + '.misses','w','utf-8')
    
    processedcorrections = []
   
    for refword in refdoc.words():
        if refword.hasannotation(folia.Correction):
            refinstances += 1
            
            try:
                goal = refdoc[refword.id].text()
            except folia.NoSuchText:          
                print >>sys.stderr, "\tERROR: No text can be obtained for  " + refword.id  + "!!!"
                continue
            try:  
                outputword = outputdoc.index[refword.id]
            except KeyError:            
                print >>sys.stderr, "\tMissing word in output document: " + refword.id
                #f.write("MISS:  " + goal + ' (' + refword.id+ ', absent in output document)\n')
                detectionmisses += 1
                continue
                
            if outputword.hasannotation(folia.Correction):                                
                detectionmatches += 1

                
                found = False
                for correction in outputword.select(folia.Correction):                     
                    print "\tCorrection detected (" + correction.id + ")"                                        
                    f.write("CORRECTION DETECTED (" + correction.id + ')\n')
                                        
                    match = False
                    for suggestion in correction.suggestions():
                        processedcorrections.append(correction)
                        if suggestion.text() == goal: 
                            found = True
                            match = True
                            break
                    if match: 
                        print "\tCorrection accepted (" + correction.id + "): " + refword.text('original').encode('utf-8') + " -> " + goal.encode('utf-8')
                        #f.write("CORRECTION ACCEPTED: " + goal + ' (' + correction.id + ')\n')                    
                        correctionmatches += 1                    
                        correctionmatchesbymod[correction.annotator] += 1
                    else:                    
                        correctionmisses += 1                    
                        correctionmissesbymod[correction.annotator] += 1
                        print "\tCorrection rejected (" + correction.id + "): " + refword.text('original').encode('utf-8') + " -> " + ";".join([ x.text().encode('utf-8') for x in correction.suggestions()])
                        fmiss.write(refword.text('original') + "\t" + goal + "\t" + ";".join([ x.text() for x in correction.suggestions()]) + "\n" )                        
                        #f.write("CORRECTION REJECTED (" + correction.id+ ")\n")
                if found:
                    detectioncorrect += 1
            else: 
                print "\tCorrection missed  (" + refword.id + "): " + refword.text('original').encode('utf-8') + " -> " + goal.encode('utf-8')
                fmiss.write(refword.text('original') + "\t" + goal + "\n") 
                #f.write("CORRECTION MISSED:  " + goal + ' (' + refword.id+ ')\n')
                detectionmisses += 1
     
    corrections = outputdoc.select(folia.Correction)
    outputinstances = len(corrections)
    for correction in corrections:  
        if not (correction in processedcorrections): 
            correctionfp += 1
            correctionfpbymod[correction.annotator] += 1
            
    #goals.append(refdoc[word.id].text())
    #try:                
    #    observations.append(outputdoc[word.id].text())
    #except KeyError:
    #    observations.append('MISSING')
    #    print >>sys.stderr, "ERROR:Missing ID in output document: " + word.id

    #evaluation = ClassEvaluation(goals, observations)
    
        
    for type in set(correctionmatchesbymod.keys()) | set(correctionmissesbymod.keys()): 
        outputinstancesbymod[type] = correctionmatchesbymod[type]+correctionmissesbymod[type]+correctionfpbymod[type] 
        #accuracy = correctionmatchesbymod[type] / float(total)
        summarytypes.add(type)
        f.write("--- Module " + type + " ---\n")
        f.write( "Output instances: " + str(outputinstancesbymod[type]) + "\n")
        f.write( "Corrected correctly:     " + str(correctionmatchesbymod[type]) + '\t' + str(round((correctionmatchesbymod[type] / float(outputinstancesbymod[type])) * 100,1)) +  "\n")
        f.write( "Corrected incorrectly:   " + str(correctionmissesbymod[type]) + '\t' + str(round((correctionmissesbymod[type] / float(outputinstancesbymod[type])) * 100 ,1)) + "\n")
        f.write( "Corrected unnecessarily: " + str(correctionfpbymod[type]) + '\t' + str(round((correctionfpbymod[type] / float(outputinstancesbymod[type])) * 100,1)) + "\n")            
        f.write( "\n")    
        #if not type in summary_accuracybymod: 
        #    summary_accuracybymod[type] = []
        #summary_accuracybymod[type].append(accuracy) 
    
    #accuracy = correctionmatches / float(correctionmatches+correctionmisses)
    if outputinstances > 0:
                
        f.write("--- Overall correction statistics ---\n")
        assert outputinstances ==  correctionmatches+correctionmisses+correctionfp 
        f.write( "Output instances: " + str( outputinstances ) + "\n")        
        f.write( "Corrected correctly:     " + str(correctionmatches) + '\t' + str(round((correctionmatches / float(outputinstances)) * 100,1)) +  "%\n")
        f.write( "Corrected incorrectly:   " + str(correctionmisses) + '\t' + str(round((correctionmisses / float(outputinstances)) * 100,1)) + "%\n")
        f.write( "Corrected unnecessarily: " + str(correctionfp) + '\t' + str(round((correctionfp / float(outputinstances))*100,1)) + "%\n")
        f.write( "\n")        
    else:
        print >>sys.stderr, "\tNo output instances"
        f.write("No output instances corrections")

    if detectionmatches+detectionmisses > 0:        
        
        f.write("--- Overall detection statistics ---\n")
        f.write( "Reference instances: " + str( correctionmatches+ correctionmisses ) + "\n")
        refinstances = detectionmatches + detectionmisses        
        f.write( "Detected:                     " + str( detectionmatches ) +  '\t' + str(round((detectionmatches / float(refinstances))*100,1)) +  "%\n")
        f.write( " .. and correctly corrected:  " + str( detectioncorrect ) +  '\t' + str(round((detectioncorrect / float(refinstances))*100,1)) +  "%\n")
        f.write( "Undetected/missed:            " + str( detectionmisses ) +  '\t' + str(round((detectionmisses / float(refinstances))*100,1)) +  "%\n")
        f.write( "\n")
        
        

    else:    
        print >>sys.stderr, "\tNo reference corrections"
        f.write("No reference corrections")
        
    f.close()
    fmiss.close()
    
    
    #cumulative over all documents
     
    total_refinstances += refinstances
    total_outputinstances += outputinstances
    total_correctionmatches += correctionmatches
    total_correctionmisses += correctionmisses
    total_correctionfp += correctionfp
    total_detectioncorrect += detectioncorrect
    total_detectionmatches += detectionmatches
    total_detectionmisses += detectionmisses
    for type in outputinstancesbymod: total_outputinstancesbymod[type] += outputinstancesbymod[type]
    for type in correctionmatchesbymod: total_correctionmatchesbymod[type] += correctionmatchesbymod[type]
    for type in correctionmissesbymod: total_correctionmissesbymod[type] += correctionmissesbymod[type]
    for type in correctionfpbymod: total_correctionfpbymod[type] += correctionfpbymod[type]
         

fsummary.write("--- Overall correction statistics ---\n")
fsummary.write( "Output instances:        " + str( total_outputinstances ) + "\n")        
fsummary.write( "Corrected correctly:     " + str(total_correctionmatches) + '\t' + str(round((total_correctionmatches / float(total_outputinstances)) * 100,1)) +  "%\n")
fsummary.write( "Corrected incorrectly:   " + str(total_correctionmisses) + '\t' + str(round((total_correctionmisses / float(total_outputinstances)) * 100,1)) + "%\n")
fsummary.write( "Corrected unnecessarily: " + str(total_correctionfp) + '\t' + str(round((total_correctionfp / float(total_outputinstances))*100,1)) + "%\n")
fsummary.write( "\n")        
fsummary.write("--- Overall detection statistics ---\n")
fsummary.write( "Reference instances: " + str( total_refinstances ) + "\n")

fsummary.write( "Detected:             " + str( total_detectionmatches ) +  '\t' + str(round((total_detectionmatches / float(total_refinstances))*100,1)) +  "%\n")
fsummary.write( " .. and correctly corrected:  " + str( total_detectioncorrect ) +  '\t' + str(round((total_detectioncorrect / float(total_refinstances))*100,1)) +  "%\n")
fsummary.write( "Undetected/missed:    " + str( total_detectionmisses ) +  '\t' + str(round((total_detectionmisses / float(total_refinstances))*100,1)) +  "%\n")
fsummary.write("\n")

for type in summarytypes:
    total_outputinstancesbymod[type] = total_correctionmatchesbymod[type]+total_correctionmissesbymod[type]+total_correctionfpbymod[type]
    fsummary.write("--- Module " + type + " ---\n")
    fsummary.write( "Output instances: " + str(total_outputinstancesbymod[type]) + "\n")
    fsummary.write( "Corrected correctly:     " + str(total_correctionmatchesbymod[type]) + '\t' + str(round((total_correctionmatchesbymod[type] / float(total_outputinstancesbymod[type])) * 100,1)) +  "%\n")
    fsummary.write( "Corrected incorrectly:   " + str(total_correctionmissesbymod[type]) + '\t' + str(round((total_correctionmissesbymod[type] / float(total_outputinstancesbymod[type])) * 100 ,1)) + "%\n")
    fsummary.write( "Corrected unnecessarily: " + str(total_correctionfpbymod[type]) + '\t' + str(round((total_correctionfpbymod[type] / float(total_outputinstancesbymod[type])) * 100,1)) + "%\n")            
    fsummary.write( "\n")            

fsummary.close()

os.system('cat ' + workdir + '/overview.score')
