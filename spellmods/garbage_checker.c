/* garbage spellmod

   baseline idea of a checker that determines whether a string is a proper word

   notes:

   * does not produce correction suggestions
   * smartly checks frequently occurring strings in the document

   args: garbage_checker <lexicon> <1-word-per-line>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MINLENGTH 3
#define MINDOCFREQ 2
#define DEBUG3 0
#define DEBUG2 1
#define DEBUG 1

unsigned long sdbm(char *str);

int main(int argc, char *argv[])
{
  FILE *bron;
  char **lexicon;
  char **doclexicon;
  unsigned long *freqs;
  unsigned long *hash;
  unsigned long *docfreqs;
  unsigned long thishash;
  char word[1024];
  char witheword[1024];
  char left[1024];
  char right[1024];
  int  i,j,k,m,nrlex=0,nrclosest=0,readnr,wordlen,nrdoclex=0;
  FILE *context;
  char inlex,indoclex=0,problem,withe,cap,withletters;

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

      lexicon[nrlex]=malloc((strlen(word)+1)*sizeof(char));
      strcpy(lexicon[nrlex],word);
      freqs[nrlex]=readnr;
      hash[nrlex]=sdbm(word);

      nrlex++;

      lexicon=realloc(lexicon,(nrlex+1)*sizeof(char*));
      freqs=realloc(freqs,(nrlex+1)*sizeof(unsigned long));
      hash=realloc(hash,(nrlex+1)*sizeof(unsigned long));
    }
  fclose(bron);

  if (DEBUG2)
    fprintf(stderr,"read %d words from lexicon\n",
	    nrlex);

  // determine recurring strings: create document lexicon
  nrdoclex=0;

  /* allocate lexicon */
  doclexicon=malloc(sizeof(char*));
  docfreqs=malloc(sizeof(unsigned long));

  context=fopen(argv[2],"r");
  while (!feof(context))
    {
      fscanf(context,"%s ",word);
      
      inlex=0;
      for (i=0; ((!inlex)&&(i<nrdoclex)); i++)
	{
	  if (strcmp(word,doclexicon[i])==0)
	    {
	      inlex=1;
	      docfreqs[i]++;
	    }
	}
      if (!inlex)
	{
	  doclexicon[nrdoclex]=malloc((strlen(word)+1)*sizeof(char));
	  strcpy(doclexicon[nrdoclex],word);
	  docfreqs[nrdoclex]=1;

	  nrdoclex++;

	  doclexicon=realloc(doclexicon,(nrdoclex+1)*sizeof(char*));
	  docfreqs=realloc(docfreqs,(nrdoclex+1)*sizeof(unsigned long));
	}
    }
  fclose(context);

  if (DEBUG3)
    {
      fprintf(stderr,"words in document above frequency threshold:\n");
      for (i=0; i<nrdoclex; i++)
	{
	  if (docfreqs[i]>=MINDOCFREQ)
	    fprintf(stderr,"%ld occurrences: [%s]\n",
		    docfreqs[i],doclexicon[i]);
	}
    }

  context=fopen(argv[2],"r");
  while (!feof(context))
    {
      fscanf(context,"%s ",word);

      problem=0;

      withletters=0;
      for (i=0; ((i<strlen(word))&&(!withletters)); i++)
	if (((word[i]>='A')&&(word[i]<='Z'))||
	    ((word[i]>='a')&&(word[i]<='z')))
	  withletters=1;
      
      if (withletters)
	{

	  withe=0;
	  if (word[strlen(word)-1]=='e')
	    {
	      withe=1;
	      strcpy(witheword,"");
	      for (i=0; i<strlen(word)-1; i++)
		{
		  strcat(witheword," ");
		  witheword[i]=word[i];
		}
	    }
	  
	  cap=0;
	  if ((word[0]>='A')&&
	      (word[0]<='Z'))
	    cap=1;
	  
	  nrclosest=0;
	  
	  wordlen=strlen(word);
	  
	  inlex=0;
	  thishash=sdbm(word);
	  
	  if (!cap)
	    {
	      for (k=0; ((k<nrlex)&&(!inlex)); k++)
		{
		  if (thishash==hash[k])
		    inlex=1;
		}
	      if ((!inlex)&&(withe))
		{
		  thishash=sdbm(witheword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if (thishash==hash[k])
			inlex=1;
		    }
		}
	      
	      indoclex=0;
	      for (k=0; ((k<nrdoclex)&&(!indoclex)); k++)
		{
		  if (word[0]==doclexicon[k][0])
		    {
		      if ((strcmp(word,doclexicon[k])==0)&&
			  (docfreqs[k]>=MINDOCFREQ))
			{
			  indoclex=1;
			}
		    }
		}
	    }
	  
	  if ((!inlex)&&
	      (!cap)&&
	      (!indoclex)&&
	      (wordlen>=(2*MINLENGTH)))
	    {
	      problem=1;
	      for (i=MINLENGTH; ((i<wordlen-(MINLENGTH-1))&&(problem)); i++)
		{
		  strcpy(left,"");
		  if (word[0]=='(')
		    {
		      for (j=1; j<i; j++)
			{
			  strcat(left," ");
			  left[j-1]=word[j];
			}
		    }
		  else
		    {
		      for (j=0; j<i; j++)
			{
			  strcat(left," ");
			  left[j]=word[j];
			}
		    }
		  
		  
		  if (DEBUG3)
		    fprintf(stderr,"testing left split of [%s]: [%s]\n",
			    word,left);
		  
		  inlex=0;
		  thishash=sdbm(left);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if (thishash==hash[k])
			inlex=1;
		    }
		  if (!inlex)
		    for (k=0; ((k<nrdoclex)&&(!inlex)); k++)
		      {
			if (left[0]==doclexicon[k][0])
			  {
			    if (strcmp(left,doclexicon[k])==0)
			      {
				inlex=1;
			      }
			  }
		      }
		  if (inlex)
		    {
		      
		      if (DEBUG3)
			fprintf(stderr,"found left split of [%s]: [%s]\n",
				word,left);
		      
		      if ((i<wordlen)&&(word[i]=='-'))
			i++;
		      if ((i<wordlen)&&(word[i]==')'))
			i++;
		      
		      strcpy(right,"");
		      for (j=i; j<wordlen; j++)
			{
			  strcat(right," ");
			  right[j-i]=word[j];
			}
		      inlex=0;
		      
		      if (DEBUG3)
			fprintf(stderr,"testing split of [%s] into [%s] [%s]\n",
				word,left,right);
		      
		      thishash=sdbm(right);
		      for (k=0; ((k<nrlex)&&(!inlex)); k++)
			{
			  if (thishash==hash[k])
			    inlex=1;
			}
		      if (!inlex)
			for (k=0; ((k<nrdoclex)&&(!inlex)); k++)
			  {
			    if (right[0]==doclexicon[k][0])
			      {
				if (strcmp(right,doclexicon[k])==0)
				  {
				    inlex=1;
				  }
			      }
			  }
		      
		      // may still be a chance of an infix -s-, -e-, -en-
		      
		      if ((!inlex)&&
			  ((word[i]=='s')||
			   (word[i]=='e')))
			{
			  m=i;
			  i++;
			  if ((word[i-1]=='e')&&
			      (word[i]=='n'))
			    i++;
			  
			  strcpy(right,"");
			  for (j=i; j<wordlen; j++)
			    {
			      strcat(right," ");
			      right[j-i]=word[j];
			    }
			  inlex=0;
			  
			  if (DEBUG3)
			    fprintf(stderr,"testing split of [%s] into [%s] [%s]\n",
				    word,left,right);
			  
			  thishash=sdbm(right);
			  for (k=0; ((k<nrlex)&&(!inlex)); k++)
			    {
			      if (thishash==hash[k])
				{
				  inlex=1;
				}
			    }
			  if (!inlex)
			    for (k=0; ((k<nrdoclex)&&(!inlex)); k++)
			      {
				if (right[0]==doclexicon[k][0])
				  {
				    if (strcmp(right,doclexicon[k])==0)
				      {
					inlex=1;
				      }
				  }
			      }
			  i=m;
			}
		      
		      if (inlex)
			{
			  if (DEBUG2)
			    fprintf(stderr,"found a split of [%s] into [%s] [%s]\n",
				    word,left,right);
			  problem=0;
			}
		    }
		}
	    }
	}
      fprintf(stdout,"%s",
	      word);
      
      if (problem)
	{
	  fprintf(stdout," ERROR");
	  if (DEBUG)
	    fprintf(stderr,"%s considered to be a non-word\n",
		    word);
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
