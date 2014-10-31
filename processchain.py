#!/usr/bin/env python
#-*- coding:utf-8 -*-

#----------------------------------------------
#   Master script for Valkuil processing chain
#----------------------------------------------

import sys
import os
import datetime
import shutil
import json
import io
import random
from threading import Thread
from Queue import Queue
from pynlpl.textprocessors import Windower
import pynlpl.formats.folia as folia


#################### ABSTRACT MODULE  #################################

class AbstractModule(object): #Do not modify
    def __init__(self, doc, rootdir, outputdir, idmap, threshold):
        self.doc = doc
        self.rootdir = rootdir
        self.outputdir = outputdir
        self.done = False
        self.failed = False
        self.idmap = idmap
        self.threshold = threshold
        super(AbstractModule, self).__init__()

    def errout(self,msg):
        s = "[" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] PROCESSING-CHAIN ['+self.NAME+']: ' + msg
        try:
            print >>sys.stderr, s.encode('utf-8')
        except:
            pass

    def runcmd(self,cmd):
        global statusfile
        if not standalone and statusfile: clam.common.status.write(statusfile, "Running module " + self.NAME,50)
        errout("\tCalling module " + self.NAME + ": " + cmd)
        r = os.system(cmd)
        if r:
            self.errout("\tModule failed!")
            self.failed = True
        else:
            self.done = True
            self.errout("\tModule done")

    def readcolumnedoutput(self, outputfile):
        f = io.open(outputfile,'r',encoding='utf-8')
        for linenumber, instance in enumerate(f.readlines()):
            #get the Word ID based on line number
            try:
                wordid = self.idmap[linenumber]
            except IndexError:
                self.errout("ERROR processing results of module " + self.NAME + ": Unable to find word ID for line  " + str(linenumber))
                continue

            #get the word with that ID from the FoLiA document
            try:
                word = self.doc.index[wordid]
            except KeyError:
                self.errout("Unable to find word with ID: " + wordid)
                continue

            #split the instance line into multiple fields
            fields = instance.split(' ')

            yield word, fields


        f.close()


    def addcorrection(self, word, **kwargs  ):

        self.errout("Adding correction for " + word.id + " " + word.text())

        #Determine an ID for the next correction
        correction_id = word.generate_id(folia.Correction)

        if not 'confidence' in kwargs:
           kwargs['confidence']  = 0.5

        if 'suggestions' in kwargs:
            #add the correction
            word.correct(
                suggestions=kwargs['suggestions'],
                id=correction_id,
                set='valkuilset',
                cls=kwargs['cls'],
                annotator=kwargs['annotator'],
                annotatortype=folia.AnnotatorType.AUTO,
                datetime=datetime.datetime.now(),
                confidence=kwargs['confidence']
            )
        elif 'suggestion' in kwargs:
            #add the correction
            word.correct(
                suggestion=kwargs['suggestion'],
                id=correction_id,
                set='valkuilset',
                cls=kwargs['cls'],
                annotator=kwargs['annotator'],
                annotatortype=folia.AnnotatorType.AUTO,
                datetime=datetime.datetime.now(),
                confidence=kwargs['confidence']
            )
        else:
            raise Exception("No suggestions= specified!")


    def adderrordetection(self, word, **kwargs):
        self.errout("Adding correction for " + word.id + " " + word.text())


        #add the correction
        word.append(
            folia.ErrorDetection(
                self.doc,
                set='valkuilset',
                cls=kwargs['cls'],
                annotator=kwargs['annotator'],
                annotatortype='auto',
                datetime=datetime.datetime.now()
            )
        )

    def splitcorrection(self, word, newwords,**kwargs):
        sentence = word.sentence()
        newwords = [ folia.Word(self.doc, generate_id_in=sentence, text=w) for w in newwords ]
        kwargs['suggest'] = True
        kwargs['datetime'] = datetime.datetime.now()
        word.split(
            *newwords,
            **kwargs
        )

    def mergecorrection(self, newword, originalwords, **kwargs):
        sentence = originalwords[0].sentence()
        if not sentence:
            raise Exception("Expected sentence for " + str(repr(originalwords[0])) + ", got " + str(repr(sentence)))
        newword = folia.Word(self.doc, generate_id_in=sentence, text=newword)
        kwargs['suggest'] = True
        kwargs['datetime'] = datetime.datetime.now()
        sentence.mergewords(
            newword,
            *originalwords,
            **kwargs
        )




