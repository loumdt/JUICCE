%scan_size = 30
%quantieme = 95
%pourcent = 0.4
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

scan_size = 15
quantieme = 95
pourcent = 0.6
data = 'tx';
scan(data,scan_size,quantieme,pourcent);

%scan_size = 30
%quantieme = 95
%pourcent = 0.8
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 30
%quantieme = 95
%pourcent = 0.9
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 15
%quantieme = 95
%pourcent = 0.4
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 15
%quantieme = 95
%pourcent = 0.6
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 8
%quantieme = 90
%pourcent = 0.9
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 15
%quantieme = 95
%pourcent = 0.9
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 8
%quantieme = 95
%pourcent = 0.4
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 8
%quantieme = 95
%pourcent = 0.6
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 8
%quantieme = 95
%pourcent = 0.8
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 8
%quantieme = 95
%pourcent = 0.9
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 15
%quantieme = 90
%pourcent = 0.9
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 15
%quantieme = 99
%pourcent = 0.9
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 15
%quantieme = 95
%pourcent = 0.6
%data = 'tx';
%scan(data,scan_size,quantieme,pourcent);

%scan_size = 30;
%quantieme = 95;
%pourcent = 0.6;
%data = 'tx';
%freq_cut = 1;
%recover_area = 0.4;
%duree = 4;
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);

%scan_size = 30;
%quantieme = 95;
%pourcent = 0.9;
%data = 'tx';
%freq_cut = 1;
%recover_area = 0.4;
%duree = 4;
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);

%scan_size = 15;
%quantieme = 95;
%pourcent = 0.9;
%data = 'tx';
%freq_cut = 1;
%recover_area = 0.4;
%duree = 4;
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);

%scan_size = 8;
%quantieme = 95;
%pourcent = 0.9;
%data = 'tx';
%freq_cut = 1;
%recover_area = 0.4;
%duree = 4;
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);

%scan_size = 15;
%quantieme = 90;
%pourcent = 0.9;
%data = 'tx';
%freq_cut = 1;
%recover_area = 0.4;
%duree = 4;
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);

%scan_size = 15;
%quantieme = 99;
%pourcent = 0.9;
%data = 'tx';
%freq_cut = 1;
%recover_area = 0.4;
%duree = 4;
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);

scan_size = 15; %size of the scanning window. For 0.25° cell size, 15 corresponds to 3.75
quantieme = 95; %quantile of temperature to exceed
pourcent = 0.6; %fraction of the surface where tx exceeds the quantile
data = 'tx'; %data 
freq_cut = 1; % ?
recover_area = 0.4; % fraction of heatwaves overlapping above which they are retained as one single event
duree = 4; %minimum number of consecutive days to be considered a heatwave
%prep_tree(data,scan_size,quantieme,pourcent,freq_cut,recover_area,duree);