/* soundalike spellmod

   a checker that looks for similarly sounding words in the lexicon 

   args: soundalike_checker <lexicon> <1-word-per-line>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MINFREQTHRESHOLD 50
#define MINLENGTH 3
#define DEBUG3 0
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
  char altword[1024];
  char thealtword[1024];
  unsigned long thishash;
  int  i,k,nrlex=0,readnr,wordlen;
  FILE *context;
  char inlex,altsound;

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

  context=fopen(argv[2],"r");
  while (!feof(context))
    {
      fscanf(context,"%s ",word);

      wordlen=strlen(word);

      // is there an obvious soundalike alternative?
      altsound=0;
      if (strlen(word)>=MINLENGTH)
	if ((strstr(word,"ei"))||
	    (strstr(word,"ij"))||
	    (strstr(word,"au"))||
	    (strstr(word,"ou"))||
	    (strstr(word,"g"))||
	    (strstr(word,"ch"))||
	    (strstr(word,"ks"))||
	    (strstr(word,"x")))
	  altsound=1;

      if (altsound)
	{
	  inlex=0;
	  thishash=sdbm(word);
	  for (k=0; ((k<nrlex)&&(!inlex)); k++)
	    {
	      if (thishash==hash[k])
		{
		  inlex=1;
		  if (DEBUG3)
		    fprintf(stderr,"word [%s] in lexicon, with frequency %ld\n",
			    word,freqs[k]);
		}
	    }

	  // if the word itself does not exist, let's look for a soundalike
	  if (!inlex)
	    {
	      if (strstr(word,"ei"))
		{
		  strcpy(altword,word);
		  i=0;
		  while ((i<strlen(word))&&
			 !((word[i]=='e')&&
			   (word[i+1]=='i')))
		    i++;
		  if (i<strlen(word))
		    {
		      altword[i]='i';
		      altword[i+1]='j';
		    }

		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }
		}

	      if (strstr(word,"ij"))
		{
		  strcpy(altword,word);
		  i=0;
		  while ((i<strlen(word))&&
			 !((word[i]=='i')&&
			   (word[i+1]=='j')))
		    i++;
		  if (i<strlen(word))
		    {
		      altword[i]='e';
		      altword[i+1]='i';
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}

	      if (strstr(word,"au"))
		{
		  strcpy(altword,word);
		  i=0;
		  while ((i<strlen(word))&&
			 !((word[i]=='a')&&
			   (word[i+1]=='u')))
		    i++;
		  if (i<strlen(word))
		    {
		      altword[i]='o';
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}

	      if (strstr(word,"ou"))
		{
		  strcpy(altword,word);
		  i=0;
		  while ((i<strlen(word))&&
			 !((word[i]=='o')&&
			   (word[i+1]=='u')))
		    i++;
		  if (i<strlen(word))
		    {
		      altword[i]='a';
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}
	      
	      if (strstr(word,"g"))
		{
		  strcpy(altword,"");
		  for (i=0; i<strlen(word); i++)
		    {
		      if (word[i]=='g')
			strcat(altword,"ch");
		      else
			{
			  strcat(altword," ");
			  altword[strlen(altword)-1]=word[i];
			}
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}

	      if (strstr(word,"ch"))
		{
		  strcpy(altword,"");
		  for (i=0; i<strlen(word); i++)
		    {
		      if ((word[i]=='c')&&
			  (word[i+1]=='h'))
			{
			  strcat(altword,"g");
			  i++;
			}
		      else
			{
			  strcat(altword," ");
			  altword[strlen(altword)-1]=word[i];
			}
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}

	      if (strstr(word,"x"))
		{
		  strcpy(altword,"");
		  for (i=0; i<strlen(word); i++)
		    {
		      if (word[i]=='x')
			strcat(altword,"ks");
		      else
			{
			  strcat(altword," ");
			  altword[strlen(altword)-1]=word[i];
			}
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}

	      if (strstr(word,"ks"))
		{
		  strcpy(altword,"");
		  for (i=0; i<strlen(word); i++)
		    {
		      if ((word[i]=='k')&&
			  (word[i+1]=='s'))
			{
			  strcat(altword,"x");
			  i++;
			}
		      else
			{
			  strcat(altword," ");
			  altword[strlen(altword)-1]=word[i];
			}
		    }
		  // does altword occur?
		  if (DEBUG2)
		    fprintf(stderr,"checking if soundalike word %s exists\n",
			    altword);
		  thishash=sdbm(altword);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if ((thishash==hash[k])&&
			  (freqs[k]>MINFREQTHRESHOLD))
			{
			  inlex=1;
			  strcpy(thealtword,altword);
			  if (DEBUG2)
			    fprintf(stderr,"found soundalike word in lexicon: %s\n",
				   thealtword);
			}
		    }

		}

	      if (!inlex)
		altsound=0;
	    }
	  else
	    altsound=0;
	}
      
      fprintf(stdout,"%s",
	      word);
      
      if ((altsound)&&
	  (strlen(thealtword)>0))
	{
	  fprintf(stdout," %s",
		  thealtword);

	  if (DEBUG)
	    {
	      fprintf(stderr,"soundalike for [%s]: [%s]\n",
		      word,thealtword);
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
