/* check-lexicon-against-errors <errorlist> <lexicon> */

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

int main(int argc, char *argv[])
{
  FILE *bron;
  char line[32768];
  char **error;
  char **correct;
  char *part;
  char readstr[1024];
  int  i,j,nrerrors,readfreq,counter=0;
  char err;

  nrerrors=0;
  bron=fopen(argv[1],"r");
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      nrerrors++;
      fgets(line,32768,bron);
    }
  fclose(bron);

  fprintf(stderr,"reading %d errors\n",
	  nrerrors);

  error=malloc(nrerrors*sizeof(char*));
  correct=malloc(nrerrors*sizeof(char*));

  bron=fopen(argv[1],"r");
  for (i=0; i<nrerrors; i++)
    {
      fscanf(bron,"%s ",readstr);

      part=strtok(readstr,"~");
      correct[i]=malloc((strlen(part)+1)*sizeof(char));
      strcpy(correct[i],part);

      part=strtok(NULL,"~");
      error[i]=malloc((strlen(part)+1)*sizeof(char));
      strcpy(error[i],part);
    }
  fclose(bron);

  fprintf(stderr,"checking lexicon...\n");
  
  bron=fopen(argv[2],"r");
  while (!feof(bron))
    {
      fscanf(bron,"%d %s ",
	     &readfreq,readstr);
      err=0;
      for (i=0; ((i<nrerrors)&&(!err)); i++)
	{
	  if (readstr[0]==error[i][0])
	    if (strcmp(readstr,error[i])==0)
	      {
		fprintf(stderr,"error in lexicon? %s\n",
			readstr);
		err=1;
	      }
	}
      counter++;
      if (counter%10000==0)
	{
	  fprintf(stderr,"%d entries processed\n",
		  counter);
	}

      if (!err)
	fprintf(stdout,"%d %s\n",
		readfreq,readstr);
    }
  fclose(bron);
}
