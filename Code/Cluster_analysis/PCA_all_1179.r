library(FactoMineR);
library(ade4);
library(vegan);
library(cluster);
library(gclus);
library(RColorBrewer);
library(labdsv);
library(ggrepel);
dataset<-read.csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_converted_EXTRACT.csv",row.names=28) ;
attach(dataset) ;
names(dataset) ;
#Glide_numbers<-data.frame(dataset[28]);
#datanum<-data.frame( (dataset[20] - mean(dataset[[20]]))/sd(dataset[[20]]),  
#                     (dataset[21] - mean(dataset[[21]]))/sd(dataset[[21]]),  
#                     (dataset[22] - mean(dataset[[22]]))/sd(dataset[[22]]),  
#                     (dataset[23] - mean(dataset[[23]]))/sd(dataset[[23]]), 
#                     (dataset[24] - mean(dataset[[24]]))/sd(dataset[[24]]),
#                     (dataset[26] - mean(dataset[[26]]))/sd(dataset[[26]]),
#                     (dataset[27] - mean(dataset[[27]]))/sd(dataset[[27]]))#,dataset[6]) ;
datanum <-data.frame(dataset[20],dataset[21],dataset[22],dataset[23], dataset[24],dataset[26],dataset[27])#,dataset[6]) ;

#define a function for coloring and sizing node elements:





#---------------------------------------------------#
#                  Coloring Function                #
#---------------------------------------------------#

reds=as.factor(row.names(dataset[dataset$DisasterType=="Extreme temperature",]))
blues=as.factor(row.names(dataset[dataset$DisasterType=="Flood",]))
greens=as.factor(row.names(dataset[dataset$DisasterType=="Storm",]))
greys=as.factor(row.names(dataset[dataset$DisasterType=="Fog",]))
sands=as.factor(row.names(dataset[dataset$DisasterType=="Drought",]))
oranges=as.factor(row.names(dataset[dataset$DisasterType=="Wildfire",]))
browns=as.factor(row.names(dataset[dataset$DisasterType=="Landslide",]))
#define a function for coloring and sizing node elements:

myCol <- list()

for (i in 1:1179) {
  if (dataset[[6]][i]=="Extreme temperature"){
    
    myCol[i]<-"firebrick1"
    
  } else if (dataset[[6]][i]=="Flood"){
    
    myCol[i]<-"royalblue3"
    
  }else if (dataset[[6]][i]=="Storm"){
    
    myCol[i]<-"aquamarine4"
    
  }else if (dataset[[6]][i]=="Wildfire"){
    
    myCol[i]<-"darkorange"
    
  }else if (dataset[[6]][i]=="Fog"){
    
    myCol[i]<-"gray"
    
  }else if (dataset[[6]][i]=="Drought"){
    
    myCol[i]<-"bisque2"
  
  }else if (dataset[[6]][i]=="Landslide"){
    
    myCol[i]<-"saddlebrown"
  }

}


options(ggrepel.max.overlaps = 10)

datanum.norm <- scale(datanum,center=T,scale=T)
datanum.ch <- dist(datanum.norm, "euc")



res.pca <- PCA(datanum, ncp=7, graph=FALSE)#, quali.sup=8) ;
#res.pca <- rda(datanum, scale=TRUE) ;
eig.val <- res.pca$eig ;

png(file = "All_events_grouped_by_events/PCA_explained_variance_all_1179.png",  width = 1200, height = 1000) ;
barplot(eig.val[, 2], 
        names.arg = 1:nrow(eig.val), 
        main = "Variances Explained by PCs (%)",
        xlab = "Principal Components",
        ylab = "Percentage of variances",
        col ="steelblue") ;
# Add connected line segments to the plot
lines(x = 1:nrow(eig.val), eig.val[, 2], type = "b", pch = 19, col = "red") ;
dev.off() ;

png(file = "All_events_grouped_by_events/PCA_proj_ind_dims_1_2_all_1179.png",  width = 1200, height = 1000) ;
plot(res.pca$ind$coord[, 1:2], type="n", 
     xlab=paste0("Axe 1 (" , round(eig.val[1,2], 2), " %) "), 
     ylab=paste0(" Axe 2 (" , round(eig.val[2,2], 2), " %) "), 
     main= "Nuage des individus",
     cex.main=1, cex.axis=0.8, cex.lab=0.8, font.lab=3) ;
abline(h=0, v=0, col= "grey", lty=3, lwd=1) ;
points(res.pca$ind$coord[, 1:2], col = as.character(myCol), pch = 19) ;
#legend("topright", legend=as.factor(dataset$DisasterType), bty= "o", text.col=1:2, col=1:2, pch=19, cex=0.8)
#plot(res.pca, choix = "ind", autoLab = "no", colour="red")
dev.off() ;

png(file = "All_events_grouped_by_events/PCA_proj_var_dims_1_2_all_1179.png",  width = 1200, height = 1000) ;
plot(res.pca, choix = "var", autoLab = "yes") ;
dev.off() ;


res.pca$call ;

# Valeurs propres
res.pca$eig ;

# Résultats des variables
res.var <- res.pca$var ;
res.var$coord    ;       # Coordonnées
res.var$contrib   ;      # Contributions aux axes
res.var$cos2   ;         # Qualité de représentation
# Résultats des individus
res.ind <- res.pca$ind ;
res.ind$coord     ;      # Coordonnées
res.ind$contrib    ;     # Contributions aux axes
res.ind$cos2   ;         # Qualité de représentation

res.var;

dimdesc(res.pca);
