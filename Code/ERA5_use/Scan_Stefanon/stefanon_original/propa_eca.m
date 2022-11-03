function [nb_beg,nb_end,ind_beg,ind_end,nb_event]=propa(red,indice,date,freq_cut,recover_area)

%load scan_scale_95_14_66.mat
freq_cut = 1;
recover_area = 0.4;

clear class*
red_temp = red(:,:,indice);
clear red
ind=find(red_temp ~=0);
test = zeros(size(red_temp));
test(ind) = 1;
 
clear ep date_* ind_* nb* red_temp ind
nb_event(1:100) = 0;
nb_beg = 0;
nb_end = 0;
cpt = 1;
compt = 1;
ii=1;
propa = 0;
for i = 2:length(indice)
   dif = squeeze(test(:,:,i)) + squeeze(test(:,:,i-1));
   ind_a =find(test(:,:,i) == 1);
   ind_b =find(test(:,:,i-1) == 1 );
   ind_c =find(dif(:,:) == 2);
   if length(ind_c)/max(length(ind_a),length(ind_b)) > recover_area
      if (date(i) - date(i-1)) > freq_cut
           nb_beg(compt) = date(i-cpt);
           ind_beg(compt) = i-cpt;
           nb_end(compt) = date(i-1);
           ind_end(compt) = i-1;
           nb_event(cpt) = nb_event(cpt) + 1;
           compt = compt + 1;
           cpt = 1;
      else      
           cpt = cpt +1;
      end
      propa = 1;
      date_propa(ii) = date(i);
      ii=ii+1;
   else
      %if and( ((date(i) - date(i-1)) < freq_cut), propa == 1)
      if and( (cpt >= freq_cut), propa == 1)
           nb_beg(compt) = date(i-cpt);
           ind_beg(compt) = i-cpt;
           nb_end(compt) = date(i-1);
           ind_end(compt) = i-1;
           nb_event(cpt) = nb_event(cpt) + 1;
           compt = compt + 1;           
           cpt = 1;
           propa = 0;
      end
      cpt = 1;      
      propa = 0;
   end
   clear ind_a ind_b ind_c
end

%STOP HERE, go to prep_tree

htw_dates=[nb_beg;nb_end;nb_end-nb_beg+1]; 
fileID = fopen('heatwaves_days.txt','w');
fprintf(fileID,'First_day Last_day Duration\n\n');
fprintf(fileID,'%d %d %d\n',htw_dates);
fclose(fileID);

#post_process = 0;
#if post_process == 1

addpath('/home/ajeze/Documents/DetectionCanicule/m_map')
m_proj('miller','long',[lon(1) lon(length(lon))],'lat',[lat(1) lat(length(lat))]);
ano=reshape(ano,siz(1),siz(2),siz(3));
ep=zeros(siz(1),siz(2),length(ind_beg));
 compress = ano(:,:,indice);
 for i = 1 :length(ind_beg)
    ep(:,:,i) = squeeze(mean(compress(:,:,ind_beg(i):ind_end(i)),3)); 
 end
 ma = 0;
 mi = 0;
 for i=1:size(ep,1)
    mi= min(min(min(ep(:,:,i))),mi);
    ma= max(max(max(ep(:,:,i))),ma);   
 end
   
  for i=1:size(ep,1)
      figure(1)
      [H,h]=m_contourf(lon,lat,squeeze(ep(:,:,i)));hold on 
      m_coast('color',[0,0,0]);hold on
      m_grid('box','fancy');hold on
      caxis([mi ma])
      colorbar
      title({datestr(nb_beg(i)),datestr(nb_end(i))});
      xlabel(i)
      %saveName = (['propa_red', num2str(i)]);
      %saveas(gcf, saveName, 'jpg');
      pause%(1)
      close(1)
  end

ep = reshape(ep,size(ep,1),siz(2)*siz(3));
nb_class = 12;
for i= 4:12
 class = kmeans(ep,i,'display','iter','replicates',10,'emptyaction','drop');
    eval(['class_' int2str(i) '=class; ']);
end
ep = reshape(ep,size(ep,1),siz(2),siz(3));



save -v7.3 file_out ep ind_beg nb_beg ind_end nb_end lon lat temps
save -v7.3 file_out_2 compress date indice lon lat temps

 ma = 0;
 mi = 0;
 for ii=4:nb_class
      eval(['class= class_' int2str(ii) '; ']);
       j=0;
 for i=1:ii
    eval([' event_' int2str(i) '=  squeeze(mean(ep(ind,:,:))); '])
    eval(['ma = max(max(max(event_' int2str(i) ' )),ma); '])
    eval(['mi = min(min(min(event_' int2str(i) ' )),mi); '])
 end
 end
 
  for ii=4:nb_class
figure(ii)
 for i=1:ii
    eval([' event_' int2str(i) '=  squeeze(mean(ep(ind,:,:))); '])
    eval(['ma = max(max(max(event_' int2str(i) ' )),ma); '])
    eval(['mi = min(min(min(event_' int2str(i) ' )),mi); '])
 end
  for i=1:ii
      if or(or(ii == 3,ii == 8), ii == 7)
          subplot(ceil(sqrt(ii)),ceil(sqrt(ii)),i);
      else
          subplot(ceil(sqrt(ii)),floor(sqrt(ii)),i);
      end
      eval([' [H,h]=m_contourf(lon,lat,event_' int2str(i) ');hold on '])
      m_coast('color',[0,0,0]);hold on
      m_grid('box','fancy');hold on
      caxis([mi ma])
      colorbar
      title(length(find(class==i)));
  end
  %[ax,h3]=suplabel('Modes with threshold, ncep'); 
  %set(h3,'FontSize',15)
  end 
 
  
  
  
  
sum(nb_end-nb_beg)
cpt = 1;
compt =1;
for i = 1 :length(nb_beg)
    while(hw(cpt)<= nb_beg(i))
        cpt = cpt +1;
        if cpt > length(hw)
           break
        end
    end
    if cpt > length(hw)
         break
    end
    while and( (hw(cpt) >= nb_beg(i)  ),   (hw(cpt) <= nb_end(i)) )
    cpt = cpt+1;
    compt = compt+1;
    if cpt > length(hw)
        break
    end
    end
end
(compt-1)*100/length(hw)

cpt = 1;
compt =1;
for i = 1 :length(nb_beg)
    while(date(cpt)<= nb_beg(i))
        cpt = cpt +1;
        if cpt > length(hw)
           break
        end
    end
    if cpt > length(hw)
         break
    end
    while and( (date(cpt) >= nb_beg(i)  ), (date(cpt) <= nb_end(i)) )
    cpt = cpt+1;
    compt = compt+1;
    if cpt > length(hw)
        break
    end
    end
end
(compt-1)*100/length(hw)  

#end
