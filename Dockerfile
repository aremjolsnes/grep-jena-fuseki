# Plan E v6: Stabil oppstart for Fuseki 6.0.0
FROM eclipse-temurin:21-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki
ENV PORT=3030

# Installer nødvendige verktøy
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE

# Last ned Fuseki 6.0.0
RUN wget https://downloads.apache.org/jena/binaries/apache-jena-fuseki-6.0.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Bruk miljøvariabler som Fuseki forstår direkte
ENV JAVA_OPTIONS="-Xmx512m -Xms512m"

EXPOSE 3030

# Den aller enkleste oppstarten som finnes:
# Vi lager datasettet 'ds' i minnet med oppdateringstilkobling (update)
CMD ["./fuseki-server", "--mem", "--update", "/ds"]
