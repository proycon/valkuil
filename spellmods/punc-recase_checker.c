/* punc-recase spellmod 

   syntax: punc-recase_checker <threshold> <punc-recase-inst>

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
  int  i,j,sock,connected,nrdist,counter,defcon,maxnr,result;
  char classifyline[32768];
  char readbuffer[1024];
  char locap[1024];
  char buffer[NRFEAT][1024];
  char membuffer[NRFEAT+3][1024];
  char buff[32768];
  char timblbuffer[1024];
  char punc[NRFEAT][32];
  char cap[1024];
  char puncstring[1024];
  char *part;
  char category[1024];
  char realout[1024];
  char capped,ready;

  ready=0;
  defcon=maxnr=connected=result=0;

  sscanf(argv[1],"%f",&threshold);
  if ((threshold<0.5)||
      (threshold>1.0))
    {
      fprintf(stderr,"[punc-recase_checker] ERROR: threshold value not between 0.5 and 1.0\n");
      exit(1);
    }

  strcpy(puncstring,",.`'\"’‘!?:;()");

  // process text file (not prefab inst!)

  // first, start up communications with the Timbl server
  ignore_pipe();
  sock=make_connection(PORT,SOCK_STREAM,MACHINE);
  if (sock==-1)
    {
      fprintf(stderr,"the punc-recase server is not responding\n");
      exit(1);
    }
  else
    connected=1;

  // cut off the Timbl welcome message
  sock_gets(sock,buff,sizeof(buff)-1); 

  // cut off the Timbl base message
  sock_gets(sock,buff,sizeof(buff)-1); 

  // tell the Timbl server to use the punc-recase base
  sprintf(timblbuffer,"base punc-recase\n");
  sock_puts(sock,timblbuffer);

  // cut off the Timbl acknowledgement
  sock_gets(sock,buff,sizeof(buff)-1); 

  // initialize buffers
  strcpy(cap,"");
  for (i=0; i<NRFEAT; i++)
    {
      strcpy(membuffer[i],"_");
      strcpy(buffer[i],"_");
      strcpy(punc[i],"NP");
      strcat(cap," ");
      cap[i]='-';
    }

  bron=fopen(argv[2],"r");
  counter=0;
  while (!ready)
    {
      if (!feof(bron))
	{
	  result=fscanf(bron,"%s ",
			readbuffer);
	}
      else
	strcpy(readbuffer,"_");

      if ((counter>(NRFEAT/2)-1)&&
	  (defcon<=NRFEAT/2))
	{
	  
	  fprintf(stdout,"%s",
		  membuffer[(NRFEAT/2)-1]);
	  if (DEBUG)
	    fprintf(stderr,"original token: [%s]\n",
		    membuffer[(NRFEAT/2)-1]);
	}
      for (i=NRFEAT; i>0; i--)
	strcpy(membuffer[i],membuffer[i-1]);
      strcpy(membuffer[0],readbuffer);

      capped=0;
      if ((readbuffer[0]>='A')&&
          (readbuffer[0]<='Z'))
        capped=1;
      strcpy(locap,"");
      for (i=0; i<strlen(readbuffer); i++)
        {
          strcat(locap," ");
          if ((readbuffer[i]>='A')&&
              (readbuffer[i]<='Z'))
            locap[i]=readbuffer[i]+32;
          else
            locap[i]=readbuffer[i];
        }

      if (strstr(puncstring,readbuffer))
	{
	  strcpy(punc[NRFEAT-1],readbuffer);
	}
      else
	{
	  for (i=0; i<NRFEAT-1; i++)
	    {
	      strcpy(buffer[i],buffer[i+1]);
	      strcpy(punc[i],punc[i+1]);
	      cap[i]=cap[i+1];
	    }
	  strcpy(buffer[NRFEAT-1],locap);
	  if (capped)
	    cap[NRFEAT-1]='C';
	  else
	    cap[NRFEAT-1]='-';
	  strcpy(punc[NRFEAT-1],"NP");
      
	  if (DEBUG)
	    fprintf(stderr,"checking [%s]-[%c]-[%s]\n",
		    buffer[(NRFEAT/2)],
		    cap[(NRFEAT/2)],
		    punc[(NRFEAT/2)]);
	  
	  
	  if (counter>2)
	    {
	      if (strcmp(punc[(NRFEAT/2)],"NP")==0)
		{
		  if (DEBUG)
		    {
		      fprintf(stderr,"\nbuffer:");
		      for (i=0; i<NRFEAT; i++)
			fprintf(stderr," [%10s]",
				buffer[i]);
		      fprintf(stderr,"\n");
		      
		      fprintf(stderr,"cap:   ");
		      for (i=0; i<NRFEAT; i++)
			fprintf(stderr," [%10c]",
				cap[i]);
		      fprintf(stderr,"\n");
		      
		      fprintf(stderr,"punc:  ");
		      for (i=0; i<NRFEAT; i++)
			fprintf(stderr," [%10s]",
				punc[i]);
		      fprintf(stderr,"\n");
		    }
		  
		  
		  strcpy(classifyline,"c ");
		  
		  for (i=0; i<NRFEAT-1; i++)
		    {
		      strcat(classifyline,buffer[i]);
		      strcat(classifyline," ");
		    }
		  
		  if (strcmp(punc[2],"NP")!=0)
		    {
		      if (cap[3]!='-')
			{
			  strcat(classifyline,punc[2]);
			  strcpy(realout,punc[2]);
			  strcat(classifyline,"C\n");
			  strcat(realout,"C");
			}
		      else
			{
			  strcat(classifyline,punc[2]);
			  strcpy(realout,punc[2]);
			  strcat(classifyline,"\n");
			}
		    }
		  else
		    {
		      if (cap[3]!='-')
			{
			  strcat(classifyline,"C\n");
			  strcpy(realout,"C");
			}
		      else
			{
			  strcat(classifyline,"-\n");
			  strcpy(realout,"-");
			}
		    }
		  
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
			  fprintf(stderr,"distro of %d:",
				  nrdist);
			  for (i=0; i<nrdist; i++)
			    fprintf(stderr," %.0f",
				    distweight[i]);
			}
		      
		      max=0.0;
		      maxnr=0;
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
			  // (max/total<1.0)&&
			  (total>MINOCC))
			{
			  if ((strcmp(category,realout)!=0)&&
			      (strcmp(category,"-")!=0))
			    {
			      if (DEBUG)
				{
				  fprintf(stderr,"line: %s",
					  classifyline);
				  fprintf(stderr,"we have to do something: predicted %s is not actual %s\n",
					  category,realout);
				  fprintf(stderr,"correction: [%s]\n",
					  category);
				}
			      fprintf(stdout," %s",
				      category);
			    }
			}
		    }
		}
	    }
	}

      if ((counter>(NRFEAT/2)-1)&&
	  (defcon<=NRFEAT/2))
	{
	  fprintf(stdout,"\n");
	  if (DEBUG)
	    fprintf(stderr,"\n");
	}

      if (feof(bron))
        defcon++;
      if (defcon>(NRFEAT/2))
        ready=1;

      counter++;
    }
  fclose(bron);
  close(sock);

  return 0;
}
