function prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree)

path_data = pwd;
file_in = cat(2,path_data,'/scan_scale_',data,'_',int2str(scan_size),'_',int2str(pourcent*10),'_',int2str(quantieme));
eval([' load ' file_in ' '])
clear compress 
freq_cut 
recover_area
duree 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Prepocessing (Bug resolution from m_map and use of variable name date)
%GO TO NEXT PART OF THE CODE
an = 69;
time = [datenum('01-Jan-1950'):datenum('31-Dec-2018')];
dep = 1;
bis= 0;
for i=1:an
      	if mod(i,4)== 2
        	temps(dep:dep+67) = time(((i-1)*365)+1 + bis:((i-1)*365)+68 + bis);
    		bis = bis + 1;
        	temps(dep+68:dep+365) = time(((i-1)*365)+68 + bis:((i-1)*365)+365 + bis);
        	dep = dep + 365;
     	else
         		temps(dep:dep+364) = time(((i-1)*365)+1 + bis:((i-1)*365)+365 + bis);
         		dep = dep + 365;     	
	end
end
time = temps;
clear bis dep i
time = temps;
clear temps
dep = 1;
for i=1:an
         temps(dep:dep+91) = time(((i-1)*365)+152 :((i-1)*365)+243 );
         dep = dep + 92;
end
datte = temps(indice);

lat = double(lat);
lon = double(lon);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
[nb_beg,nb_end,ind_beg,ind_end,nb_event]=propa_eca(red,indice,datte,freq_cut,recover_area);

cpt = 0; 

clear hw_*
indices_red=[];
dates_red=[];
for i=1:length(ind_beg)
    if( (nb_end(i)-nb_beg(i)) > duree )
       cpt = cpt + 1;
       hw_date(cpt,1) = nb_beg(i);
       hw_date(cpt,2) = nb_end(i);
       hw_index(cpt,1) = ind_beg(i);
       hw_index(cpt,2) = ind_end(i);
       indices_red(length(indices_red)+1:length(indices_red)+ nb_end(i)-nb_beg(i)+1) = ind_beg(i):ind_end(i)
       dates_red(length(dates_red)+1:length(dates_red)+ nb_end(i)-nb_beg(i)+1) = nb_beg(i):nb_end(i)
    end
end
cpt 
ano =reshape(ano,length(lon),length(lat),length(temps));

clear ep*
for i = 1:length(hw_index)
   ep(:,:,i) = squeeze(mean(ano(:,:,indice(hw_index(i,1)):indice(hw_index(i,2))),3));
end
for i = 1:length(hw_index)
   ep_red(:,:,i) = squeeze(mean(red(:,:,indice(hw_index(i,1)):indice(hw_index(i,2))),3));
end
for i = 1:length(indices_red)
   ep_red_tot(:,:,i) = squeeze(red(:,:,indices_red(i)));
end
ep =reshape(ep,length(lon),length(lat),size(ep,3));
ep(isnan(ep)) = zeros(size(ep(isnan(ep))));
mi = 0;
ma = 0;
for i=1:size(ep,3)
   mi = min(min(min(min(ep))),mi);
   ma = max(max(max(max(ep))),ma);
end

save -v7.3 tx_wrong_seasonal_cycle_d4.mat ano dates_red ep ep_red ep_red_tot hw_date hw_index indice indices_red lat lon temps
%Stop here

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
weight = cos(pi*lat/180)*ones(1,siz(1));
for i = 1 : length(hw_index)
        ep1(:,:,i) = weight.*squeeze(ep(:,:,i))';
	ep2(:,:,i) = weight.*squeeze(ep_red(:,:,i))';
end
ep1 = reshape(ep1,length(lat)*length(lon),length(hw_index));
ep1 = ep1';
ep2 = reshape(ep2,length(lat)*length(lon),length(hw_index));
ep2 = ep2';

D = pdist(ep2,@acc_eca,lat);
Z = linkage(D,'complete');
ep1 = ep1';
ep1 = reshape(ep1,length(lat),length(lon),length(hw_index));
ep2 = ep2';
ep2 = reshape(ep2,length(lat),length(lon),length(hw_index));


