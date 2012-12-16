/* abstaining-classifier */

#include<stdio.h>
#include<string.h>

#define NRFEAT 8
#define MINOCC 10.

int main(int argc, char *argv[])
{
  FILE  *bron;
  char  feats[NRFEAT][65536];
  char  line[65536];
  char  *part;
  int   i,tot,ttot,cor,tcor;
  float thres,sum,this,peak;
  char  match=0;

  tot=cor=tcor=ttot=0;

  sscanf(argv[1],"%f",&thres);

  bron=fopen(argv[2],"r");
  fgets(line,65536,bron);
  while (!feof(bron))
    {
      //fprintf(stderr,"\nline: %s",
      //      line);

      part=strtok(line," \n");
      for (i=0; i<NRFEAT; i++)
	{
	  strcpy(feats[i],part);
	  part=strtok(NULL," \n");
	}
      
      sum=0;
      peak=0.0;
      //part=strtok(NULL," \n");
      while ((part!=NULL)&&
	     (strcmp(part,"}")!=0))
	{
	  match=0;
	  part=strtok(NULL," \n");
	  if (strcmp(part,"}")!=0)
	    {
	      //fprintf(stderr,"comparing %s - %s\n",
	      //      part,feats[NRFEAT-1]);
	      if (strcmp(part,feats[NRFEAT-1])==0)
		match=1;
	      part=strtok(NULL," \n");
	      if (part[strlen(part)-1]==',')
		sscanf(part,"%f,",&this);
	      else
		sscanf(part,"%f",&this);
	      sum+=this;
	      if (match)
		{
		  peak=this;
		}
	    }
	}

      //fprintf(stderr,"peak %.0f - sum %.0f - div %f - thres %f \n",
      //    peak,sum,peak/sum,thres);

      if (strcmp(feats[NRFEAT-2],feats[NRFEAT-1])==0)
	{
	  cor++;
	  if (((peak/sum)>=thres)&&
	      (peak>MINOCC)&&
	      ((peak/sum)<1.0))
	    tcor++;
	}
      tot++;

      if (((peak/sum)>=thres)&&
	  (peak>MINOCC)&&
	  ((peak/sum)<1.0))
	ttot++;

      fgets(line,65536,bron);
    }
  fclose(bron);

  // fprintf(stderr,"overall accuracy %8.6f (%d out of %d)\n",
  //	  (1.*cor)/(1.*tot),cor,tot);
  fprintf(stderr,"%.3f\tabstaining: %6d out of %6d correct = %8.6f\n",
	  thres,tcor,ttot,(1.*tcor)/(1.*ttot));

}
