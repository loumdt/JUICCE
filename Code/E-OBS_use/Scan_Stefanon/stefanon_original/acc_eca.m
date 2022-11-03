function [r]=acc_eca(X,Y,lat)

for i = 1 : size(Y,1)
	num =  X.*squeeze(Y(i,:));
	denom_1 = X.^2;
        denom_2 = Y(i,:).^2;
        r(i) = 1 - sum(num)/sqrt(sum(denom_1).*sum(denom_2));
%        r(i) = 1 - sum(num)/sqrt(sum(denom_1)).*sqrt(sum(denom_2));
end
