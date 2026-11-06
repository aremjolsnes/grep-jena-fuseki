# Plan E v10.6: Endelig stabil og persistent
FROM eclipse-temurin:17-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE/databases

# Last ned Fuseki 5.3.0 fra Maven Central (archive.apache.org har vært utilgjengelig fra runneren).
# SHA-512 er kontrollert mot Apaches offisielle .sha512 (archive.apache.org/dist/jena/binaries/).
RUN wget -q https://repo1.maven.org/maven2/org/apache/jena/apache-jena-fuseki/5.3.0/apache-jena-fuseki-5.3.0.tar.gz -O /tmp/fuseki.tar.gz && \
    echo "5204eefefb921ec029346139f5cb768fe298c816c8642ab590c9bdcee4f24cfacfb15c4266f7acf020d0d5232eea909e4af876f1d5162231ea4b8f8fe0feb3cf  /tmp/fuseki.tar.gz" | sha512sum -c - && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Konfigurasjon: åpen lesing, skriving krever innlogging (se fuseki/config.ttl og fuseki/entrypoint.sh)
COPY fuseki/config.ttl fuseki/shiro.ini fuseki/entrypoint.sh $FUSEKI_HOME/
RUN sed -i 's/\r$//' $FUSEKI_HOME/entrypoint.sh && chmod 755 $FUSEKI_HOME/entrypoint.sh

# 2 GB heap (VM har 4 GB) – gir rom for nattlige SPARQL Update-regler
ENV JAVA_OPTIONS="-Xmx2g -Xms2g"

EXPOSE 3030

# Bruker persistent lagring på Fly.io-volumet (/fuseki). Krever Fly-secret FUSEKI_PASSWORD.
CMD ["/opt/fuseki/entrypoint.sh"]
