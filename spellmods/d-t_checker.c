/* d-t spellmod 

   syntax: d-t_checker <threshold> <d-t list> <valkuil-inst>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include "sockhelp.h"
#include<unistd.h>

#define PORT "2000"
#define MACHINE "localhost"
#define NRFEAT 7
#define MINOCC 5.
#define DEBUG 0

int main(int argc, char *argv[])
{
  FILE *bron;
  float distweight[1024];
  float total,max,threshold;
  int  i,j,nrddt,mid,sock,connected,nrdist,maxnr;
  char **dtwords;
  char **dwords;
  char thisdtword[1024];
  char thisdword[1024];
  char locaps[1024];
  char classifyline[32768];
  char line[32768];
  char buff[32768];
  char feats[NRFEAT][1024];
  char *part;
  char category[1024];
  char dtmatch;

  sscanf(argv[1],"%f",&threshold);
  if ((threshold<0.5)||
      (threshold>1.0))
    {
      fprintf(stderr,"[d-t_checker] ERROR: threshold value not between 0.5 and 1.0\n");
      exit(1);
    }

  bron=fopen(argv[2],"r");
  nrddt=0;
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      nrddt++;
      fgets(line,32768,bron);
    }
  fclose(bron);

  dtwords=malloc(nrddt*sizeof(char*));
  dwords=malloc(nrddt*sizeof(char*));

  bron=fopen(argv[2],"r");
  for (i=0; i<nrddt; i++)
    {
      fscanf(bron,"%s %s ",
	     thisdtword,thisdword);
      dtwords[i]=malloc((strlen(thisdtword)+1)*sizeof(char));
      strcpy(dtwords[i],thisdtword);
      dwords[i]=malloc((strlen(thisdword)+1)*sizeof(char));
      strcpy(dwords[i],thisdword);
    }
  fclose(bron);

  if (DEBUG)
    fprintf(stderr,"read %d d-t triggers from %s\n",
	    nrddt,argv[2]);

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

  // tell the Timbl server to use the d-t base
  sock_puts(sock,"base d-t\n");

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
	  strcpy(locaps,"");
	  for (i=0; i<strlen(feats[mid]); i++)
	    {
	      strcat(locaps," ");
	      if ((feats[mid][i]>='A')&&
		  (feats[mid][i]<='Z'))
		locaps[i]=feats[mid][i]+32;
	      else
		locaps[i]=feats[mid][i];
	    }

	  dtmatch=0;
	  i=0;
	  while ((i<nrddt)&&
		 (!dtmatch))
	    {
	      if ((strcmp(feats[mid],dtwords[i])==0)||
		  (strcmp(locaps,dtwords[i])==0)||
		  (strcmp(feats[mid],dwords[i])==0)||
		  (strcmp(locaps,dwords[i])==0))
		dtmatch=1;
	      if (!dtmatch)
		i++;
	    }

	  fprintf(stdout,"%s",
		  feats[mid]);
	  if (dtmatch)
	    {
	      // call Timbl
	      strcpy(classifyline,"c ");
	      for (j=0; j<NRFEAT; j++)
		{
		  if (j!=mid)
		    strcat(classifyline,feats[j]);
		  else
		    strncat(classifyline,feats[j],strlen(feats[j])-1);
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
		    fprintf(stderr," - max %6.3f certainty\n",
			    (max/total));
		  
		  if ((max/total>=threshold)&&
		      (total>MINOCC))
		    {
		      if (category[0]!=feats[mid][strlen(feats[mid])-1])
			{
			  fprintf(stdout," ");
			  if (category[0]=='t')
			    {
			      for (j=0; j<strlen(feats[mid])-1; j++)
				fprintf(stdout,"%c",
					feats[mid][j]);
			      fprintf(stdout,"t");
			      fprintf(stderr,"correcting %s to ",
				      feats[mid]);
			      for (j=0; j<strlen(feats[mid])-1; j++)
				fprintf(stderr,"%c",
					feats[mid][j]);
			      fprintf(stderr,"t");
			    }
			  else
			    {
			      for (j=0; j<strlen(feats[mid])-1; j++)
				fprintf(stdout,"%c",
					feats[mid][j]);
			      fprintf(stdout,"d");
			      fprintf(stderr,"correcting %s to ",
				      feats[mid]);
			      for (j=0; j<strlen(feats[mid])-1; j++)
				fprintf(stderr,"%c",
					feats[mid][j]);
			      fprintf(stderr,"d");			      
			    }
			}
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
