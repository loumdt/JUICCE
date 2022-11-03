library(corrplot);
library(ade4);
library(vegan);
library(cluster);
library(gclus);
library(RColorBrewer);
library(labdsv);
dataset<-read.csv("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_most_significant.csv",row.names=28) ;
attach(dataset) ;
names(dataset) ;
#Glide_numbers<-data.frame(dataset[28]);
#datanum<-data.frame(dataset[20]/sd(dataset[[20]]),dataset[21]/sd(dataset[[21]]),dataset[22]/sd(dataset[[22]]),dataset[23]/sd(dataset[[23]]), dataset[24]/sd(dataset[[24]]),dataset[26]/sd(dataset[[26]]),dataset[27]/sd(dataset[[27]])) ;
datanum<-data.frame(dataset[20],dataset[21],dataset[22],dataset[23], dataset[24],dataset[26],dataset[27]) ;

datanum.norm <- decostand(datanum, "normalize")
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
myCol <- grep("red", colors(), value = TRUE)


colLab <- function(n)
{
  if(is.leaf(n))
  {
    a <- attributes(n)
    if ( length(which(reds == a$label)) == 1 )
    {
      attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "firebrick1", lab.cex=1.5,
                                              col="firebrick1", pch=16 ))
    }
    else
      if ( length(which(blues == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "royalblue3", lab.cex=1.5,
                                                col="royalblue3" , pch=16))
      }
    else
      if ( length(which(greens == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "aquamarine4", lab.cex=1.5,
                                                col="aquamarine4" , pch=16))
      }
    else
      if ( length(which(greys == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "gray", lab.cex=1.5,
                                                col="gray" , pch=16))
      }
    else
      if ( length(which(sands == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "bisque2", lab.cex=1.5,
                                                col="bisque2" , pch=16))
      }
    else
      if ( length(which(oranges == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "darkorange", lab.cex=1.5,
                                                col="darkorange" , pch=16))
      }
    else
      if ( length(which(browns == a$label)) == 1 )
      {
        attr(n, "nodePar") <- c(a$nodePar, list(lab.col = "saddlebrown", lab.cex=1.5,
                                                col="saddlebrown" , pch=16))
      }
  }
  n
}


#---------------------------------------------------#
# Single Linkage Agglomerative Clustering           #
#---------------------------------------------------#

datanum.ch.single <- hclust(datanum.ch,method="single")

dend <- as.dendrogram(datanum.ch.single)
dend_colored <- dendrapply(dend, colLab)


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_single_linkage_most_sig_161.png", width = 10000, height = 9000)
plot(dend_colored)#, type="upper", order="hclust", tl.col="black", tl.srt=45) #plot
dev.off()


#---------------------------------------------------#
# Complete Linkage Agglomerative Clustering         #
#---------------------------------------------------#

datanum.ch.complete <- hclust(datanum.ch,method="complete") ;

dend2 <- as.dendrogram(datanum.ch.complete)
dend2_colored <- dendrapply(dend2, colLab)


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_complete_linkage_most_sig_161.png", width = 10000, height = 9000)
plot(dend2_colored)#, type="upper", order="hclust", tl.col="black", tl.srt=45) #plot
dev.off()


#---------------------------------------------------#
# Average Agglomerative Clustering                  #
#---------------------------------------------------#

datanum.ch.UPGMA <- hclust(datanum.ch,method="average") ;

dend3 <- as.dendrogram(datanum.ch.UPGMA) ;
dend3_colored <- dendrapply(dend3, colLab)


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_average_most_sig_161.png", width = 10000, height = 9000)
plot(dend3_colored)#, type="upper", order="hclust", tl.col="black", tl.srt=45) #plot
dev.off()


#---------------------------------------------------#
# Ward's Minimum Variance Clustering                #
#---------------------------------------------------#

datanum.ch.ward <- hclust(datanum.ch,method="ward.D") ;
datanum.ch.ward$height <- sqrt(datanum.ch.ward$height) ;

dend4 <- as.dendrogram(datanum.ch.UPGMA) ;
dend4_colored <- dendrapply(dend4, colLab)


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_ward_min_most_sig_161.png", width = 10000, height = 9000)
plot(dend4_colored)#, type="upper", order="hclust", tl.col="black", tl.srt=45) #plot
dev.off()

#---------------------------------------------------#
#   Fusion Level values of the different methods    #
#---------------------------------------------------#

datanum.ch.ward <- hclust(datanum.ch,method="ward.D2") ;
datanum.ch.ward$height <- sqrt(datanum.ch.ward$height) ;

dend4 <- as.dendrogram(datanum.ch.UPGMA) ;
dend4_colored <- dendrapply(dend4, colLab)


png(file = "Most_sig_events_grouped_by_events/Dendrogramme_ward_min_most_sig_161.png", width = 10000, height = 9000)
plot(dend4_colored)#, type="upper", order="hclust", tl.col="black", tl.srt=45) #plot
dev.off()