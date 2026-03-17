# Plan E v10.1: Trygghet først (Java 17 + Fuseki 5.3.0)
FROM eclipse-temurin:17-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Lag mapper og sørg for at de er skrivbare
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE/databases

# Last ned Fuseki 5.3.0
RUN wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-5.3.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Sjenerøs RAM: 1GB til Java, resten (over 3GB) til OS og Disk-cache (TDB2).
# Vi bruker Java 17 for å garantere at "unsafe memory access" (Java 21 feature) ikke kan skje.
ENV JAVA_OPTIONS="-Xmx1g -Xms1g"

EXPOSE 3030

# Vi bruker en 'sh -c' for å sikre at databasemappen finnes på den monterte disken før start.
CMD ["sh", "-c", "mkdir -p /fuseki/databases && java $JAVA_OPTIONS -jar fuseki-server.jar --port=3030 --tdb2 --loc=/fuseki/databases --update /ds"]
