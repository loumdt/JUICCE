clear all
load /home/ajeze/Documents/DetectionCanicule/tn

%boucle sur le nombre d'années
%but: retirer hiver printemps et automne
%for i=1:26
%	temps((26-i)*365+244:(26-i)*365+365) = [];
%	temps((26-i)*365+1:(26-i)*365+151) = [];
%	var(:,:,(26-i)*365+244:(26-i)*365+365) = [];
%	var(:,:,(26-i)*365+1:(26-i)*365+151) = [];
%end
ind = (find(var<-95));
var(ind) = NaN;

%choix du nombre d'années
an = 69;
%variable anomalies pour l'été
ano = reshape(var,length(lon),length(lat),153,an);
%moyenne calendaire des anomalies. Pour chaque jour, chaque latitude, chaque longitude, je moyenne sur les années.
mea_ano = mean(ano,4);

%boucle pour créer les anomalies
for i=1:an
    ano(:,:,:,i) = squeeze(ano(:,:,:,i)) - mea_ano;
end
%je crée un fichier anomalie avec une variable temps qui met bout à bout les jours estivaux.
var  = reshape(ano,length(lon),length(lat),153*69);


save -v7.3 /home/ajeze/Documents/DetectionCanicule/ano/tn lat lon temps var var_name var_unit

