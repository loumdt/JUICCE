function calcT95_Tmin_exact(quantieme)
filename = "../../tg_ens_mean_summer_cropped.nc"
clear var;
var = ncread(filename,'tg');
addpath('../m_map')
data = 'tn';
quantieme = 95;
n=10; %nb de jours max de part et d'autre pour moyenner et calculer qtile
an = 69;

##path_data = '/homedata/mstefano/eca/europe/ano_year/' ;
##path_data_out = '/homedata/mstefano/eca/europe/quantile/';
##path = pwd;
##prefix = cat(2,'T',int2str(quantieme),'_p');
##var = 0;
##file = cat(2,path_data,data,'1');
##eval(['  load ' file '  '])
##file = cat(2,path_data,data,'2');
##eval(['  load ' file '  '])
##var = cat(3,var1,var2);
##clear var1 var2
##whos

siz = size(var);
var = reshape(var,siz(1)*siz(2),siz(3)/an,an);

for i = 1 : siz(1)*siz(2)
	Var = squeeze(var(i,:,:));
	Mat=[Var(22:133,:)];
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
%clear var buffer
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
eval([' var = reshape(T' int2str(quantieme) ',siz(1),siz(2),6348); '])



eval(['save -v7.3 quantile/Q' int2str(quantieme) '_Tmin_test.mat var lon lat temps var_unit var_name ']);


end
