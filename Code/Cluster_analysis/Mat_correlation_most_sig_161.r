library(corrplot);
dataset<-read.table("/home/theom/Bureau/PFE/Data/EM-DAT/emdat_Europe_1950-2021_most_significant.csv",h=TRUE,sep=",",dec=".") ;
attach(dataset) ;
names(dataset) ;
datanum<-data.frame(dataset[20]/sd(dataset[[20]]),dataset[21]/sd(dataset[[21]]),dataset[22]/sd(dataset[[22]]),dataset[23]/sd(dataset[[23]]), dataset[24]/sd(dataset[[24]]),dataset[26]/sd(dataset[[26]]),dataset[27]/sd(dataset[[27]])) ;
mat_cor<-cor(datanum) ; #Correlation matrix

png(file = "Mat_correlation_most_sig_161.png", width = 800, height = 700)
corrplot(mat_cor, type="upper", order="hclust", tl.col="black", tl.srt=45) #Correlation matrix plot
dev.off()


#mat_cov<-cov(datanum) #Covariance matrix
