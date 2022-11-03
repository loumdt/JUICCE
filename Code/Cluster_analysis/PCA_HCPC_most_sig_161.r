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
#dataset<-read.csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_most_significant.csv",row.names=28) ;
dataset<-read.csv("D:/Ubuntu/PFE/Data/EM-DAT/emdat_Europe_1950-2021_most_significant.csv",row.names=28) ;
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

distance <- get_dist(datanum.norm)
fviz_dist(distance, gradient = list(low = "#00AFBB", mid = "white", high = "#FC4E07"))

k6 <- kmeans(datanum.norm,centers=6,nstart=100)
k7 <- kmeans(datanum.norm,centers=7,nstart=100)
#fviz_cluster(k6,data=datanum.norm)

# plots to compare
p1 <- fviz_cluster(k6, geom = "point", data = datanum.norm, axes = c(1, 2)) + ggtitle("dims 1 & 2")
p2 <- fviz_cluster(k6, geom = "point", data = datanum.norm, axes = c(3, 4)) + ggtitle("dims 3 & 4")
p3 <- fviz_cluster(k6, geom = "point", data = datanum.norm, axes = c(5, 6)) + ggtitle("dims 5 & 6")

library(gridExtra)
png(file = "Most_sig_events_grouped_by_events/Clusters_fact_map_most_sig_161_Kmeans.png", width = 1000, height = 900) ;
grid.arrange(p1, p2, p3, nrow = 3) ;
dev.off() ;


fviz_nbclust(datanum.norm, kmeans, method = "wss")
fviz_nbclust(datanum.norm, kmeans, method = "silhouette")
fviz_nbclust(datanum.norm, kmeans, method = "gap_stat")

#---------------------------------------------------#


# 1. ACP 
res.pca <- PCA(datanum.norm, ncp = 7, graph = FALSE) ;

eig.val <- res.pca$eig ;

#png(file = "Most_sig_events_grouped_by_events/PCA_explained_variance_most_sig_161.png",  width = 1200, height = 1000) ;
barplot(eig.val[, 2], 
        names.arg = 1:nrow(eig.val), 
        main = "Variances Explained by PCs (%)",
        xlab = "Principal Components",
        ylab = "Percentage of variances",
        col ="steelblue") ;
# Add connected line segments to the plot
lines(x = 1:nrow(eig.val), eig.val[, 2], type = "b", pch = 19, col = "red") ;
#dev.off() ;


png(file = "Most_sig_events_grouped_by_events/PCA_proj_var_dims_1_2_most_sig_161.png",  width = 1200, height = 1000) ;
fviz_pca_var(res.pca, axes = c(1, 2)) ;
dev.off() ;
png(file = "Most_sig_events_grouped_by_events/PCA_proj_var_dims_3_4_most_sig_161.png",  width = 1200, height = 1000) ;
fviz_pca_var(res.pca, axes = c(3, 4)) ;
dev.off() ;
png(file = "Most_sig_events_grouped_by_events/PCA_proj_var_dims_5_6_most_sig_161.png",  width = 1200, height = 1000) ;
fviz_pca_var(res.pca, axes = c(5, 6)) ;
dev.off() ;





# 2. HCPC
res.hcpc <- HCPC(res.pca, graph = FALSE, method="ward",nb.clust=7) ;


hcpcTree<-res.hcpc$call$t$tree
apeTree<-as.phylo(hcpcTree)
apeTree<-as.dendrogram(apeTree)

#---------------------------------------------------#
#                  Coloring Function                #
#---------------------------------------------------#




myCol <- list()
match_list2<-match(res.hcpc[["call"]][["t"]][["tree"]][["labels"]],row.names(datanum))
#match_list<-match(row.names(datanum),res.hcpc[["call"]][["t"]][["tree"]][["labels"]])

