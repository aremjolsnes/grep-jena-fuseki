# Plan E v7: Persistent lagring på harddisk (ingen flere slettede data!)
FROM eclipse-temurin:21-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE

RUN wget https://downloads.apache.org/jena/binaries/apache-jena-fuseki-6.0.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Øker minnet til prosessen (Siden vi nå har 2GB på Fly)
ENV JAVA_OPTIONS="-Xmx1536m"

EXPOSE 3030

# --loc peker på harddisken vår (/fuseki)
# Dette gjør at dataene overlever omstart!
CMD ["./fuseki-server", "--loc=/fuseki/databases/ds", "--update", "/ds"]