#################### MODULE DEFINITIONS #################################

class ErrorListModule(AbstractModule):
    NAME = "errorlist"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'errorlist_comparison.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-fout', annotator=self.NAME)

    def run(self):
        self.errout("MODULE: " + self.NAME)

        #Extract data for module
        f = io.open(self.outputdir + 'errorlist_comparison.test.inst','w',encoding='utf-8')
        for currentword in self.doc.words():
            f.write( unicode(currentword) + ' ')
        f.close()

        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/errorlist_checker ' + self.rootdir + 'spellmods/ValkuilErrors.1.1 ' + self.outputdir + 'errorlist_comparison.test.inst > ' + self.outputdir + 'errorlist_comparison.test.out')



class LexiconModule(AbstractModule):
    NAME = "lexiconmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lexicon_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='woordenlijstfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/lexicon_checker ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.freq20.length3.lex ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'lexicon_checker.test.out')


class AspellModule(AbstractModule):
    NAME = "aspellmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'aspell_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='woordenlijstfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/aspell_checker ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.freq20.length3.lex ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'aspell_checker.test.out')


class SoundAlikeModule(AbstractModule):
    NAME = "soundalikemodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'soundalike_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='klankfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/soundalike_checker ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.freq20.length3.lex ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'soundalike_checker.test.out')


class GarbageChecker(AbstractModule):
    NAME = "garbagechecker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'garbage_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.adderrordetection(word, cls='woordenlijstfout', annotator=self.NAME)



    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/garbage_checker ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.freq20.length3.lex ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'garbage_checker.test.out')

class SplitChecker(AbstractModule): #(merges in FoLiA terminology)
    NAME = "splitchecker"

    def process_result(self):
        if self.done:
            merges = []
            merge = []
            text = []
            prev = ''
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'split_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    if prev and fields[-1] != prev:
                        if merge:
                            merges.append(merge)
                            text.append(prev)
                            merge = []
                    else:
                        merge.append(word)
                    prev = fields[-1]
                else:
                    if merge:
                        merges.append(merge)
                        text.append(prev)
                        merge = []
                    prev = ''
            if merge:
                merges.append(merge)
                text.append(prev)

            for i, mergewords in enumerate(merges):
                #Add correction suggestion
                newword = text[i]
                self.mergecorrection(newword, mergewords, cls='spatiefout', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/split_checker ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.freq20.length3.lex ' + self.rootdir + 'spellmods/ValkuilSplitRunon.1.0 ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'split_checker.test.out')


class RunonChecker(AbstractModule): #(splits in FoLiA terminology)
    NAME = "runonchecker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'runon_checker.test.out'):
                if len(fields) > 2:
                    self.splitcorrection(word, fields[1:], cls='spatiefout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/runon_checker ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.freq20.length3.lex ' + self.rootdir + 'spellmods/ValkuilSplitRunon.1.0 ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'runon_checker.test.out')

class D_DT_Checker(AbstractModule):
    NAME = "d_dt_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'd-dt_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='werkwoordfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/d-dt_checker ' + str(self.threshold) + ' ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.d-dt ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'd-dt_checker.test.out')



class T_DT_Checker(AbstractModule):
    NAME = "t_dt_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 't-dt_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='werkwoordfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/t-dt_checker ' + str(self.threshold) + ' ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.t-dt ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 't-dt_checker.test.out')



class D_T_Checker(AbstractModule):
    NAME = "d_t_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'd-t_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='werkwoordfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/d-t_checker ' + str(self.threshold) + ' ' + self.rootdir + 'spellmods/ValkuilLexicon.1.1.d-t ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'd-t_checker.test.out')

class TTE_TTEN_Checker(AbstractModule):
    NAME = "tte_tten_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'tte-tten_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='werkwoordfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/tte-tten_checker ' + str(self.threshold) + ' ' + self.rootdir + 'spellmods/ValkuilLexicon.1.5.tte-tten ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'tte-tten_checker.test.out')


class T_Checker(AbstractModule):
    NAME = "t_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 't_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='t-uitgangfout', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/t_checker 0.975 ' + self.rootdir + 'spellmods/ValkuilLexicon.1.1.t ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 't_checker.test.out')



class WOPRChecker(AbstractModule):
    NAME = "woprchecker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'wopr_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='fout-volgens-context', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/wopr_checker ' + self.rootdir + 'spellmods/ValkuilWopr.1.0 ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'wopr_checker.test.out')


class WikiChecker(AbstractModule):
    NAME = "wikichecker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'wiki_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='fout-volgens-context', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/wiki_checker ' + str(self.threshold) + ' ' + self.rootdir + 'spellmods/wiki.confusibles ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'wiki_checker.test.out')


class JOU_JOUW_Checker(AbstractModule):
    NAME = "jou_jouw_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'jou-jouw_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error jou jouw ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'jou-jouw_checker.test.out')



class U_UW_Checker(AbstractModule):
    NAME = "u_uw_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'u-uw_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error u uw ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'u-uw_checker.test.out')



class ZEI_ZIJ_Checker(AbstractModule):
    NAME = "zei_zij_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'zei-zij_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)



    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error zei zij ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'zei-zij_checker.test.out')


