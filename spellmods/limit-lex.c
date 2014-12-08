/* limit-lex -- limit lexicon: economical preprocessing step before turning the lexicon into a trie */

#include<stdio.h>
#include<string.h>

int main(int argc, char *argv[])
{
  FILE *bron;
  char line[65536];
  char word[4096];
  char *part;
  int  i,withletters;
  float letterratio;
  unsigned long freq;
  char *result;

  setbuf(stdout,NULL);

  bron=fopen(argv[1],"r");
  result=fgets(line,65536,bron);
  while (!feof(bron))
    {

      part=strtok(line," \n");
      sscanf(part,"%ld",&freq);

      part=strtok(NULL," \n");
      strcpy(word,part);

      withletters=0;
      for (i=0; i<strlen(word); i++)
        if (((word[i]>='A')&&(word[i]<='Z'))||
            ((word[i]>='a')&&(word[i]<='z')))
          withletters++;

      letterratio=(1.*withletters)/(1.*strlen(word));

      if (((freq>1000)&&
	   (strlen(word)>=3)&&
	   (letterratio>=0.25))||
	  ((freq>=20)&&
	   (strlen(word)>=3)&&
	   (letterratio>=0.5)))
	{
	  fprintf(stdout,"%ld %s\n",
		  freq,word);
	}
      result=fgets(line,65536,bron);
    }
  fclose(bron);
}
