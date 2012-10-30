#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import codecs
from collections import defaultdict

total = defaultdict(int)
byannotator = {}
byclass = {}

begindate = None
beginline = 0
taillines = 0

try:
    if int(sys.argv[2]) < 0:
        taillines = int(sys.argv[2])
    else:
        begindate = sys.argv[2]
except:
    pass

if taillines < 0:
    linecount = 0
    f = open(sys.argv[1],'r')
    for line in f:    
        linecount += 1
    f.close()
    beginline = linecount + taillines

f = codecs.open(sys.argv[1],'r','utf-8')
for i,line in enumerate(f):
    fields = line.split(' ')
    if len(fields) != 12 and len(fields) != 15:
        print >>sys.stderr,"Skipping line " + str(i+1) + ", old format..."#, len(fields)
        continue 
    else:
        print >>sys.stderr,"Processing " + str(i+1)

    if begindate:
        if len(fields) == 15:
            if fields[0] < begindate:
                print >>sys.stderr,"Skipping line " + str(i+1) + ", prior to date threshold..."#, len(fields)
                continue    
        else:
            print >>sys.stderr,"Skipping line " + str(i+1) + ", old format, no timestamp..."#, len(fields)
            continue
    elif beginline:    
        if (i < beginline):
            print >>sys.stderr,"Skipping line " + str(i+1) + "..."#, len(fields)
            continue    
    
    
    mode = fields[-5]
    cls = fields[-4]    
    correction = fields[-1]
    annotator = fields[-3]
    
    if annotator and len(annotator) < 30:
        if not annotator in byannotator:     
            byannotator[annotator] = defaultdict(int)
        byannotator[annotator][mode] += 1
    if cls:
        if not cls in byclass:     
            byclass[cls] = defaultdict(int)
        byclass[cls][mode] += 1        
    total[mode] += 1                
            
print "TOTALS\n---------------------\n"
for key, value in total.items(): 
    print key + ':\t' + str(value)
try:
    print 'Accepted Ratio:\t' + str(total['accepted-correction'] / float(total['discarded'] + total['accepted-correction']))
except:   
    pass

#print "\nBY MODULE\n---------------------\n"
#for annotator in sorted(byannotator):
#    print annotator
#    for key, value in byannotator[annotator].items(): 
#        print key + ':\t' + str(value)
#    print

print "\nBY CLASS\n---------------------\n"
for cls in sorted(byclass):
    print cls
    for key, value in byclass[cls].items():         
        print key + ':\t' + str(value)
    try:
        print 'Accepted Ratio:\t' + str(byclass[cls]['accepted-correction'] / float(byclass[cls]['discarded'] + byclass[cls]['accepted-correction']))
    except: 
        pass
    print
        
    
    
f.close()
