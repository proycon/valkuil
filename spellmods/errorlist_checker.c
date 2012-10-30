/* errorlist spellmod

   a checker that knows a lot of error-correction pairs and serves
   the corrections upon seeing an error

   args: errorlist_checker <lexicon> <1-word-per-line>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define DEBUG 1

unsigned long sdbm(char *str);

int main(int argc, char *argv[])
{
  FILE *bron,*context;
  char *part;
  char **errors;
  char **corrections;
  unsigned long *hash;
  char word[1024];
  char line[32768];
  unsigned long thishash;
  int  i,nrpairs=0;

  /* allocate error-correction pair list */
  errors=malloc(sizeof(char*));
  corrections=malloc(sizeof(char*));
  hash=malloc(sizeof(unsigned long));

  /* read error-correction pair list */
  nrpairs=0;
  bron=fopen(argv[1],"r");
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      part=strtok(line,"~\n");
      strcpy(word,part);
      corrections[nrpairs]=malloc((strlen(word)+1)*sizeof(char));
      strcpy(corrections[nrpairs],word);

      part=strtok(NULL,"~\n");
      strcpy(word,part);
      errors[nrpairs]=malloc((strlen(word)+1)*sizeof(char));
      strcpy(errors[nrpairs],word);

      hash[nrpairs]=sdbm(word);

      nrpairs++;

      corrections=realloc(corrections,(nrpairs+1)*sizeof(char*));
      errors=realloc(errors,(nrpairs+1)*sizeof(char*));
      hash=realloc(hash,(nrpairs+1)*sizeof(unsigned long));
      
      fgets(line,32768,bron);
    }
  fclose(bron);

  if (DEBUG)
    fprintf(stderr,"read %d words from lexicon\n",
	    nrpairs);

  context=fopen(argv[2],"r");
  while (!feof(context))
    {
      fscanf(context,"%s ",word);
      thishash=sdbm(word);
      
      fprintf(stdout,"%s",
	      word);
      
      for (i=0; i<nrpairs; i++)
	{
	  if (thishash==hash[i])
	    {
	      if (DEBUG)
		fprintf(stderr,"found correction [%s] for presumed error [%s]\n",
			corrections[i],word);
	      fprintf(stdout," %s",
		      corrections[i]);
	    }
	}

      fprintf(stdout,"\n");
      
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