class HAAR_ZIJ_Checker(AbstractModule):
    NAME = "haar_zij_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'haar-zij_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker haar zij ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'haar-zij_checker.test.out')


class WIL_WILT_Checker(AbstractModule):
    NAME = "wil_wilt_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'wil-wilt_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker wil wilt ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'wil-wilt_checker.test.out')


class WORD_WORDT_Checker(AbstractModule):
    NAME = "word_wordt_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'word-wordt_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error word wordt ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'word-wordt_checker.test.out')


class DEZE_DIT_Checker(AbstractModule):
    NAME = "deze_dit_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'deze-dit_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker deze dit ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'deze-dit_checker.test.out')


class DIE_WELKE_Checker(AbstractModule):
    NAME = "die_welke_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'die-welke_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker die welke 0.925 ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'die-welke_checker.test.out')


class HEN_HUN_Checker(AbstractModule):
    NAME = "hen_hun_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'hen-hun_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)



    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error hen hun ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'hen-hun_checker.test.out')


class DE_HET_Checker(AbstractModule):
    NAME = "de_het_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'de-het_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)



    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker de het 0.98 ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'de-het_checker.test.out')


class HUN_ZIJ_Checker(AbstractModule):
    NAME = "hun_zij_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'hun-zij_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)



    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error hun zij ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'hun-zij_checker.test.out')



class MIJ_IK_Checker(AbstractModule):
    NAME = "mij_ik_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'mij-ik_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker mij ik ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'mij-ik_checker.test.out')


class ME_MIJN_Checker(AbstractModule):
    NAME = "me_mijn_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'me-mijn_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error me mijn ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'me-mijn_checker.test.out')


class BEIDE_BEIDEN_Checker(AbstractModule):
    NAME = "beide_beiden_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'beide-beiden_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker beide beiden' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'beide-beiden_checker.test.out')



class NOG_NOCH_Checker(AbstractModule):
    NAME = "nog_noch_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'nog-noch_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error nog noch ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'nog-noch_checker.test.out')


class HARD_HART_Checker(AbstractModule):
    NAME = "hard_hart_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'hard-hart_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker hard hart ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'hard-hart_checker.test.out')


class ALS_DAN_Checker(AbstractModule):
    NAME = "als_dan_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'als-dan_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error als dan ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'als-dan_checker.test.out')


class TE_TEN_Checker(AbstractModule):
    NAME = "te_ten_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'te-ten_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker te ten ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'te-ten_checker.test.out')


class EENS_IS_Checker(AbstractModule):
    NAME = "eens_is_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'eens-is_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker eens is ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'eens-is_checker.test.out')


class LICHT_LIGT_Checker(AbstractModule):
    NAME = "licht_ligt_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'licht-ligt_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error licht ligt ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'licht-ligt_checker.test.out')


class GROOTTE_GROTE_Checker(AbstractModule):
    NAME = "grootte_grote_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'grootte-grote_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error grootte grote ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'grootte-grote_checker.test.out')


class HOOGTE_HOOGTEN_Checker(AbstractModule):
    NAME = "hoogte_hoogten_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'hoogte-hoogten_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)

    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker hoogte hoogten ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'hoogte-hoogten_checker.test.out')


