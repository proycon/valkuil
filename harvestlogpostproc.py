#!/usr/bin/python

import sys
import codecs

previtem = None
bufferline = None


previous = (None,None,None,None,None,None,None,None)


with codecs.open(sys.argv[1],'r','utf-8') as f:
    for line in f:
        fields = line.strip().split(' ')
        if len(fields) == 9:
            leftcontext = fields[:3]
            focusword = fields[3]
            rightcontext = fields[4:7]
            mode = fields[7]
            correction = fields[8] 
            suggestions = annotator = cls = ""
            current = (leftcontext, focusword, rightcontext, mode, correction)
        elif len(fields) == 10:
            leftcontext = fields[:3]
            focusword = fields[3]
            rightcontext = fields[4:7]
            mode = fields[7]
            suggestions = fields[8]
            annotator = cls = ""
            correction = fields[9]                        
            current = (leftcontext, focusword, rightcontext, mode, correction)
        elif len(fields) == 12:            
            leftcontext = fields[:3]
            focusword = fields[3]
            rightcontext = fields[4:7]
            mode = fields[7]
            cls = fields[8]
            annotator = fields[9]
            suggestions = fields[10]
            correction = fields[11]                        
            current = (leftcontext, focusword, rightcontext, mode, correction)            
        else:
            print >>sys.stderr, "Unexpected number of fields: " + str(len(fields)) + ", skipping..."
            continue
            
        if current == previous: 
            print >>sys.stderr, "Duplicate record, skipped: " + repr(current)
            continue

        if (mode == 'free-correction' and previous[3] == 'discarded' and leftcontext == previous[0] and rightcontext == previous[2]):
            print >>sys.stderr, "Discarded prior to free-correction, omitting: " + repr(previous) 
            previous = (None,None,None,None,None,None,None,None)
        
        #print PREVIOUS record:
        leftcontext,focusword, rightcontext,mode,cls,annotator,suggestions,correction = previous
        if mode and ( ( mode in ['manual-correction','free-correction','accepted-correction'] and focusword != correction) or mode == 'discarded'):  
            s = correction.upper() + "\t" + " ".join(leftcontext) + "\t" + focusword + "\t" + " ".join(rightcontext) + "\t" + mode.upper() + "\t" + cls + "\t" + annotator+ "\t" + suggestions + "\t" + correction
            print s.encode('utf-8')             
        
        previous = current
            
                                   
            
            # curitem = (leftcontext,focusword,rightcontext)
            # if curitem != previtem and bufferline:
                #flush buffer
                # print bufferline
                # bufferline = None
            # previtem = tuple(curitem)
                        

            # if mode == 'discarded' and bufferline == None:
                # bufferline = line
            # elif mode in ['manual-correction','free-correction','accepted-correction']:
                # bufferline = ""
                # if correction != focusword:
                    # print line
            
            
        
