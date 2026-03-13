# Plan E v8: Persistent lagring med ferdig opprettet mappe
FROM eclipse-temurin:21-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Lag alle nødvendige mapper på forhånd
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE/databases

# Last ned Fuseki 6.0.0
RUN wget https://downloads.apache.org/jena/binaries/apache-jena-fuseki-6.0.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Øker minnet til prosessen (Siden vi nå har 2GB på Fly)
ENV JAVA_OPTIONS="-Xmx1536m"

EXPOSE 3030

# Vi bruker /fuseki/databases som lokasjon - Fuseki vil nå finne denne!
CMD ["./fuseki-server", "--loc=/fuseki/databases", "--update", "/ds"]
