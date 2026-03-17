# Plan E v10.2: Nød-sletting og Java 17 (Den tryggeste ruten)
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

# NØD-Grep: Hvis miljøvariabelen WIPE_DB er satt til 'true', sletter vi alt i databasemappen før start.
# Dette unngår 'unsafe memory access' krasj ved sletting av store datasett.
CMD ["sh", "-c", "if [ \"$WIPE_DB\" = \"true\" ]; then echo 'Wiping database folder...'; rm -rf /fuseki/databases/*; fi && mkdir -p /fuseki/databases && java $JAVA_OPTIONS -jar fuseki-server.jar --port=3030 --tdb2 --loc=/fuseki/databases --update /ds"]
