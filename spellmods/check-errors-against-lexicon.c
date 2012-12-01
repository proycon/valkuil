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
#define DEBUG2 0
#define DEBUG 1

unsigned long sdbm(char *str);

int main(int argc, char *argv[])
{
  FILE *bron;
  char **lexicon;
  unsigned long *freqs;
  unsigned long *hash;
  char word[1024];
  char memword[1024];
  char corword[1024];
  char errword[1024];
  char capword[1024];
  char witheword[1024];
  char closestword[MAXNRCLOSEST+1][1024];
  int  closest[MAXNRCLOSEST+1];
  unsigned long closestfreq[MAXNRCLOSEST+1];
  unsigned long thishash,corhash,errhash,corfreq,errfreq;
  int  i,j,k,l,thislev,nrlex=0,nrclosest=0,readnr,wordlen,lexlen,counter;
  FILE *context;
  char *part;
  unsigned long freqthres=MINFREQTHRESHOLD;
  char inlex,withe,cap,inflection;

  /* allocate lexicon */
  lexicon=malloc(sizeof(char*));
  freqs=malloc(sizeof(unsigned long));
  hash=malloc(sizeof(unsigned long));

  /* read lexicon */
  nrlex=0;
  bron=fopen(argv[1],"r");
  while (!feof(bron))
    {
      fscanf(bron,"%d %s ",
	     &readnr,word);

      fprintf(stderr,"%d %s\n",
	      readnr,word);

      lexicon[nrlex]=malloc((strlen(word)+1)*sizeof(char));
      strcpy(lexicon[nrlex],word);
      freqs[nrlex]=readnr;
      hash[nrlex]=sdbm(word);

      nrlex++;

      if (nrlex%1000000==0)
	fprintf(stderr,"read %d words (%d %s)\n",
		nrlex,readnr,word);

      lexicon=realloc(lexicon,(nrlex+1)*sizeof(char*));
      freqs=realloc(freqs,(nrlex+1)*sizeof(unsigned long));
      hash=realloc(hash,(nrlex+1)*sizeof(unsigned long));
    }
  fclose(bron);

  if (DEBUG2)
    fprintf(stderr,"read %d words from lexicon\n",
	    nrlex);

  context=fopen(argv[2],"r");
  counter=0;
  while (!feof(context))
    {
      fscanf(context,"%s ",word);
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
      if (errfreq>10)
	fprintf(stderr,"corword: [%s]-[%ld], errword: [%s]-[%ld]\n",
		corword,corfreq,errword,errfreq);
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