for (i in 1:161) {
  if (dataset[[match_list2[i],6]]=="Extreme temperature"){
    myCol[i]<-"cyan"
    if(dataset[[match_list2[i],7]]=="Heat wave"){
      myCol[i]<-"firebrick1"
    }
    
  } else if (dataset[[match_list2[i],6]]=="Flood"){
    
    myCol[i]<-"royalblue3"
    
  }else if (dataset[[match_list2[i],6]]=="Storm"){
    
    myCol[i]<-"aquamarine4"
    
  }else if (dataset[[match_list2[i],6]]=="Wildfire"){
    
    myCol[i]<-"darkorange"
    
  }else if (dataset[[match_list2[i],6]]=="Fog"){
    
    myCol[i]<-"gray"
    
  }else if (dataset[[match_list2[i],6]]=="Drought"){
    
    myCol[i]<-"bisque2"
    
  }else if (dataset[[match_list2[i],6]]=="Landslide"){
    
    myCol[i]<-"saddlebrown"
  }
  
}


myCol_correct_order <- list()
for (i in 1:161){
  myCol_correct_order[i]<-myCol[order.dendrogram(apeTree)[i]]
  
}

options(ggrepel.max.overlaps = 50)

Palette_0 = brewer.pal(n=7, name='Dark2')


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_most_sig_161.png", width = 1500, height = 1300)
fviz_dend(res.hcpc, 
          k=7,
          cex = 0.7,                     # Taille du texte
          palette = Palette_0,               # Palette de couleur ?ggpubr::ggpar
          rect = TRUE, rect_fill = TRUE, # Rectangle autour des groupes
          rect_border = Palette_0,           # Couleur du rectangle
          labels_track_height = 0.01,      # Augmente l'espace pour le texte
          color_labels_by_k = TRUE,
          label_cols=as.character(myCol_correct_order),
          main="161 Most significant events - Cluster dendrogram"
) ;
dev.off()

Palette_1<-Palette_0
Palette_1[[1]]<-Palette_0[[2]]
Palette_1[[2]]<-Palette_0[[4]]
Palette_1[[3]]<-Palette_0[[6]]
Palette_1[[4]]<-Palette_0[[1]]
Palette_1[[5]]<-Palette_0[[7]]
Palette_1[[6]]<-Palette_0[[3]]
Palette_1[[7]]<-Palette_0[[5]]

png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_most_sig_161_dim_1_2.png", width = 1000, height = 900)
fviz_cluster(res.hcpc, 
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "161 Most significant events - Factor map",
             cex=7,
             axes=c(1,2)
) ;
dev.off()


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_most_sig_161_dim_1_2_Kmeans.png", width = 1000, height = 900)
fviz_cluster(k6, data = datanum.norm,
             #geom = "point",
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "161 Most significant events - Factor map, k-means",
             cex=7,
             axes=c(1,2)
) ;
dev.off()

png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_most_sig_161_dim_3_4.png", width = 1000, height = 900)
fviz_cluster(res.hcpc,
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "161 Most significant events - Factor map",
             cex=7,
             axes=c(3,4)
) ;
dev.off()

png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_most_sig_161_dim_3_4_Kmeans.png", width = 1000, height = 900)
fviz_cluster(k6, data = datanum.norm,
             #geom = "point",
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "161 Most significant events - Factor map, k-means",
             cex=7,
             axes=c(3,4)
) ;
dev.off()


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_most_sig_161_dim_5_6.png", width = 1000, height = 900)
fviz_cluster(res.hcpc,
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "161 Most significant events - Factor map",
             cex=7,
             axes=c(5,6)
) ;
dev.off()

png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_most_sig_161_dim_5_6_Kmeans.png", width = 1000, height = 900)
fviz_cluster(k6, data = datanum.norm,
             #geom = "point",
             repel = TRUE,            # Evite le chevauchement des textes
             show.clust.cent = TRUE, # Montre le centre des clusters
             palette = Palette_1,         # Palette de couleurs, voir ?ggpubr::ggpar
             ggtheme = theme_minimal(),
             main = "161 Most significant events - Factor map, k-means",
             cex=7,
             axes=c(5,6)
) ;
dev.off()



# Principal components + tree

options(ggrepel.max.overlaps = 20)

png(file = "Most_sig_events_grouped_by_events/Dendrogramme_and_clusters_fact_map_3D_most_sig_161.png", width = 1000, height = 900)
plot(res.hcpc, choice = "3D.map",angle=65) ;
dev.off()

plot(res.hcpc, choice = "bar")
