#!/usr/bin/python

import sys
import codecs
from pynlpl.formats import folia
from pynlpl.clients.frogclient import FrogClient

doc = None
outputfile = ''
docnum = 0



try:
    inputfile = sys.argv[1]
    frogport = int(sys.argv[2])
    outputdir = sys.argv[3]
    if len(sys.argv) >= 5:
        stripcorrections = bool(int(sys.argv[4]))
    else:
        stripcorrections = False
except:
    print >>sys.stderr ,"Usage: opentaalerrorharvest2folia.py inputfile frogport outputdir [stripcorrections=0/1]\nStart a frog server with: $ frog --skip=mp -S portnum"
    sys.exit(2)

frogclient = FrogClient('localhost', frogport)
correctioncount = 0

with codecs.open(inputfile,'r','utf-8','ignore') as f:
    for i, line in enumerate(f):        
        print >>sys.stderr,"@" + str(i),  
        if i % 1000 == 0:            
            if doc:
                doc.save(outputfile)
                print >>sys.stderr,"Saved " + outputfile
            docnum += 1
            outputfile = outputdir + '/opentaalerrorharvest' + str(docnum) + '.xml'
            doc = folia.Document(id='opentaalerrorharvest' + str(docnum))                        
            doc.declare(folia.AnnotationType.TOKEN, set='http://ilk.uvt.nl/folia/sets/ucto-nl.foliaset', annotator='Frog',annotatortype=folia.AnnotatorType.AUTO)
            doc.declare(folia.AnnotationType.POS, set='http://ilk.uvt.nl/folia/sets/cgn-legacy.foliaset', annotator='Frog',annotatortype=folia.AnnotatorType.AUTO)
            doc.declare(folia.AnnotationType.LEMMA, set='http://ilk.uvt.nl/folia/sets/mblem-nl.foliaset', annotator='Frog',annotatortype=folia.AnnotatorType.AUTO)
            if not stripcorrections:
                doc.declare(folia.AnnotationType.CORRECTION, set='opentaal', annotator='unknown',annotatortype= folia.AnnotatorType.MANUAL)
            textbody = doc.append(folia.Text) #, id='opentaalerrorharvest' + str(docnum) + '.text')

        line = line.strip()            
        if line:            
            sample_id = None
            corrections = {} #original -> new
            in_correction = 0
            skipsample = False
            
            #get natural text string and extract corrections
            text = ""        
            for j, c in enumerate(line):                
                if c == '|':
                    if not sample_id:
                        sample_id = 'OPENTAAL-s' + line[:j]
                        print >>sys.stderr, sample_id 
                    if in_correction:
                        correction_sep = j
                elif c == '~' and sample_id:
                    if in_correction and correction_sep:
                        if line[in_correction:correction_sep] in corrections:
                            print >>sys.stderr,"WARNING: Can not deal with two similar corrections ("+line[in_correction:correction_sep]+") in one sample. Skipping sample " + sample_id
                            skipsample = True
                            break
                        elif ' ' in line[in_correction:correction_sep] or ' ' in  line[correction_sep+1:j]:
                            print >>sys.stderr,"WARNING: Can not deal splits and merges (\"" + line[in_correction:correction_sep] + "\" -> \"" +  line[correction_sep+1:j] + "\" ) . This correction will be omitted"                            
                        else:                            
                            print >>sys.stderr,"Found correction (\"" + line[in_correction:correction_sep] + "\" -> \"" +  line[correction_sep+1:j] + "\" )"                    
                            corrections[line[in_correction:correction_sep]] = line[correction_sep+1:j]                        
                        text += line[in_correction:correction_sep]
                        in_correction = 0
                        correction_sep = 0
                    else:
                        in_correction = j+1
                elif not in_correction and sample_id:
                    text += c
            
            if "\\" in text:
                print >>sys.stderr,"WARNING: backslash in text, skipping sample to prevent Frog bug."
                continue
            
            if skipsample:
                continue
    
            
            if text and corrections and sample_id:
                print >>sys.stderr,"Invoking Frog and processing text: " + text
                paragraph = folia.Paragraph(doc, id=sample_id)
                sentence = paragraph.append(folia.Sentence)
                for j, (wordtext, lemma, morph, pos) in enumerate(frogclient.process(text)):
                    if not wordtext:
                        print >>sys.stderr,"Moving to next sentence"
                        sentence = paragraph.append(folia.Sentence)
                    else:
                        word = sentence.append(folia.Word, text=wordtext)
                        if lemma: 
                            word.append(folia.LemmaAnnotation, cls=lemma)
                        if pos: 
                            word.append(folia.PosAnnotation, cls=pos)
                        if wordtext in corrections and not stripcorrections:                            
                            word.correct(new=corrections[wordtext])
                            correctioncount += 1
                            print >>sys.stderr, "Succesfully added a correction (" + str(correctioncount) + ")"
                            
                textbody.append(paragraph)
                
if doc:
    doc.save(outputfile)
    print >>sys.stderr,"Saved " + outputfile            

            
            
        
