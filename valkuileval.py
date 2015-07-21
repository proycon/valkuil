#! /usr/bin/env python3
# -*- coding: utf8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import glob
import random
from pynlpl.formats import folia
from collections import defaultdict


annotator2class = {
    'errorlist': 'nonworderror',
    'lexiconmodule': 'nonworderror',
    'aspellmodule': 'nonworderror',
    'soundalikemodule': 'nonworderror',
    'splitchecker': 'spliterror',
    'woprchecker':'confusion',
    'd_dt_checker':'confusion',
    'deze_dit_checker':'confusion',
    'hard_hart_checker':'confusion',
    'de_het_checker':'confusion',
    'runonchecker':'runonerror',
    #'punc_recase_checker': 'capitalizationerror',
}


def getrandomid(doc,prefix="C"):
    randomid = ""
    while not randomid or randomid in doc.index:
        randomid =  prefix + "%08x" % random.getrandbits(32) #generate a random ID
    return randomid

def usage():
    print("valkuileval", file=sys.stderr)
    print("  by Maarten van Gompel (proycon)", file=sys.stderr)
    print("  Radboud University Nijmegen", file=sys.stderr)
    print("  2015 - Licensed under GPLv3", file=sys.stderr)
    print("", file=sys.stderr)
    print("FoLiA " + folia.FOLIAVERSION + ", library version " + folia.LIBVERSION, file=sys.stderr)
    print("", file=sys.stderr)
    print("This tool evaluates the difference between two copies of the same FoLiA document (IDs must be equal), one Valkuil output, one reference.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Usage: valkuileval file-or-dir-reference file-or-dir-system", file=sys.stderr)
    print("", file=sys.stderr)



def replace(correction, correctionchild):
    parent = correction.parent
    index = parent.getindex(correction)
    elements = correctionchild.copychildren(correction.doc)
    parent.remove(correction)
    for i, e in enumerate(elements):
        if isinstance(e, folia.TextContent) and e.cls == 'original':
            e.cls = 'current'
        parent.insert(index+i, e)


class Evaldata():
    def __init__(self):
        self.tp = self.fp = self.fn = 0
        self.aggrtp = self.aggrfp = self.aggrfn = 0
        self.modtp = defaultdict(int)
        self.modfp = defaultdict(int)
        self.clstp = defaultdict(int)
        self.clsfp = defaultdict(int)
        self.clsfn = defaultdict(int)
        self.refclsdistr = defaultdict(int)
        self.outclsdistr = defaultdict(int)
        self.aggrav = 0
        self.totalout = 0
        self.totalref = 0

    def output(self):
        print("OVERALL RESULTS")
        print("=================")
        assert self.tp + self.tp == self.totalout
        print(" Total number of corrections in output      : ", self.tp+self.fp ),
        print(" Total number of corrections in reference   : ", self.totalref ),
        print(" Matching output corrections (tp)                  : ",  self.tp)
        print(" Missed output corrections (fp)                    : ",  self.fp)
        print(" Missed reference corrections (fn)                 : ",  self.fn)
        print(" Virtual total (tp+fn)                             : ",  self.tp+self.fn )
        print(" Precision (micro)                          : ", round(self.tp / (self.tp+self.fp),2) )
        print(" Recall (micro)                             : ", round(self.tp / (self.tp+self.fn),2) )
        print(" F1-score (micro)                           : ", round(2*self.tp / (2*self.tp+self.fp+self.fn),2) )
        print("")
        print("Aggregated corrections when they are on the same words:")
        print(" Aggregated average corrections                        : ", round(self.aggrav,2) )
        print(" Total number of aggregated corrections in output      : ", self.aggrtp+self.aggrfp ),
        print(" Total number of aggregated corrections in reference   : ",  self.aggrtp+self.aggrfn )
        print(" Matching aggregated corrections                       : ",  self.aggrtp)
        print(" Aggregated precision (micro)                          : ", round(self.aggrtp / (self.aggrtp+self.aggrfp),2) )
        print(" Aggregated recall (micro)                             : ", round(self.aggrtp / (self.aggrtp+self.aggrfn),2) )
        print(" Aggregated F1-score (micro)                           : ", round(2*self.aggrtp / (2*self.aggrtp+self.aggrfp+self.aggrfn),2) )
        if self.modtp:
            print("")
            print("PER-MODULE RESULTS")
            print("====================")
            for module in self.modtp:
                print("Precision for " + module + " : ", round(self.modtp[module] / (self.modtp[module]+self.modfp[module]),2) )
            print("")
        if self.clstp:
            print("")
            print("PER-CLASS RESULTS")
            print("====================")
            for cls in sorted(set(self.clstp.keys()) | set(self.clsfn.keys())| set(self.clsfn.keys())):
                try:
                    p = round(self.clstp[cls] / (self.clstp[cls]+self.clsfp[cls]),2)
                except ZeroDivisionError:
                    p = 0
                try:
                    r = round(self.clstp[cls] / (self.clstp[cls]+self.clsfn[cls]),2)
                except ZeroDivisionError:
                    r = 0
                f = round(2*self.clstp[cls] / (2*self.clstp[cls]+self.clsfp[cls]+self.clsfn[cls]),2)
                print(cls + " : ", "P=" + str(p) + "\t" + "R=" + str(r) + "\t" + "F=" + str(f) )
            print("")
        print("REFERENCE CLASS DISTRIBUTION")
        print("================================")
        totalfreq = sum(self.refclsdistr.values())
        for cls, freq in self.refclsdistr.items():
            print(cls + " : ", freq, round(freq / totalfreq,2))
        print("")
        print("OUTPUT CLASS DISTRIBUTION")
        print("================================")
        totalfreq = sum(self.outclsdistr.values())
        for cls, freq in self.outclsdistr.items():
            print(cls + " : ", freq, round(freq / totalfreq,2))