class KAN_KEN_Checker(AbstractModule):
    NAME = "kan_ken_checker"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'kan-ken_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='bekende-verwarring', annotator=self.NAME)


    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'spellmods/confusible_checker_error kan ken ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'kan-ken_checker.test.out')



# --- Add new module classes here, and don't forget to declare them in the list below: ---


###################### MODULE DECLARATION  ###############################################

#Add all desired modules classes here here:

modules = [WOPRChecker, ErrorListModule, LexiconModule, AspellModule, SoundAlikeModule, SplitChecker, RunonChecker, D_DT_Checker, ZEI_ZIJ_Checker, NOG_NOCH_Checker, HARD_HART_Checker, LICHT_LIGT_Checker, GROOTTE_GROTE_Checker, DEZE_DIT_Checker, DE_HET_Checker, ALS_DAN_Checker, HEN_HUN_Checker, U_UW_Checker, KAN_KEN_Checker, ME_MIJN_Checker, WORD_WORDT_Checker, HUN_ZIJ_Checker]

# disabled for now: WikiChecker, T_DT_Checker, WIL_WILT_Checker, JOU_JOUW_Checker, DIE_WELKE_Checker, T_Checker, TTE_TTEN_Checker, TE_TEN_Checker, D_T_Checker, HAAR_ZIJ_Checker, HOOGTE_HOOGTEN_Checker, MIJ_IK_Checker, GarbageChecker, BEIDE_BEIDEN_Checker, EENS_IS_Checker

################################################################################




def errout(msg):
    print >>sys.stderr,  "[" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] PROCESSING-CHAIN: ' + msg

def processor(queue):
    while True:
        job = queue.get()
        job.run()
        queue.task_done()

def process(inputfile, outputdir, rootdir, bindir, statusfile, modules, threshold,standalone, save=True):
    #detect ID from filename
    id = os.path.basename(inputfile).split('.',1)[0].replace(' ','_')



    #Step 1 - Tokenize input text (plaintext) and produce FoLiA output
    if inputfile[-4:] == '.xml':
        shutil.copyfile(inputfile, outputdir+id+'.xml')
    else:
        if not standalone and statusfile: clam.common.status.write(statusfile, "Starting Tokeniser",1)
        errout("Starting tokeniser...")
        if sys.argv[1] == 'clam':
            os.system(bindir + 'ucto -c ' + bindir + '/../etc/ucto/tokconfig-nl -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')
        else:
            os.system(bindir + 'ucto -L nl -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')

        errout("Tokeniser finished")

    if not standalone and statusfile: clam.common.status.write(statusfile, "Reading FoLiA document",2)

    #Step 2 - Read FoLiA document
    doc = folia.Document(file=outputdir + id + '.xml')
    doc.declare(folia.Correction, 'valkuilset' )
    doc.declare(folia.ErrorDetection, 'valkuilset' )
    doc.language(value='nld');

    if not standalone and doc.metadatatype == folia.MetaDataType.NATIVE:
        if 'donate' in clamdata and clamdata['donate']:
            doc.metadata['donate'] = "yes"
            errout("Donated")
        else:
            doc.metadata['donate'] = "no"
            errout("Not donated")

    #Presuming that each token will be on one line, make a mapping from lines to IDs
    idmap = [ w.id for w in doc.words() ]

    ########## Extract data for modules ##############

    if not standalone and statusfile: clam.common.status.write(statusfile, "Extracting data for modules",3)


    f = io.open(outputdir + 'input.tok.txt','w',encoding='utf-8')
    for currentword in doc.words():
        f.write( unicode(currentword) + ' ')
    f.close()

    f = io.open(outputdir + 'agreement_checker.test.inst','w', encoding='utf-8')
    for prevword3, prevword2, prevword, currentword, nextword, nextword2, nextword3 in Windower(doc.words(),7):
        f.write( unicode(prevword3) + ' ' + unicode(prevword2) + ' ' + unicode(prevword) + ' ' + unicode(currentword) + ' ' + unicode(nextword) + ' ' + unicode(nextword2) + ' ' + unicode(nextword3) + ' ' + unicode(currentword) + '\n')
    f.close()


    ###### BEGIN CALL MODULES (USING PARALLEL POOL) ######
    # (nothing to edit here)

    errout( "Calling modules")
    if not standalone and statusfile: clam.common.status.write(statusfile, "Calling Modules",4)



    queue = Queue()
    threads = 4

    for i in range(threads):
        thread = Thread(target=processor,args=[queue])
        thread.setDaemon(True)
        thread.start()

    mods = [ Module(doc,rootdir,outputdir,idmap, threshold) for Module in modules ]
    for module in mods:
        queue.put(module)

    queue.join()
    #all modules done

    #process results and integrate into FoLiA
    for module in mods:
        module.process_result()

    ###### END ######

    #Store FoLiA document
    if save:
        if not standalone and statusfile: clam.common.status.write(statusfile, "Saving document",99)
        errout( "Saving document")
        doc.save()

    return doc



