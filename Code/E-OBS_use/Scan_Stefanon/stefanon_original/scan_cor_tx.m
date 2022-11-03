
scan_size = 15
quantieme = 95
pourcent = 0.6
data = 'tx';

scan(data,scan_size,quantieme,pourcent)

function scan(data,scan_size,quantieme,pourcent)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

path_data = '/home/ajeze/Documents/DetectionCanicule/ano/' ;
path_data_seuil = '/home/ajeze/Documents/DetectionCanicule/quantile/' ;
path_data_out = pwd; 
path = pwd;
an = 69;
var = 0;

load /home/ajeze/Documents/DetectionCanicule/ano/tx_JJA.mat
%cat(2,path_data,data);
%eval(['  load ' file '  '])
whos

siz=size(var);
ano = reshape(var,length(lat)*length(lon),length(temps));
clear buffer var

scan_lon = scan_size;
scan_lat = scan_size;
quantieme 
pourcent


calc_red = 0;
%if calc_red ==1

   load /home/ajeze/Documents/DetectionCanicule/quantile/tx95.mat
   %cat(2,path_data_seuil,data,int2str(quantieme))
   %eval(['  load ' file '  '])
   seuil = reshape(var,length(lat)*length(lon),length(temps));
   whos
   clear var
   ano_scale = zeros(size(ano));
   ano_scale = ano - seuil;
   clear seuil
%red, on ne garde les anomalies que pour les jours où ano>T95, sinon on met tout à zéro
   for j = 1 : siz(3)
      for i = 1 :  siz(1) * siz(2)
         %if( and( (ano_scale(i,j) >=  1),(lsm(i)==1) ))
         if(ano_scale(i,j) >=  0) 
            red(i,j) = ano(i,j);
         else
            red(i,j) = 0;
         end
      end
   end
   red = reshape(red,siz(1),siz(2),siz(3));
   eval([' save -v7.3 red_' int2str(quantieme) '_scale_tx.mat red ; '])
%else
%   eval([' load   red_' int2str(quantieme) '_scale.mat ; '])
%end
display('seuil calc');

clear ano_scale
%land sea mask EOBS
load /home/ajeze/Documents/DetectionCanicule/mask/lsm.mat
whos
tt = 1;
mem = zeros(siz(3),1);
mem(1) = temps(1);
compress = zeros(siz(1),siz(2),1);
weight = cos(pi*lat/180);
%on fait l'opération de scan de chaque zone, pour déterminer les dates des vagues de chaleur qui sont stockées dans date
for t = 1 : length(temps)
   for i = 1 : length(lon)/2
      if(i*2+scan_lon) > length(lon)
      %if(i+scan_lon) > length(lon)
         break
      end
      for j = 1 : length(lat)/2
          if(j*2+scan_lat) > length(lat)
          %if(j+scan_lat) > length(lat)
             break
          end
          cpt = 0;
          sea_cpt = 0;
	  seuil = 0;
          for ii = 1 : scan_lon
             for jj = 1 : scan_lat
                if( red((i-1)*2+ii,(j-1)*2+jj,t)>0 )
                   cpt = cpt +  weight((j-1)*2+jj);
                end
                if (lsm((i-1)*2+ii,(j-1)*2+jj)==0)
                   sea_cpt = sea_cpt + weight((j-1)*2+jj); 
                end
             end
          end
          %if (cpt > floor((scan_lon*scan_lat-sea_cpt)*pourcent))
          if (cpt > round((sum(scan_lon*weight((j-1)*2+1:(j-1)*2+scan_lat))-sea_cpt)*pourcent))
             compress((i-1)*2+1:(i-1)*2+scan_lon,(j-1)*2+1:(j-1)*2+scan_lat,tt) = red((i-1)*2+1:(i-1)*2+scan_lon,(j-1)*2+1:(j-1)*2+scan_lat,t);
             date(tt) = temps(t);
             indice(tt) = t;
             %cpt  
	     %round((sum(scan_lon*weight((j-1)*2+1:(j-1)*2+scan_lat))-sea_cpt)*pourcent)
             %i
             %j
             %pause
             datestr(date(tt));
             if(mem(tt) ~= temps(t))
                mem(tt:tt+1) = temps(t);
                tt = tt + 1;
             end
          end
      end
   end
end
t
whos


compress = reshape(compress,siz(1)*siz(2),size(compress,3));

file_out = cat(2,path_data_out,'/scan_scale',data,'_',int2str(scan_size),'_',int2str(pourcent*10),'_',int2str(quantieme),'_cor');
%eval(['save -v7.3 ' file_out ' date compress seuil ano temps lon lat siz red quantieme pourcent scan_lon scan_lat indice ']);
eval(['save -v7.3 ' file_out ' date compress ano temps lon lat siz red quantieme pourcent scan_lon scan_lat indice ']);

display('save done');
end


