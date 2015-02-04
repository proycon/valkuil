/* check-errors-against-lexicon 

   check the errorlist whether it actually contains frequent words as errors

   based on the lexicon spellmod

   args: check-errors-against-lexicon <lexicon> <errorlist>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MAXLD 2
#define MEDLD 1
#define LDTHRESHOLD 15
#define FREQFACTOR 10000
#define MINLENGTH 5
#define MINFREQTHRESHOLD 10000
#define MAXNRCLOSEST 5
#define DEBUG2 1
#define DEBUG 1

unsigned long sdbm(char *str);

int main(int argc, char *argv[])
{
  FILE *bron;
  char **lexicon;
  char *result;
  unsigned long *freqs;
  unsigned long *hash;
  char word[4096];
  char memword[4096];
  char corword[4096];
  char errword[4096];
  char capword[4096];
  char witheword[4096];
  char line[32768];
  char closestword[MAXNRCLOSEST+1][1024];
  int  closest[MAXNRCLOSEST+1];
  unsigned long closestfreq[MAXNRCLOSEST+1];
  unsigned long thishash,corhash,errhash,corfreq,errfreq;
  int  i,j,k,l,thislev,nrlex=0,nrclosest=0,readnr,wordlen,lexlen,counter,res;
  FILE *context;
  char *part;
  unsigned long freqthres=MINFREQTHRESHOLD;
  char inlex,withe,cap,inflection;

  setbuf(stdout,NULL);

  /* allocate lexicon */
  lexicon=malloc(sizeof(char*));
  freqs=malloc(sizeof(unsigned long));
  hash=malloc(sizeof(unsigned long));

  /* read lexicon */
  nrlex=0;
  bron=fopen(argv[1],"r");
  readnr=999;
  result=fgets(line,32768,bron);
  while ((!feof(bron))&&
	 (readnr>1))
    {
      sscanf(line,"%d %s ",
	     &readnr,word);

      lexicon[nrlex]=malloc((strlen(word)+1)*sizeof(char));
      strcpy(lexicon[nrlex],word);
      freqs[nrlex]=readnr;
      hash[nrlex]=sdbm(word);

      nrlex++;

      lexicon=realloc(lexicon,(nrlex+1)*sizeof(char*));
      freqs=realloc(freqs,(nrlex+1)*sizeof(unsigned long));
      hash=realloc(hash,(nrlex+1)*sizeof(unsigned long));
      result=fgets(line,32768,bron);
    }
  fclose(bron);

  if (DEBUG2)
    fprintf(stderr,"read %d words from lexicon\n",
	    nrlex);

  context=fopen(argv[2],"r");
  counter=0;
  while (!feof(context))
    {
      res=fscanf(context,"%s ",word);
      strcpy(memword,word);
      part=strtok(word,"~");
      strcpy(corword,part);
      part=strtok(NULL,"~");
      strcpy(errword,part);
      corhash=sdbm(corword);
      errhash=sdbm(errword);

      corfreq=errfreq=0;

      for (k=0; k<nrlex; k++)
	{
	  if (corhash==hash[k])
	    corfreq=freqs[k];
	  if (errhash==hash[k])
	    errfreq=freqs[k];
	}
      if (((errfreq*5)>corfreq)&&
	  (corfreq>0))
	fprintf(stderr,"corword: [%s]-[%ld], errword: [%s]-[%ld]\n",
		corword,corfreq,errword,errfreq);
      else
	fprintf(stdout,"%s\n",
		memword);
      counter++;
      if (counter%1000==0)
	fprintf(stderr,"processed %d word-error pairs\n",
		counter);

    }
  fclose(context);  

  return 0;
}

unsigned long sdbm(char *str)
{
  unsigned long hash = 0;
  int c;

  while (c = *str++)
    hash = c + (hash << 6) + (hash << 16) - hash;

  return hash;
}