def folia2json(doc):
    data = {}
    for correction in doc.data[0].select(folia.Correction):
        suggestions = []
        for suggestion in correction.suggestions():
            suggestions.append( {'suggestion': unicode(suggestion), 'confidence': suggestion.confidence } )

        ancestor = correction.ancestor(folia.AbstractStructureElement)
        index = None
        if isinstance(ancestor, folia.Sentence):
            text = unicode(correction.current())
            index = 0
            for i, item in enumerate(ancestor):
                if isinstance(item, folia.Word):
                    index += 1
                if item is correction:
                    break
        elif isinstance(ancestor, folia.Word):
            text = unicode(ancestor)
            sentence = ancestor.ancestor(folia.Sentence)
            for i, word in enumerate(sentence.words()):
                if word is ancestor:
                    index = i
                    break
        if index is None:
            raise Exception("index not found")

        data.append( {'index': index, 'text': text, 'suggestions': suggestions, 'annotator': correction.annotator  } )
    return data



try:
    import clam.common.data
    import clam.common.status
    standalone = False
except ImportError:
    standalone = True
    print sys.stderr, "WARNING: CLAM modules not found, trying to run standalone...."

id = None
bindir = ''
if sys.argv[1] == 'clam':
    standalone = False
    #called from CLAM: processchain.py clam datafile.xml
    rootdir = sys.argv[2]
    bindir = sys.argv[3]
    if bindir[-1] != '/':
        bindir += '/'
    datafile = sys.argv[4]
    outputdir = sys.argv[5]
    if outputdir[-1] != '/':
        outputdir += '/'
    statusfile = sys.argv[6]


    clamdata = clam.common.data.getclamdata(datafile)
    threshold = float(clamdata['sensitivity'])

    for inputfile in clamdata.inputfiles('foliainput'):
        process(str(inputfile), outputdir, rootdir, bindir, statusfile, modules, threshold,standalone)
    for inputfile in clamdata.inputfiles('textinput'):
        process(str(inputfile), outputdir, rootdir, bindir, statusfile, modules, threshold,standalone)

    sys.exit(0)

elif sys.argv[1] == 'process_sentence':
    standalone = True
    rootdir = ''
    statusfile = None

    sentence = unicode(sys.argv[2], 'utf-8')

    tmpdir = ".process_sentence." + "%032x" % random.getrandbits(128)
    os.mkdir(tmpdir)
    with io.open(tmpdir + '/sentence.txt', 'w', encoding='utf-8') as f:
        f.write(sentence)
    threshold = 0.9

    doc = process(tmpdir + '/sentence.txt', tmpdir, rootdir, bindir, statusfile, modules, threshold,standalone, False)

    print json.dumps(folia2json(doc))

    shutil.rmtree(tmpdir)

else:
    standalone = True
    try:
        inputfile = sys.argv[1]
        if len(sys.argv) >= 3:
            id = sys.argv[2]
    except:
        print >>sys.stderr, "Syntax: processchain.py inputfile [id] [responsivity-threshold]"
        sys.exit(1)
    try:
        threshold = int(sys.argv[3])
    except:
        threshold = 0.9
    rootdir = ''
    outputdir = '' #stdout
    statusfile = None

    process(inputfile, outputdir, rootdir, bindir, statusfile, modules,  threshold,standalone)


if not standalone and statusfile: clam.common.status.write(statusfile, "All done",100)
errout("All done!")
sys.exit(0)
