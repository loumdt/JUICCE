import statsmodels as sm
from statsmodels.tools import add_constant 
from statsmodels.api import Logit 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as clrs
from scipy import signal
from scipy import stats
 
#régression logistique - on passe la cible et les explicatives 
df=pd.read_csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/characteristics_htws.csv")

print(df.info())
#y (Extreme_bool) est l'avant-dernière colonne 
yTrain = df.iloc[:,-2] 
 
#X (les autres) sont les variables qui précèdent la dernière 
XTrain = df.iloc[:,:-2] 

Xnorm = df.iloc[:,1:-2]

print(Xnorm)

for col in range(np.shape(Xnorm)[1]) :
    Xnorm.iloc[:,col] = Xnorm.iloc[:,col]/np.max(Xnorm.iloc[:,col])

#comptage des modalités de y 
print(yTrain.value_counts()) 

#données X avec la constante 
XTrainBis = add_constant(XTrain) 
XnormBis = add_constant(Xnorm) 

#premières lignes 
print(XTrainBis.head())
print(Xnorm.head())
 
#vérifier la structure 
print(XTrainBis.info())
print(Xnorm.info())
 
lr = Logit(endog=yTrain,exog=XTrainBis) 
lr_norm = Logit(endog=yTrain,exog=Xnorm) 
 
#lancer les calculs 
#algorithme de Newton-Raphson utilisé par défaut 
#https://www.statsmodels.org/stable/generated/statsmodels.discrete.discrete_model.Logit.fit.html 
res = lr.fit()
res_norm = lr_norm.fit()

#résumé des résultats 
print(res.summary()) 
print(res_norm.summary()) 

#print(res_norm.params[2:])

meteo_list = [0]*np.shape(df)[0]
for i in range(len(meteo_list)) :
    meteo_list[i]=np.array(np.sum(res_norm.params[:]*XnormBis.iloc[i,:]))

min_val = np.min(meteo_list)
max_val = np.max(meteo_list)
print('min',np.min(meteo_list),'max',np.max(meteo_list))

idx_scatt = np.array([])
nb_htw_scatt = np.array([],dtype=np.int32)
impact_list = np.array([])

for i in range(len(df.loc[:,'impact'])) :

    if df.iloc[i,-1] > 0 :
        idx_scatt = np.append(idx_scatt, meteo_list[i])
        nb_htw_scatt = np.append(nb_htw_scatt, df.iloc[i,0])
        impact_list = np.append(impact_list, df.iloc[i,-1])

nb_htw_scatt = nb_htw_scatt[idx_scatt.argsort()] #sort the EM-DAT heatwaves lists in order to have a more readable figure, but have to keep matching impact with the given number and meteo criterion
impact_list = impact_list[idx_scatt.argsort()]
idx_scatt.sort()

fig = plt.figure(1,figsize=(24,16))

count_misplaced = 0
for val in idx_scatt :
    for val2 in meteo_list :
        if val2 not in idx_scatt and val2>val :
            count_misplaced += 1
            plt.scatter([val2],[-1],s=4,c='b',marker='s')
print('count_misplaced',count_misplaced)
class_perf = 1/(1+count_misplaced)

Y,bins_edges=np.histogram(meteo_list,bins=np.linspace(start=0.97*min_val, stop=1.03*max_val, num=30)) #histogram of the E-OBS heatwaves distribution
X=[0]*len(Y)

for k in range(len(Y)) :
    X[k]=(bins_edges[k+1]+bins_edges[k])/2
Y=np.array(Y)
Y2=signal.savgol_filter(Y, 7, 3) #smooth the histogram edges with a savitzky-golay filter

plt.plot(X,Y,'ko')
plt.plot(X,Y2,'r-')

plt.axvline(np.median(meteo_list),linewidth=1) #add median of the meteo criterion list
plt.axvline(np.percentile(meteo_list,75),linewidth=1) #add 3rd quartile of the meteo criterion list
plt.grid()
plt.xlabel('Multi_criterion')
plt.ylabel('Frequency')
plt.title('Heatwaves distribution over Multi_criterion')# ('+criteria_dico[chosen_meteo]+')',y=1)

for k in range(len(impact_list)):
    plt.annotate(str(nb_htw_scatt[k]),(idx_scatt[k],1+(k%4)),size=10,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
    y_scatt=3
    mark_size=15e3

CS1=plt.scatter(idx_scatt,[y_scatt]*len(idx_scatt),c=impact_list,s=[mark_size]*len(impact_list),cmap='YlOrRd',marker='|',norm=clrs.LogNorm(vmin=1, vmax=72210),linewidths=4) #add the EM-DAT heatwaves along with their respective impact and numbers on the E-OBS heatwaves distribution
cax = plt.axes([0.35, 0.04, 0.35, 0.01])
plt.title('Impact of the extreme heatwaves (Total_Deaths)',y=0.8)
plt.colorbar(CS1,cax=cax,orientation='horizontal')

plt.savefig("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/Heatwaves_distrib_Total_Deaths_Multi_criterion_thresh_900.png")
#plt.show()
#break

fig.clear()

plt.plot(idx_scatt,np.log10(impact_list),'k+')
(slope,intercept,rvalue,pvalue,stderr)=stats.linregress(idx_scatt,np.log10(impact_list))
X0 = np.min(idx_scatt)
Y0 = slope*X0+intercept
X1 = np.max(idx_scatt)
Y1 = slope*X1+intercept
print('pearson :',stats.pearsonr(idx_scatt,np.log10(impact_list)))
print('kendall :',stats.kendalltau(idx_scatt,np.log10(impact_list)))
print('spearman :',stats.spearmanr(idx_scatt,np.log10(impact_list)))
print('class_perf :',class_perf)
print('class_perf x Rpearson :', class_perf*rvalue)
plt.plot([X0,X1],[Y0,Y1], 'k-')
plt.annotate('R='+str(round(rvalue,5)),((X0+X1)/2,(Y0+Y1/2)),size=20)
plt.grid()
plt.ylabel('Log(Total_Deaths)')#+units_dico[meteo_criteria[j]])
plt.xlabel('Multi_criterion')

plt.savefig("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/correlation_Total_Deaths_Multi_criterion_thresh_300.png")