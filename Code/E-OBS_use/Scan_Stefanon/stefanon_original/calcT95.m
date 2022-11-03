%function calcT95(data,quantieme)
addpath('/home/ajeze/Documents/DetectionCanicule/m_map')
data = 'tx';
quantieme = 95;
n=10; %nb de jours max de part et d'autre pour moyenner et calculer qtile
an = 69;

path_data =  'D:/Ubuntu/PFE/Data/E-OBS/0.1deg/';
path_data_out = 'D:/Ubuntu/PFE/Code/E-OBS_use/Stefanon/code_Stefanon/DetectionCanicule';
path = pwd
prefix = cat(2,'T',int2str(quantieme),'_p')
%var = 0
%file = cat(2,path_data,data,'1')
%eval(['  load ' file '  '])
%file = cat(2,path_data,data,'2')
%eval(['  load ' file '  '])
%var = cat(3,var1,var2);
%clear var1 var2
whos

siz = size(var);
var = reshape(var,siz(1)*siz(2),siz(3)/an,an);

for i = 1 : siz(1)*siz(2)
	Var = squeeze(var(i,:,:));
	Mat=[Var((92-n+1):92,:) ; Var; Var(1:n,:)];
	MM=Mat;
		for k=1:n
		    MM=[MM(2:end-1,:) Mat(1+2*k:end,:) Mat(1:end-2*k,:)];
		end
	MN=MM(n-k+1:end-n+k,:)';
	eval([' T' int2str(quantieme)  '(i,:) = repmat(quantile(MN,' int2str(quantieme) '/100,1),1,' int2str(an) ');'])	
	if mod(i,1000) == 0
		whos
		%buffer = eval(['  T' int2str(quantieme)  '(' int2str(i-999) ':' int2str(i) ',:) ']) ;
		%eval(['save  T'  int2str(quantieme)   '_p' int2str(i)  '.mat buffer  lon lat ']);
		%eval(['T'  int2str(quantieme)   '_p' int2str(i)  '=  T' int2str(quantieme)  '(' int2str(i-999) ':' int2str(i) ',:); ']) ;
	end
end
i
%buffer = eval(['  T' int2str(quantieme)  '(' int2str(38001) ':' int2str(i) ',:) ']) ;
%%eval(['save  T'  int2str(quantieme)   '_p' int2str(i)  '.mat buffer  lon lat ']);
%eval(['T'  int2str(quantieme)   '_p' int2str(i)  '=  T' int2str(quantieme)  '(' int2str(38001) ':' int2str(i) ',:); ']) ;
clear var buffer
whos


%file = cat(2,prefix,int2str(1000));
%eval([' var =  ' file ';']);
%eval([' clear ' file '']);
%for i = 2000 : 1000 : 38000
%	file = cat(2,prefix,int2str(i));
%	eval([' var =  vertcat(var,' file ');']);
%eval([' clear ' file '']);
%end
%file = cat(2,prefix,int2str(38801));
%eval(['  load ' file '  '])
%var = vertcat(var,buffer);
%eval([' var =  vertcat(var,' file ');']);
%eval([' clear ' file '']);	
eval([' var = reshape(T' int2str(quantieme) ',siz(1),siz(2),siz(3)); '])


eval(['save -v7.3 ' path_data_out '/' data '' int2str(quantieme) '_test.mat var lon lat temps var_unit var_name ']);


