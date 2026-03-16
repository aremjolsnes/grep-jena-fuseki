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

# RAM-innstillinger for stabil drift på liten maskin (512MB VM)
ENV JAVA_OPTIONS="-Xmx384m -Xms128m"

EXPOSE 3030

# Her er den magiske kombinasjonen for Fuseki 6:
# --tdb2 : Bruk den moderne databasetypen
# --loc  : Her skal filene lagres
# (Lytter på alle adresser som standard i Fuseki 6)
# /ds    : Navnet på datasettet helt til slutt
CMD ["./fuseki-server", "--port=3030", "--tdb2", "--loc=/fuseki/databases", "--update", "/ds"]
