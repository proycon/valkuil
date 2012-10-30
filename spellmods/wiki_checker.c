/* wiki spellmod 

   syntax: wiki_checker <threshold> <wiki list> <valkuil-inst>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include "sockhelp.h"
#include<unistd.h>

#define PORT "2000"
#define MACHINE "137.56.83.160"
#define NRFEAT 7
#define MINOCC 5.
#define DEBUG 0
#define MINLEN 4
#define MAXDIST 3.881010 // has to match on more than centre word

int main(int argc, char *argv[])
{
  FILE *bron;
  float distweight[1024];
  float total,max,threshold,distance;
  int  i,j,nrwiki,mid,sock,connected,nrdist,maxnr;
  char **wikiwords;
  char thiswikiword[1024];
  char classifyline[32768];
  char line[32768];
  char buff[32768];
  char feats[NRFEAT][1024];
  char *part;
  char category[1024];
  char wikimatch;

  sscanf(argv[1],"%f",&threshold);
  if ((threshold<0.5)||
      (threshold>1.0))
    {
      fprintf(stderr,"[wiki_checker] ERROR: threshold value not between 0.5 and 1.0\n");
      exit(1);
    }

  bron=fopen(argv[2],"r");
  nrwiki=0;
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      nrwiki++;
      fgets(line,32768,bron);
    }
  fclose(bron);

  wikiwords=malloc(nrwiki*sizeof(char*));

  bron=fopen(argv[2],"r");
  for (i=0; i<nrwiki; i++)
    {
      fscanf(bron,"%s ",
	     thiswikiword);
      wikiwords[i]=malloc((strlen(thiswikiword)+1)*sizeof(char));
      strcpy(wikiwords[i],thiswikiword);
    }
  fclose(bron);

  if (DEBUG)
    fprintf(stderr,"read %d wiki triggers from %s\n",
	    nrwiki,argv[2]);

  // process inst file

  // first, start up communications with the Timbl server
  ignore_pipe();
  sock=make_connection(PORT,SOCK_STREAM,MACHINE);
  if (sock==-1)
    {
      fprintf(stderr,"the confusible server is not responding\n");
      exit(1);
    }
  else
    connected=1;

  // cut off the Timbl welcome message
  sock_gets(sock,buff,sizeof(buff)-1); 

  // cut off the Timbl base message
  sock_gets(sock,buff,sizeof(buff)-1); 

  // tell the Timbl server to use the d-dt base
  sock_puts(sock,"base wiki\n");

  // cut off the Timbl acknowledgement
  sock_gets(sock,buff,sizeof(buff)-1); 
  
  mid=NRFEAT/2;
  bron=fopen(argv[3],"r");
  fgets(line,32768,bron);
  while (!feof(bron))
    {

      part=strtok(line," \n");
      for (i=0; ((part!=NULL)&&(i<NRFEAT)); i++)
	{
	  strcpy(feats[i],part);
	  part=strtok(NULL," \n");
	}

      if (!((strcmp(feats[mid],"<begin>")==0)||
            (strcmp(feats[mid],"<end>")==0)))
        {

	  wikimatch=0;
	  i=0;
	  while ((i<nrwiki)&&
		 (!wikimatch))
	    {
	      if (strcmp(feats[mid],wikiwords[i])==0)
		wikimatch=1;
	      i++;
	    }
	  
	  fprintf(stdout,"%s",
		  feats[mid]);
	  
	  if ((wikimatch)&&
	      (strlen(feats[mid])>=MINLEN))
	    {
	      // call Timbl
	      strcpy(classifyline,"c ");
	      for (j=0; j<NRFEAT; j++)
		{
		  strcat(classifyline,feats[j]);
		  strcat(classifyline," ");
		}
	      strcat(classifyline,"?\n");
	      
	      if (DEBUG)
		fprintf(stderr,"\ncalling Timbl with %s",
			classifyline);
	      
	      sock_puts(sock,classifyline);
	      sock_gets(sock,buff,sizeof(buff));
	      
	      if (DEBUG)
		fprintf(stderr,"getting back: %s\n",
			buff);
	      
	      part=strtok(buff," \n");
	      part=strtok(NULL," \n");
	      strcpy(category,"");
	      for (j=1; j<strlen(part)-1; j++)
		{
		  strcat(category," ");
		  category[j-1]=part[j];
		}
	      while ((part!=NULL)&&
		     (strcmp(part,"{")!=0))
		part=strtok(NULL," \n");
	      
	      if (part!=NULL)
		{
		  nrdist=0;
		  while ((part!=NULL)&&
			 (strcmp(part,"}")!=0))
		    {
		      part=strtok(NULL," \n");
		      if (strcmp(part,"}")!=0)
			{
			  part=strtok(NULL," \n");
			  if (part[strlen(part)-1]==',')
			    sscanf(part,"%f,",&distweight[nrdist]);
			  else
			    sscanf(part,"%f",&distweight[nrdist]);
			  nrdist++;
			}
		    }

		  // read distance
		  if (part!=NULL)
		    {
		      part=strtok(NULL," \n");
		      part=strtok(NULL," \n");
		      sscanf(part,"{%f}",&distance);
		    }

		  if (DEBUG)
		    {
		      fprintf(stderr,"distro of %d: ",
			      nrdist);
		      for (i=0; i<nrdist; i++)
			fprintf(stderr," %9.4f",
				distweight[i]);
		    }
		  max=0.0;
		  total=0.0;
		  for (i=0; i<nrdist; i++)
		    {
		      total+=distweight[i];
		      if (distweight[i]>max)
			{
			  max=distweight[i];
			  maxnr=i;
			}
		    }
		  
		  if (DEBUG)
		    {
		      fprintf(stderr," - max %6.3f certainty\n",
			      (max/total));
		      fprintf(stderr,"distance: %f\n",
			      distance);
		    }
		  
		  if ((max/total>=threshold)&&
		      (total>MINOCC)&&
		      (distance<MAXDIST))
		    {
		      if (DEBUG)
			fprintf(stderr,"[wiki_checker] correcting [%s] to [%s]\n",
				feats[mid],category);
		      fprintf(stdout," %s",
			      category);
		    }
		}
	    }
	  fprintf(stdout,"\n");
	}
      fgets(line,32768,bron);
    }
  fclose(bron);
  close(sock);

  return 0;
}
