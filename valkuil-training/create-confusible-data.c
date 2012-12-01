/* create-confusible-data

   create-confusible-data <conf1> <conf2> <tokenizedcorpus>

 */

#include<stdio.h>
#include<string.h>

#define WINDOW 7

int main(int argc, char *argv[])
{
  FILE *bron;
  char feats[WINDOW][65536];
  char word[65536];
  char conf1[65536];
  char conf2[65536];
  char conf1caps[65536];
  char conf2caps[65536];
  int  i,mid;
  
  strcpy(conf1,argv[1]);
  strcpy(conf2,argv[2]);

  strcpy(conf1caps,conf1);
  strcpy(conf2caps,conf2);

  if ((conf1[0]>='a')&&(conf1[0]<='z'))
    conf1caps[0]-=32;

  if ((conf2[0]>='a')&&(conf2[0]<='z'))
    conf2caps[0]-=32;

  for (i=0; i<WINDOW; i++)
    strcpy(feats[i],"_");

  mid=WINDOW/2;

  bron=fopen(argv[3],"r");
  while (!feof(bron))
    {
      fscanf(bron,"%s ",
	     word);
      for (i=0; i<WINDOW-1; i++)
	strcpy(feats[i],feats[i+1]);
      strcpy(feats[WINDOW-1],word);

      if ((strcmp(feats[mid],conf1)==0)||
	  (strcmp(feats[mid],conf1caps)==0)||
	  (strcmp(feats[mid],conf2)==0)||
	  (strcmp(feats[mid],conf2caps)==0))
	{
	  for (i=0; i<WINDOW; i++)
	    if (i!=mid)
	      fprintf(stdout,"%s ",
		      feats[i]);
	  fprintf(stdout,"%s\n",
		  feats[mid]);
	}
    }
  fclose(bron);
}
