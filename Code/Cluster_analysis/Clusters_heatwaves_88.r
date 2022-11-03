library(corrplot);
library(ade4);
library(vegan);
library(cluster);
library(gclus);
library(RColorBrewer);
library(labdsv);
dataset<-read.csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_heatwaves_grouped_by_countries.csv",row.names=1) ;
attach(dataset) ;
names(dataset) ;
#Glide_numbers<-data.frame(dataset[28]);
#datanum<-data.frame(dataset[20]/sd(dataset[[20]]),dataset[21]/sd(dataset[[21]]),dataset[22]/sd(dataset[[22]]),dataset[23]/sd(dataset[[23]]), dataset[24]/sd(dataset[[24]]),dataset[26]/sd(dataset[[26]]),dataset[27]/sd(dataset[[27]])) ;
datanum<-data.frame(dataset[36],dataset[37],dataset[38], dataset[40],dataset[43]) ;

datanum.norm <- scale(datanum,center=T,scale=T)
datanum.ch <- dist(datanum.norm, "euc") ;

#---------------------------------------------------#
# Single Linkage Agglomerative Clustering           #
#---------------------------------------------------#

datanum.ch.single <- hclust(datanum.ch,method="single") ;

dend1 <- as.dendrogram(datanum.ch.single) ;

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_single_linkage_heatwaves_88.png", width = 1200, height = 1000) ;
plot(datanum.ch.single,hang=-1,cex=1) ;
dev.off() ;

#png(file = "Heatwaves_grouped_by_countries/Dendrogramme_single_linkage_heatwaves_88_as_dend.png", width = 1200, height = 1000) ;
#plot(dend1) ;
#dev.off() ;


#---------------------------------------------------#
# Complete Linkage Agglomerative Clustering         #
#---------------------------------------------------#

datanum.ch.complete <- hclust(datanum.ch,method="complete") ;

dend2 <- as.dendrogram(datanum.ch.complete) ;

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_complete_linkage_heatwaves_88.png", width = 1200, height = 1000) ;
plot(datanum.ch.complete) ;
dev.off() ;

#png(file = "Heatwaves_grouped_by_countries/Dendrogramme_complete_linkage_heatwaves_88_as_dend.png", width = 800, height = 700) ;
#plot(dend2) ;
#dev.off() ;


#---------------------------------------------------#
# Average Agglomerative Clustering                  #
#---------------------------------------------------#

datanum.ch.UPGMA <- hclust(datanum.ch,method="average") ;

dend3<- as.dendrogram(datanum.ch.UPGMA) ;

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_average_heatwaves_88.png", width = 1200, height = 1000) ;
plot(datanum.ch.UPGMA) ;
dev.off() ;

#png(file = "Heatwaves_grouped_by_countries/Dendrogramme_average_heatwaves_88_as_dend.png", width = 800, height = 700) ;
#plot(dend3) ;
#dev.off() ;


#---------------------------------------------------#
# Ward's Minimum Variance Clustering                #
#---------------------------------------------------#

datanum.ch.ward <- hclust(datanum.ch,method="ward.D2") ;
datanum.ch.ward$height <- sqrt(datanum.ch.ward$height) ;

dend4<- as.dendrogram(datanum.ch.ward) ;

png(file = "Heatwaves_grouped_by_countries/Dendrogramme_ward_min_heatwaves_88.png", width = 1200, height = 1000) ;
plot(datanum.ch.ward) ;
dev.off() ;

#png(file = "Heatwaves_grouped_by_countries/Dendrogramme_ward_min_heatwaves_88_as_dend.png", width = 800, height = 700) ;
#plot(dend4) ;
#dev.off() ;