for j = 2:10
nb_node = j;
%figure(j)
[H,T,perm] = dendrogram(Z,nb_node);
clear event S* 
for i=1:nb_node
   ind = find(T==i);
   switch j
   	case {2 3 4 5 6}
              subplot(3,2,i)
	case {7 8 9}
	      subplot(3,3,i)
	case {10 11 12 13 14 15 16}
      	      subplot(4,4,i)    
   end
   if length(ind) ==1
       %[H,h]=m_contourf(lon,lat,squeeze(ep(:,:,ind))');hold on 
       %contourf(lon,lat,squeeze(ep(:,:,ind))');
       eval([' event_' int2str(i) '=  squeeze(ep2(:,:,ind)); '])
       %xlabel(datestr(hw_date(ind,:)));
       %ylabel(ind);
   else
       eval([' event_' int2str(i) '=  squeeze(mean(ep2(:,:,ind),3)); '])
       %[H,h]=m_contourf(lon,lat,squeeze(mean(ep(:,:,ind),3))');hold on
       %contourf(lon,lat,squeeze(mean(ep(:,:,ind),3))');
   end
   %m_coast('color',[0,0,0]);hold on
   %m_grid('box','fancy');hold on
   caxis([0 10])
   colorbar
   title(length(ind))
   event(i,:) = eval([' reshape(event_' int2str(i) ',1,length(lat)*length(lon)) ']) ;
end
S = pdist(event,@acc_eca,lat);
[A B]= min(S);
evaluation(j-1,1)=j;
evaluation(j-1,2)=mean(S);
evaluation(j-1,3)=std(S);
evaluation(j-1,4)=A;
evaluation(j-1,5)=max(S);
cpt = 1;
for i = 1 : length(S)
    if i ~= B
        S2(cpt) = S(i);  
        cpt = cpt +1;
    end
end
%[A B]= min(S2);
%evaluation(j-1,5)=A;
%cpt = 1;
%for i = 1 : length(S2)
%    if i ~= B
%        S3(cpt) = S2(i);  
%        cpt = cpt +1;
%    end
%end
%[A B]= min(S3);
%evaluation(j-1,6)=A;
%[ax,h3]=suplabel('Heat wave ECA');
%set(h3,'FontSize',15) 
saveName = cat(2,'heat_wave_event_',num2str(scan_size),'_',int2str(pourcent*10),'_',num2str(quantieme),'_',num2str(j));
%saveas(gcf, saveName, 'jpg');
%hgsave(saveName)
%eval([' print -depsc2 ' saveName  '   '])
%saveName = cat(2,saveName,'.eps');
%eval([' fixPSlinestyle( saveName , saveName ); '])
end
close all
sum(hw_index(:,2) - hw_index(:,1)) + size(hw_index,1)
size(hw_index,1)
plot(evaluation(:,1),evaluation(:,4),'r','linewidth',5)
hold on
%plot(evaluation(:,1),evaluation(:,5),'r')
set(gca,'FontSize',16,'FontName','Times')
title('Classifiability Index','Fontsize',20,'FontName','Times')
xlabel('Number of Clusters','Fontsize',16,'FontName','Times')
ylabel('1 - ACC','Fontsize',16,'FontName','Times')
legh = legend('First minimum');set(legh,'FontSize',16,'FontName','Times')
legend('boxoff');

clear C* index
dep = 1;
for i = 1 : size(hw_index,1)
        index(1:  length(hw_index(i,1):hw_index(i,2)) )   = hw_index(i,1):hw_index(i,2);
        C(dep:dep+ length(hw_index(i,1):hw_index(i,2)) -1) = datte(index);
	dep = dep + length(hw_index(i,1):hw_index(i,2));
	clear index
end

nb_node = 3;
[H,T,perm] = dendrogram(Z,nb_node);
close
compt = 0;
compt2 = 0;
for i=1:nb_node
    ind=find(T==i);
    clear index
    cpt = 1;
    for j = 1:length(ind)
        compt =  hw_index(ind(j),2) - hw_index(ind(j),1) + compt;
        compt2 = length(hw_index(ind(j),1):hw_index(ind(j),2)) + compt2;
        length(hw_index(ind(j),1):hw_index(ind(j),2));
        hw_index(ind(j),1):hw_index(ind(j),2);
        index(cpt: cpt + length(hw_index(ind(j),1):hw_index(ind(j),2)) -1)   = hw_index(ind(j),1):hw_index(ind(j),2);
        cpt = cpt + length(hw_index(ind(j),1):hw_index(ind(j),2));
    end  
    eval([' C' int2str(i) ' = date(index)   ; '])       
end
saveName = cat(2,'date_eca_',int2str(scan_size),'_',int2str(pourcent*10),'_',int2str(quantieme));
eval([' save ' saveName ' C C1 C2 C3 C4 C5'])% C4 C5 C6 C7 C8


for i=1:nb_node
	ind = find(T==i); 
        %eval([' E=C' int2str(i) '    ; '])       
	pattern = squeeze(mean(ep2(:,:,ind),3));
	%pattern = squeeze(mean(ep_red(:,:,ind),3));
        cpt = max(max(pattern))*0.5;
        ind = find(pattern < cpt);
        pattern(ind) = 0; 
	eval(['  pattern_tn' int2str(i)  ' = pattern; '])
	%SigPat(pattern,lat,lon,ano,temps,E)
end
SigPat(pattern,lat,lon,ano,temps,C)


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Artefact graphique
m_proj('miller','long',[lon(1) lon(end)],'lat',[lat(end) lat(1)]);
saveformat={'pdf','png','jpg','eps'};	
sav = 4;
load('topo_globale_5min.mat');
s_we=-15;
e_we=45;
s_sn=30;
e_sn=70;

[in_s_we,in_e_we,in_s_sn,in_e_sn]=extract(latitude,longitude,s_we,e_we,s_sn,e_sn);
latitude = latitude(in_s_sn : in_e_sn);
longitude = longitude(in_s_we : in_e_we);
h = h(in_s_sn : in_e_sn,in_s_we : in_e_we);

alpha1 = '(a)';
alpha2 = '(b)';
alpha3 = '(c)';
alpha4 = '(d)';
alpha5 = '(e)';
alpha6 = '(f)';
alpha7 = '(g)';
alpha8 = '(h)';
alpha9 = '(i)';
alpha10 = '(j)';
alpha11 = '(k)';
alpha12 = '(l)';
alpha = cat(1,alpha1,alpha2,alpha3,alpha4,alpha5,alpha6,alpha7,alpha8,alpha9,alpha10,alpha11,alpha12);


% Carte Patterns
nb_node = 3;
[H,T,perm] = dendrogram(Z,nb_node);
for i=1:nb_node
   ind = find(T==i);
   subplot(3,2,i)
   eval([' event_' int2str(i) '=  squeeze(mean(ep(:,:,ind),3)); '])
   if i==1  
       title('Heat Wave class')
   end
   contourf(lon,lat,squeeze(mean(ep(:,:,ind),3))','linestyle','none');hold on
   [hc,cc] = contour(longitude,latitude,h,[0 0],'k');set(cc,'LineWidth',2);
   caxis([-3 6]);
   set(gca,'FontSize',16,'FontName','Times','XLim',[-15 45],'XTick',[-15:15:45],'YLim',[30 70],'YTick',[30:10:70])
   %ht = text(-12,65,alpha(i,:));set(ht,'FontSize',16,'FontName','Times');
   %titre = cat(2,int2str(length(ind)),': Events');
   %title(titre)
   title(length(ind))
end
hcol = colorbar('horiz');
set(hcol,'FontSize',14,'FontName','Times','XLim',[-3 6],'XTick',[0:1.5:6])
set(get(hcol,'XLabel'),'String','Daily maximum temperature anomaly (deg K)','FontSize',14,'FontName','Times')
set(hcol,'Position',[0.3540   0.05    0.2375    0.0109])
saveName = (['hw_' data '_event_', num2str(nb_node) '_' int2str(scan_size) '_' int2str(pourcent*10) '_' int2str(quantieme)]);
if sav == 1 || sav==2 || sav==3        
	saveas(gcf, saveName, saveformat{sav});
	hgsave(saveName)
end
if sav ==4
	eval([' print -depsc2 ' saveName  '   '])
        hgsave(saveName)
	saveName = cat(2,saveName,'.eps');
	eval([' fixPSlinestyle( saveName , saveName ); '])
end

% Carte outil évaluation
plot(evaluation(:,1),evaluation(:,4),'r')
hold on
set(gca,'FontSize',16,'FontName','Times')
title('Classifiability Index','Fontsize',20)
xlabel('Number of Clusters','Fontsize',15)
ylabel('1 - ACC','Fontsize',15)
legend('First minimum')
saveName = cat(2,'classif',int2str(scan_size),'_',int2str(pourcent*10),'_',int2str(quantieme));
if sav == 1 || sav==2 || sav==3        
	saveas(gcf, saveName, saveformat{sav});
	hgsave(saveName)
end
if sav ==4
	eval([' print -depsc2 ' saveName  '   '])
        hgsave(saveName)
	saveName = cat(2,saveName,'.eps');
	eval([' fixPSlinestyle( saveName , saveName ); '])
end
saveName = cat(2,'classif_eca_',int2str(scan_size),'_',int2str(pourcent*10),'_',int2str(quantieme));
eval([' save ' saveName ' evaluation'])
close all



load classif_eca_30_6_95.mat
plot(evaluation(:,1),evaluation(:,4),'r')
hold on
load classif_15_9_95.mat
plot(evaluation(:,1),evaluation(:,4),'b')
load classif_eca_8_9_95.mat
plot(evaluation(:,1),evaluation(:,4),'y')
load classif_eca_15_6_95.mat
plot(evaluation(:,1),evaluation(:,4),'g')
set(gca,'FontSize',16,'FontName','Times')
title('Classifiability Index','Fontsize',20)
xlabel('Number of Clusters','Fontsize',15)
ylabel('1 - ACC','Fontsize',15)
legend('7.5/6/95','4.25/9/95','2/9/95','4.25/6/95')

% Dendrogramme
[H,T] = dendrogram(Z,77,'colorthreshold',max(Z(:,3)));
title('Classification tree','Fontsize',20)
xlabel('Clusters number','Fontsize',15)
ylabel('Similarity degree','Fontsize',15)
saveName = (['dendrogram']);
eval([' print -depsc2 ' saveName  '   '])
hgsave(saveName)
saveName = cat(2,saveName,'.eps');
eval([' fixPSlinestyle( saveName , saveName ); '])

% sauvegarde des composites des évènements

place1 = 'RU';
place2 = 'WE';
place3 = 'EE';
place4 = 'IB';
place5 = 'SC';
place6 = 'BA';
place = cat(1,place1,place2,place3,place4,place5,place6);

load /homedata/mstefano/eca/europe/lsm.mat
mask = find(var == 0);

for j =1:6
	ind = find(T==j);
	for i = 1: length(ind)
		figure(1)
		graf = squeeze(mean(ep(:,:,ind(i)),3));
		graf(mask) = NaN;
		contourf(lon,lat,graf','linestyle','none');hold on
		caxis([-4 8])
		[hc,cc] = contour(longitude,latitude,h,[0 0],'k');set(cc,'LineWidth',1);
		hcol = colorbar('horiz');
		t=title([datestr(hw_date(ind(i),1)) ' : ' datestr(hw_date(ind(i),2))]);
		set(t,'FontSize',14,'FontName','Times')
		set(hcol,'FontSize',14,'FontName','Times')
		set(gcf,'PaperUnits', 'centimeters',...
		'PaperSize', [20.984 29.6774],...
		'Units', 'centimeters',...
		'PaperType', 'A4',...
		'Position', [0.634517 2.63743 19.715 24.41],...
		'PaperPositionMode', 'auto');
		saveName = ['./event_graf/pattern_' place(j,:) '' int2str(i) ];
		eval([' print -depsc2 ' saveName  '   '])
	        hgsave(saveName)
		saveName = cat(2,saveName,'.eps');
		eval([' fixPSlinestyle( saveName , saveName ); '])
	        system(['epstopdf ' saveName]);
		close(1)
	end
end
