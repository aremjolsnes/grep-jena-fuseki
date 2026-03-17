# Plan E v10.3: HARD RESET (Fjern alle korrupte filer)
FROM eclipse-temurin:17-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE/databases

# Last ned Fuseki 5.3.0
RUN wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-5.3.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

ENV JAVA_OPTIONS="-Xmx1g -Xms1g"

EXPOSE 3030

# TVUNGET RESET: Vi sletter alt på disken VED HVER START i denne versjonen.
# Dette er den eneste måten å bli kvitt de korrupte filene som krasjer JVM-en.
CMD ["sh", "-c", "echo 'TVUNGET RESET: Sletter alle databaser på disk...'; rm -rf /fuseki/databases/*; mkdir -p /fuseki/databases && java $JAVA_OPTIONS -jar fuseki-server.jar --port=3030 --tdb2 --loc=/fuseki/databases --update /ds"]
