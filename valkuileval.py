#! /usr/bin/env python3
# -*- coding: utf8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import glob
from pynlpl.formats import folia
from collections import defaultdict


classmap = {
    'bekende-fout': 'nonworderror',
    'woordenlijstfout': 'nonworderror',
    'hoofdletter': 'capitalizationerror',
    'punctuatie': 'missingpunctuation',
    'klankfout': 'confusion',
    'werkwoordfout': 'confusion',
    'bekende-verwarring': 'confusion',
    'fout-volgens-context': 'contexterror',
}


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
        self.refclsdistr = defaultdict(int)
        self.outclsdistr = defaultdict(int)
        self.aggrav = 0

    def output(self):
        print("OVERALL RESULTS")
        print("=================")
        print(" Total number of corrections in output      : ", self.tp+self.fp ),
        print(" Total number of corrections in reference   : ",  self.tp+self.fn )
        print(" Matching corrections                       : ",  self.tp)
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
            for cls in self.clstp:
                print("Precision for " + cls + " : ", round(self.clstp[cls] / (self.clstp[cls]+self.clsfp[cls]),2) )
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
        evaldata.outclsdistr[correction_out.cls] += 1
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

        correction_out.match = False
        for correction_ref in correction_out.alignedto:
            if correction_ref.new().hastext(strict=False) and correction_ref.new().text().strip() in ( suggestion.text().strip() for suggestion in correction_out.suggestions() ):
                #the reference text is in the suggestions!
                correction_out.match = True
                break
                #(deletions are filtered out)

        if correction_out.match:
            print(" + true positive: Suggestion for correction '" + origwordtext + "' ->  '" + correction_ref.text() + "' matches reference ["+correction_out.annotator + ", " + correction_out.cls + "]" ,file=sys.stderr)
            evaldata.tp += 1
            evaldata.modtp[correction_out.annotator] += 1
            evaldata.clstp[correction_out.cls] += 1
        else:
            if correction_out.alignedto:
                print(" - false positive: Corrections were suggested for '" + origwordtext + "', (" + correction_out.id + ") but none match the " +  str(len(correction_out.alignedto)) + " reference correction(s) ["+correction_out.annotator + ", " + correction_out.cls + "]" , file=sys.stderr)
            else:
                print(" - false positive: Corrections were suggested for '" + origwordtext + "', (" + correction_out.id + ") but there are no reference corrections for this word ["+correction_out.annotator + ", " + correction_out.cls + "]" , file=sys.stderr)

            evaldata.fp += 1
            evaldata.modfp[correction_out.annotator] += 1
            evaldata.clsfp[correction_out.cls] += 1

        correction_out.handled = False #init next round


    #Compute aggregated precision, all correction on the same word(s) are combined, only one needs to match
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
    for correction_ref in corrections_ref:
        evaldata.refclsdistr[correction_ref.cls] += 1
        if correction_ref.hasoriginal() and correction_ref.original().hastext(None,strict=False):
            origtext = correction_ref.original().text(None)
        else:
            origtext = None


        if not correction_ref.hastext(strict=False):
            if not origtext:
                print("ERROR: Reference correction " + correction_ref.id + " has no text whatsoever! Ignoring...", file=sys.stderr)
            else:
                print(" - Reference correction is a deletion, ignoring: '" + origtext + "' -> (deletion)", file=sys.stderr)
            continue

        if not origtext:
            origtext = "(insertion)"

        if isinstance(correction_ref.parent, folia.Word):
            #Correction under word,  set a custom attribute
            correction_ref.alignedto = [ co for co in corrections_out if co.parent.id == correction_ref.parent.id ]
        else:
            #insertions, merges, splits
            correction_ref.alignedto = [ co for co in corrections_out if co.hascurrent() and co.current().hastext(strict=False) and correction_ref.original().hastext(None,strict=False) and co.current().text() == correction_ref.original().text(None) and co.parent.id == correction_ref.parent.id ]

        match = False
        for correction_out in correction_ref.alignedto:
            if correction_ref.text() in ( suggestion.text() for suggestion in correction_out.suggestions() ):
                #the reference text is in the suggestions!
                match = True
                break

        if not match:
            if not correction_ref.alignedto:
                #print("ID: ", correction_ref.id,file=sys.stderr)
                #print("HASTEXT STRICT: ", correction_ref.hastext(strict=True),file=sys.stderr)
                #print("HASTEXT NONSTRICT: ", correction_ref.hastext(strict=False),file=sys.stderr)
                #print("TEXT: ", correction_ref.text(),file=sys.stderr)
                print(" - false negative: Reference correction '" + origtext  +  "' -> '" + correction_ref.text() + "' (" + correction_ref.id + ") was missed alltogether in the Valkuil output",file=sys.stderr)
                evaldata.fn += 1
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
