# Plan E v10: Den mest robuste konfigurasjonen for Fuseki 6 + Fly.io
FROM eclipse-temurin:21-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Lag mapper og sørg for at de er skrivbare
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE/databases

# Last ned Fuseki 6.0.0
RUN wget https://downloads.apache.org/jena/binaries/apache-jena-fuseki-6.0.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Balansert RAM: 768MB til Java, resten (over 1.2GB) til OS og Disk-cache (TDB2).
# Dette er den gylne middelvei for 2GB VM-er.
ENV JAVA_OPTIONS="-Xmx768m -Xms768m"

EXPOSE 3030

# Vi bruker en 'sh -c' for å sikre at databasemappen finnes på den monterte disken før start.
# Dette er kritisk når man bruker Fly.io volumes.
CMD ["sh", "-c", "mkdir -p /fuseki/databases && java $JAVA_OPTIONS -jar fuseki-server.jar --port=3030 --tdb2 --loc=/fuseki/databases --update /ds"]
