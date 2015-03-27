#! /usr/bin/env python3
# -*- coding: utf8 -*-



import getopt
import sys
import os
import glob
import traceback
from pynlpl.formats import folia


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
        self.tp = self.fp = self.np = 0
        self.modtp = defaultdict(int)
        self.modfp = defaultdict(int)
        self.clstp = defaultdict(int)
        self.clsfp = defaultdict(int)

    def output(self):
        print("OVERALL RESULTS")
        print("=================")
        print(" Total number of corrections in output      : ", self.tp+self.fp )
        print(" Total number of corrections in reference   : ",  self.tp+self.fn )
        print(" Precision (micro)                          : ", round(self.tp / self.tp+self.fp,2) )
        print(" Recall (micro)                             : ", round(self.tp / self.tp+self.fn,2) )
        print(" F1-score (micro)                           : ", round(2*self.tp / (2*self.tp+iself.fp+self.fn),2) )
        if self.modtp:
            print("")
            print("PER-MODULE RESULTS")
            print("====================")
            for module in self.modtp:
                print("Precision for " + module + " : ", round(self.modtp[module] / self.modtp[module]+self.modfp[module],2) )
            print("")
        if self.clstp:
            print("")
            print("PER-CLASS RESULTS")
            print("====================")
            for cls in self.clstp:
                print("Precision for " + cls + " : ", round(self.clstp[cls] / self.clstp[cls]+self.clsfp[cls],2) )
            print("")



def valkuileval(outfile, reffile, evaldata):
    outdoc = folia.Document(file=outfile)
    refdoc = folia.Document(file=reffile)
    if outdoc.id != refdoc.id:
        raise Exception("Mismatching document IDs for " +outfile + " and " + reffile)


    corrections_out  = list(outdoc.select(folia.Correction))
    corrections_ref  = list(refdoc.select(folia.Correction))

    #match the ones that cover the same words
    for correction_out in corrections_out:
        if isinstance(correction_out.parent, folia.Word):
            #Correction under word, set a custom attribute
            correction_out.alignedto = [ cr for cr in corrections_ref if cr.parent.id == correction_out.parent.id ]
        else:
            #insertions, merges, splits
            correction_out.alignedto = [ cr for cr in corrections_ref if cr.original().text('original') == correction_out.current.text() and cr.parent.id == correction_out.parent.id ]

        match = False
        for correction_ref in correction_out.alignedto:
            if correction_ref.text() in ( suggestion.text() for suggestion in correction_out.suggestions() ):
                #the reference text is in the suggestions!
                match = True
                break

        if match:
            evaldata.tp += 1
            evaldata.modtp[correction_out.annotator] += 1
            evaldata.clstp[correction_out.cls] += 1
        else:
            evaldata.fp += 1
            evaldata.modfp[correction_out.annotator] += 1
            evaldata.clsfp[correction_out.cls] += 1

    for correction_ref in corrections_ref:
        if isinstance(correction_ref.parent, folia.Word):
            #Correction under word,  set a custom attribute
            correction_ref.alignedto = [ co for co in corrections_out if co.parent.id == correction_ref.parent.id ]
        else:
            #insertions, merges, splits
            correction_out.alignedto = [ cr for cr in corrections_ref if co.current().text() == correction_ref.original().text('original') and co.parent.id == correction_ref.parent.id ]

        match = False
        for correction_out in correction_ref.alignedto:
            if correction_ref.text() in ( suggestion.text() for suggestion in correction_out.suggestions() ):
                #the reference text is in the suggestions!
                match = True
                break

        if not match:
            evaldata.fn += 1


def processdir(out, ref, evaldata):
    print("Searching in  " + out,file=sys.stderr)
    tp = fp = fn = 0
    for outfile in glob.glob(os.path.join(out ,'*')):
        reffile = outfile.replace(out,ref)
        if file[-len(settings.extension) - 1:] == '.' + settings.extension:
            valkuileval(outfile, reffile, evaldata)
        elif settings.recurse and os.path.isdir(reffile):
            processdir(outfile, reffile, evaldata)


class settings:
    extension = 'xml'
    recurse = True
    encoding = 'utf-8'
    ignoreerrors = False
    stdout = False

def main():
    original = acceptsuggestion = output = corrected = False
    setfilter = classfilter = None

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
