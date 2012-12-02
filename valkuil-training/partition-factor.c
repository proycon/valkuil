/* partition - randomize and make one out of n-fold partitions 
   syntax: partition <datafile> <n> <partition number[0-4]> <seed> */

#include<stdio.h>
#include<string.h>
#include<stdlib.h>
#include<stddef.h>
#include<time.h>

#define TOPRAND 999999999
#define LINELEN 65536

int main(int argc, char *argv[])
{ 
  FILE *bron,*doel,*train,*test;
  char trainnaam[32768];
  char testnaam[32768];
  char line[LINELEN];
  int  n,tel,seed,partnr;

  if (argc!=5)
    {
      fprintf(stderr,"\nsyntax error. Usage: partition <datafile> <n> <partition number[0-(n-1)]> <seed>\n\n");
      exit(1);
    }

  bron=fopen(argv[1],"r");
  if (bron==NULL)
    {
      fprintf(stderr,"%s: no such file\n\n",argv[1]);
      exit(1);
    }

  sscanf(argv[2],"%d",&n);
  if (n<0)
    {
      fprintf(stderr,"n must be greater than zero\n\n");
      exit(1);
    }

  sscanf(argv[3],"%d",&partnr);
  if ((partnr<0)||(partnr>(n-1)))
    {
      fprintf(stderr,"partition number must be in range [0-(n-1)]\n\n");
      exit(1);
    }

  sscanf(argv[4],"%d",&seed);

  fprintf(stderr,"\n PARTITION - Antal May 2001\n\n");
  fprintf(stderr,"randomizing with seed %d\n",seed);
  
  srand48((unsigned long int) seed);
  system("rm -rf effe >/dev/null 2>&1\n");
  doel=fopen("effe","w");
  fgets(line,LINELEN,bron);
  while (!feof(bron))
  { 
    fprintf(doel,"%d %s",(int) lrand48()%seed,line);
    fgets(line,LINELEN,bron);
  }
  fclose(doel);
  fclose(bron);
  
  system("nice sort -n effe -o effe\n");
  system("cut -d\" \" -f2- effe > effe2\n");
  system("rm effe\n");

  fprintf(stderr,"generating partition %d\n",
	  partnr);
  tel=0;
  bron=fopen("effe2","r");
  sprintf(trainnaam,"%s.%d.data",
	  argv[1],partnr);
  sprintf(testnaam,"%s.%d.test",
	  argv[1],partnr);
  train=fopen(trainnaam,"w");
  test=fopen(testnaam,"w");
  fgets(line,LINELEN,bron);
  while (!feof(bron))
    { 
      if (strlen(line)>1)
	{ 
	  if (tel==partnr)
	    fputs(line,test);
          else
	    fputs(line,train);
	}
      tel++;
      if (tel==n)
	tel=0;
      fgets(line,LINELEN,bron);

    }
  fclose(test);
  fclose(train);
  fclose(bron);

  system("rm effe2\n");
  fprintf(stderr,"ready.\n\n");

  return 0;
}
