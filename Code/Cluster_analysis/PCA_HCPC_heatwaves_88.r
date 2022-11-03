library(corrplot);
library(ade4);
library(vegan);
library(cluster);
library(gclus);
library(RColorBrewer);
library(labdsv);
library(FactoMineR);
library(factoextra);
dataset<-read.csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_heatwaves_grouped_by_countries.csv",row.names=1) ;
attach(dataset) ;
names(dataset) ;
#Glide_numbers<-data.frame(dataset[28]);
datanum<-data.frame(dataset[36],dataset[37],dataset[38], dataset[40],dataset[43]) ;
#datanum<-data.frame( (dataset[20] - mean(dataset[[20]]))/sd(dataset[[20]]),  
#                     (dataset[21] - mean(dataset[[21]]))/sd(dataset[[21]]),  
#                     (dataset[22] - mean(dataset[[22]]))/sd(dataset[[22]]),  
#                     (dataset[23] - mean(dataset[[23]]))/sd(dataset[[23]]), 
#                     (dataset[24] - mean(dataset[[24]]))/sd(dataset[[24]]),
#                     (dataset[26] - mean(dataset[[26]]))/sd(dataset[[26]]),
#                     (dataset[27] - mean(dataset[[27]]))/sd(dataset[[27]])) ;

datanum.norm <- scale(datanum,center=T,scale=T)
datanum.ch <- dist(datanum.norm, "euc")

# 1. ACP 
res.pca <- PCA(datanum.norm, ncp = 7, graph = FALSE) ;
# 2. HCPC
res.hcpc <- HCPC(res.pca, graph = FALSE, method = "ward") ;

options(ggrepel.max.overlaps = 88)

Palette_0 = brewer.pal(n=8, name='Dark2')

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_and_clusters_heatwaves_88.png", width = 1500, height = 1300)
fviz_dend(res.hcpc, 
          cex = 1,                     # Taille du texte
          palette = Palette_0,               # Palette de couleur ?ggpubr::ggpar
          rect = TRUE, rect_fill = TRUE, # Rectangle autour des groupes
          rect_border = Palette_0,           # Couleur du rectangle
          labels_track_height = 0.01      # Augmente l'espace pour le texte
) ;
dev.off()


Palette_1<-Palette_0
Palette_1[[1]]<-Palette_0[[1]]
Palette_1[[2]]<-Palette_0[[2]]
Palette_1[[3]]<-Palette_0[[4]]
Palette_1[[4]]<-Palette_0[[3]]
Palette_1[[5]]<-Palette_0[[8]]
Palette_1[[6]]<-Palette_0[[5]]
Palette_1[[7]]<-Palette_0[[7]]
Palette_1[[8]]<-Palette_0[[6]]

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_and_clusters_fact_map_heatwaves_88.png", width = 1000, height = 900)
fviz_cluster(res.hcpc,
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "88 Heatwaves events (by countries) - Cluster dendrogram",
             cex=5
) ;
dev.off()


# Principal components + tree

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_and_clusters_fact_map_3D_heatwaves_88.png", width = 1000, height = 900)
plot(res.hcpc, choice = "3D.map",angle=45)
dev.off()


