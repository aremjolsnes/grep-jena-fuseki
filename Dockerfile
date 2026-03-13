# Plan E: Last ned Fuseki direkte fra Apache kodeservere
FROM eclipse-temurin:21-jre

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki
ENV PORT=3030

# Installer nødvendige verktøy
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Lag mapper
RUN mkdir -p $FUSEKI_HOME $FUSEKI_BASE

# Last ned og pakk ut Fuseki direkte fra Apache
RUN wget https://downloads.apache.org/jena/binaries/apache-jena-fuseki-6.0.0.tar.gz -O /tmp/fuseki.tar.gz && \
    tar -xf /tmp/fuseki.tar.gz -C $FUSEKI_HOME --strip-components=1 && \
    rm /tmp/fuseki.tar.gz

WORKDIR $FUSEKI_HOME

# Eksponer porten
EXPOSE 3030

# Start serveren direkte (uten sh -c) for bedre signalhåndtering
ENTRYPOINT ["./fuseki-server"]
CMD ["--mem", "--dataset", "/ds", "--port=3030", "--localhost=false"]