def valkuileval(outfile, reffile, evaldata):

    try:
        outdoc = folia.Document(file=outfile)
    except Exception as e:
        print("Unable to read " + outfile + ": " + str(e),file=sys.stderr)
        if settings.ignoreerrors:
            return
        else:
            raise

    try:
        refdoc = folia.Document(file=reffile)
    except Exception as e:
        print("Unable to read " + reffile + ": " + str(e),file=sys.stderr)
        if settings.ignoreerrors:
            return
        else:
            raise

    if outdoc.id != refdoc.id:
        raise Exception("Mismatching document IDs for " +outfile + " and " + reffile)

    print("Processing " + outdoc.id,file=sys.stderr)


    corrections_out  = list(outdoc.select(folia.Correction))
    corrections_ref  = list(refdoc.select(folia.Correction))
    if not corrections_ref:
        print("No corrections in reference document " + refdoc.id + ", skipping...",file=sys.stderr)
        return

    #match the ones that cover the same words
    for correction_out in corrections_out:
        if not correction_out.id:
            #ensure all correctons have an ID
            correction_out.id = getrandomid(correction_out.doc)
        try:
            if correction_out.annotator == 'punc_recase_checker': #special handling
                deletion = any( [ not sug.hastext() for sug in correction_out.suggestions() ])
                if deletion:
                    mappedclass = 'redundantpunctuation'
                else:
                    ispunc = not any( [ sug.text().isalnum() for sug in correction_out.suggestions() if sug.hastext() ] )
                    if ispunc:
                        mappedclass = 'missingpunctuation'
                    else:
                        mappedclass = 'capitalizationerror'
            else:
                mappedclass = annotator2class[correction_out.annotator]
        except KeyError:
            print("WARNING: Unknown class '" + correction_out.annotator + "' in output, ID " + correction_out.id + " in document " + outdoc.id + ", mapping to 'uncertain'...",file=sys.stderr)
            mappedclass = 'uncertain'
        evaldata.outclsdistr[mappedclass] += 1
        if isinstance(correction_out.parent, folia.Word):
            #Correction under word, set a custom attribute
            correction_out.alignedto = [ cr for cr in corrections_ref if cr.parent.id == correction_out.parent.id ]
            origwordtext = correction_out.parent.text()
        else:
            if correction_out.hascurrent():
                #merges, splits
                correction_out.alignedto = [ cr for cr in corrections_ref if cr.original().hastext(None,strict=False) and correction_out.current().hastext(strict=False) and cr.original().text(None) == correction_out.current().text() and cr.parent.id == correction_out.parent.id ]
                origwordtext = correction_out.current().text()
            else:
                #insertions
                next_out = correction_out.next(folia.Word)
                previous_out = correction_out.previous(folia.Word)
                correction_out.alignedto = [ cr for cr in corrections_ref if (not cr.hasoriginal() or len(cr.original()) == 0) and cr.parent.id == correction_out.parent.id and ((cr.next(folia.Word) and next_out and cr.next(folia.Word).id == next_out.id) or (cr.previous(folia.Word) and previous_out and cr.previous(folia.Word).id == previous_out.id) )  ]
                origwordtext = '(insertion)'

        deletion = False
        correction_out.match = False
        match = None
        for correction_ref in correction_out.alignedto:
            if correction_ref.new().hastext(strict=False) and correction_ref.new().text().strip() in ( suggestion.text().strip() for suggestion in correction_out.suggestions() if suggestion.hastext(strict=False) ):
                #the reference text is in the suggestions!
                correction_out.match = True
                correction_ref.match = True
                match = correction_ref
            elif correction_ref.hasnew(True) and not correction_ref.new().hastext(strict=False) and any( not suggestion.hastext(strict=False) for suggestion in correction_out.suggestions() ):
                #(we have a matching deletion)
                correction_out.match = True
                correction_ref.match = True
                match = correction_ref
                deletion = True

            if match is correction_ref:
                if not hasattr(correction_ref, 'alignedto'): correction_ref.alignedto = []
                if not correction_out in correction_ref.alignedto: correction_ref.alignedto.append(correction_out)

        correction_ref = match

        if correction_out.match:
            if deletion:
                print(" + true positive for deletion of '" + origwordtext + "' matches reference ["+correction_out.annotator + ", " + correction_out.cls + "]" ,file=sys.stderr)
            else:
                print(" + true positive: Suggestion for correction '" + origwordtext + "' ->  '" + correction_ref.text() + "' matches reference ["+correction_out.annotator + ", " + correction_out.cls + "]" ,file=sys.stderr)
            evaldata.tp += 1
            evaldata.modtp[correction_out.annotator] += 1
            evaldata.clstp[mappedclass] += 1
        else:
            if correction_out.alignedto:
                print(" - false positive: Corrections were suggested for '" + origwordtext + "', (" + correction_out.id + ") but none match the " +  str(len(correction_out.alignedto)) + " reference correction(s) ["+correction_out.annotator + ", " + correction_out.cls + "]" , file=sys.stderr)
            else:
                print(" - false positive: Corrections were suggested for '" + origwordtext + "', (" + correction_out.id + ") but there are no reference corrections for this word ["+correction_out.annotator + ", " + correction_out.cls + "]" , file=sys.stderr)

            evaldata.fp += 1
            evaldata.modfp[correction_out.annotator] += 1
            evaldata.clsfp[mappedclass] += 1

        correction_out.handled = False #init next round


    #Compute aggregated precision, all correction on the same word(s) are combined, only one needs to match
    evaldata.totalout = len(corrections_out)
    for correction_out in corrections_out:
        if not correction_out.handled:
            if isinstance(correction_out.parent, folia.Word):
                correction_out.siblings = [ co for co in corrections_out if co.parent.id == correction_out.parent.id and co is not correction_out ]
            else:
                correction_out.siblings = [] #there are never multiple splits/merges in different corrections

            evaldata.aggrav = (evaldata.aggrav + 1 + len(correction_out.siblings)) / 2
            if correction_out.match or any( co.match for co in correction_out.siblings ):
                evaldata.aggrtp += 1
            else:
                evaldata.aggrfp += 1

            correction_out.handled = True
            for co in correction_out.siblings:
                co.handled = True



    #Computing recall
    evaldata.totalref = len(corrections_ref)
    for correction_ref in corrections_ref:
        evaldata.refclsdistr[correction_ref.cls] += 1
        if correction_ref.hasoriginal() and correction_ref.original().hastext(None,strict=False):
            origtext = correction_ref.original().text(None)
        else:
            origtext = None

        deletion = False

        if not correction_ref.hastext(strict=False):
            if not origtext:
                print("ERROR: Reference correction " + correction_ref.id + " has no text whatsoever! Ignoring...", file=sys.stderr)
            else:
                deletion = True
                print(" - Reference correction is a deletion: '" + origtext + "' -> (deletion)", file=sys.stderr)


        if not origtext:
            origtext = "(insertion)"

        #if deletion:
        #    #Deletion: Correction with suggestions in scope of word for output, Word in Correction/Original in reference
        #    correction_ref.alignedto = [ co for co in corrections_out if co.parent.id == correction_ref.original().id ]
        #elif isinstance(correction_ref.parent, folia.Word):
        #    #Correction under word,  set a custom attribute
        #    correction_ref.alignedto = [ co for co in corrections_out if co.parent.id == correction_ref.parent.id ]
        #else:
        #    #insertions, merges, splits
        #    correction_ref.alignedto = [ co for co in corrections_out if co.hascurrent() and co.current().hastext(strict=False) and correction_ref.original().hastext(None,strict=False) and co.current().text() == correction_ref.original().text(None) and co.parent.id == correction_ref.parent.id ]

        #match = False
        #for correction_out in correction_ref.alignedto:
        #    if deletion:
        #        #is there an empty suggestion? Then the deletion matches
        #        if any( not suggestion.hastext() for suggestion in correction_out.suggestions() ):
        #            match = True
        #            break
        #    else:
        #        if correction_ref.text() in ( suggestion.text() for suggestion in correction_out.suggestions() if suggestion.hastext() ):
        #            #the reference text is in the suggestions!
        #            match = True
        #            break

        if not hasattr(correction_ref,'match') or not correction_ref.match:
            if not hasattr(correction_ref, 'alignedto') or not correction_ref.alignedto:
                #print("ID: ", correction_ref.id,file=sys.stderr)
                #print("HASTEXT STRICT: ", correction_ref.hastext(strict=True),file=sys.stderr)
                #print("HASTEXT NONSTRICT: ", correction_ref.hastext(strict=False),file=sys.stderr)
                #print("TEXT: ", correction_ref.text(),file=sys.stderr)
                try:
                    print(" - false negative: Reference correction '" + origtext  +  "' -> '" + correction_ref.text() + "' (" + str(correction_ref.id) + ") was missed alltogether in the Valkuil output",file=sys.stderr)
                except folia.NoSuchText:
                    print(" - false negative: Reference correction '" + origtext  +  "' -> '(deletion)' (" + str(correction_ref.id) + ") was missed alltogether in the Valkuil output",file=sys.stderr)
                evaldata.fn += 1
                evaldata.clsfn[correction_ref.cls] += 1
                evaldata.aggrfn += 1


def processdir(out, ref, evaldata):
    print("Searching in  " + out,file=sys.stderr)
    for outfile in glob.glob(os.path.join(out ,'*')):
        reffile = outfile.replace(out,ref)
        if outfile[-len(settings.extension) - 1:] == '.' + settings.extension:
            valkuileval(outfile, reffile, evaldata)
        elif settings.recurse and os.path.isdir(reffile):
            processdir(outfile, reffile, evaldata)


class settings:
    extension = 'xml'
    recurse = True
    encoding = 'utf-8'
    ignoreerrors = True

def main():

    try:
        out = sys.argv[1]
        ref = sys.argv[2]
    except:
        print("Syntax: valkuileval out-file-or-dir ref-file-or-dir",file=sys.stderr)
        sys.exit(2)

    evaldata = Evaldata()

    if os.path.isdir(out) and os.path.isdir(ref):
        processdir(out, ref, evaldata)
    elif os.path.isfile(out) and os.path.isfile(ref):
        valkuileval(out, ref, evaldata)
    else:
        print("Specify two existing files or directories",file=sys.stderr)
        sys.exit(3)

    evaldata.output()

if __name__ == "__main__":
    main()
