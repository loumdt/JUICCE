library(corrplot);
library(ggplot2);
library(ade4);
library(vegan);
library(cluster);
library(gclus);
library(RColorBrewer);
library(labdsv);
library(FactoMineR);
library(factoextra);
library(tidyverse);  # data manipulation
library(ape);
#dataset<-read.csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_converted_EXTRACT.csv",row.names=28) ;
dataset<-read.csv("D:/Ubuntu/PFE/Data/EM-DAT/emdat_Europe_1950-2021_converted_EXTRACT.csv",row.names=28) ;
attach(dataset) ;
names(dataset) ;
#Glide_numbers<-data.frame(dataset[28]);
datanum<-data.frame(dataset[20],dataset[21],dataset[22],dataset[23],dataset[26],dataset[27]) ;
#datanum<-data.frame( (dataset[20] - mean(dataset[[20]]))/sd(dataset[[20]]),  
#                     (dataset[21] - mean(dataset[[21]]))/sd(dataset[[21]]),  
#                     (dataset[22] - mean(dataset[[22]]))/sd(dataset[[22]]),  
#                     (dataset[23] - mean(dataset[[23]]))/sd(dataset[[23]]), 
#                     (dataset[24] - mean(dataset[[24]]))/sd(dataset[[24]]),
#                     (dataset[26] - mean(dataset[[26]]))/sd(dataset[[26]]),
#                     (dataset[27] - mean(dataset[[27]]))/sd(dataset[[27]])) ;

datanum.norm <- scale(datanum,center=T,scale=T)
datanum.ch <- dist(datanum.norm, "euc")


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

colLab <- function(n)
{
  if(is.leaf(n))
  {
    a <- attributes(n)
    if ( length(which(reds == a$label)) == 1 )
    {
      attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "firebrick1", lab.cex=.5,
                                              col="firebrick1", pch=16 ))
    }
    else
      if ( length(which(blues == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "royalblue3", lab.cex=.5,
                                                col="royalblue3" , pch=16))
      }
    else
      if ( length(which(greens == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "aquamarine4", lab.cex=.5,
                                                col="aquamarine4" , pch=16))
      }
    else
      if ( length(which(greys == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "gray", lab.cex=.5,
                                                col="gray" , pch=16))
      }
    else
      if ( length(which(sands == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "bisque2", lab.cex=.5,
                                                col="bisque2" , pch=16))
      }
    else
      if ( length(which(oranges == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "darkorange", lab.cex=.5,
                                                col="darkorange" , pch=16))
      }
    else
      if ( length(which(browns == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "saddlebrown", lab.cex=.5,
                                                col="saddlebrown" , pch=16))
      }
  }
  n
}



# 1. ACP 
res.pca <- PCA(datanum.norm, ncp = 7, graph = FALSE) ;

eig.val <- res.pca$eig ;

png(file = "All_events_grouped_by_events/PCA_proj_var_dims_1_2_all_1179.png",  width = 1200, height = 1000) ;
fviz_pca_var(res.pca, axes = c(1, 2)) ;
dev.off() ;
png(file = "All_events_grouped_by_events/PCA_proj_var_dims_3_4_all_1179.png",  width = 1200, height = 1000) ;
fviz_pca_var(res.pca, axes = c(3, 4)) ;
dev.off() ;
png(file = "All_events_grouped_by_events/PCA_proj_var_dims_5_6_all_1179.png",  width = 1200, height = 1000) ;
fviz_pca_var(res.pca, axes = c(5, 6)) ;
dev.off() ;

#png(file = "All_events_grouped_by_events/PCA_explained_variance_most_sig_161.png",  width = 1200, height = 1000) ;
barplot(eig.val[, 2], 
        names.arg = 1:nrow(eig.val), 
        main = "Variances Explained by PCs (%)",
        xlab = "Principal Components",
        ylab = "Percentage of variances",
        col ="steelblue") ;
# Add connected line segments to the plot
lines(x = 1:nrow(eig.val), eig.val[, 2], type = "b", pch = 19, col = "red") ;
#dev.off() ;

library(gridExtra)
p1<-fviz_pca_var(res.pca, axes = c(1, 2)) ;
p2<-fviz_pca_var(res.pca, axes = c(3, 4)) ;
p3<-fviz_pca_var(res.pca, axes = c(5, 6)) ;
png(file = "All_events_grouped_by_events/PCA_all_dims_all_1179.png", width = 1200, height = 1000) ;
ggarrange(p1, p2, p3, ncol=2, nrow = 2) ;
dev.off() ;


# 2. HCPC
res.hcpc <- HCPC(res.pca, graph = FALSE,method="ward") ;




myCol <- list()

for (i in 1:1179) {
  if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Extreme temperature"){
    
    myCol[i]<-"firebrick1"
    
  } else if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Flood"){
    
    myCol[i]<-"royalblue3"
    
  }else if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Storm"){
    
    myCol[i]<-"aquamarine4"
    
  }else if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Wildfire"){
    
    myCol[i]<-"darkorange"
    
  }else if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Fog"){
    
    myCol[i]<-"gray"
    
  }else if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Drought"){
    
    myCol[i]<-"bisque2"
    
  }else if (dataset[[res.hcpc$call$t$tree$order[i],6]]=="Landslide"){
    
    myCol[i]<-"saddlebrown"
  }
  
}



Palette_0 = brewer.pal(n=6, name='Dark2')

png(file = "All_events_grouped_by_events/Dendrogramme_and_clusters_all_1179.png", width = 10000, height = 9000)
fviz_dend(res.hcpc, 
          cex = 0.7,                     # Taille du texte
          palette = Palette_0,               # Palette de couleur ?ggpubr::ggpar
          rect = TRUE, rect_fill = TRUE, # Rectangle autour des groupes
          rect_border = Palette_0,           # Couleur du rectangle
          labels_track_height = 0.01,      # Augmente l'espace pour le texte
          label_cols=as.character(myCol)
) ;
dev.off()

Palette_1<-Palette_0
Palette_1[[1]]<-Palette_0[[1]]
Palette_1[[2]]<-Palette_0[[5]]
Palette_1[[3]]<-Palette_0[[4]]
Palette_1[[4]]<-Palette_0[[6]]
Palette_1[[5]]<-Palette_0[[3]]
Palette_1[[6]]<-Palette_0[[2]]

options(ggrepel.max.overlaps = 50)

png(file = "All_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_all_1179.png", width = 10000, height = 9000)
fviz_cluster(res.hcpc,
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "Factor map",
) ;
dev.off()


# Principal components + tree

png(file = "All_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_3D_all_1179.png", width = 10000, height = 9000)
plot(res.hcpc, choice = "3D.map")
dev.off()


