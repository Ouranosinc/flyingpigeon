# vim:set ft=dockerfile:
FROM birdhouse/bird-base:latest
MAINTAINER https://github.com/bird-house

LABEL Description="flyingpigeon application" Vendor="Birdhouse" Version="0.2.1"

RUN apt-get update && apt-get install -y --no-install-recommends \
        software-properties-common \
        build-essential && \
    rm -rf /var/lib/apt/lists/*



# Configure hostname and ports for services
#ENV HTTP_PORT 8093
#ENV HTTPS_PORT 8443
#ENV OUTPUT_PORT 8090
#ENV HOSTNAME localhost

# Set current home
ENV HOME /root

# Copy application sources
COPY . /opt/birdhouse/src/flyingpigeon

# cd into application
WORKDIR /opt/birdhouse/src/flyingpigeon

# Provide custom.cfg with settings for docker image
RUN printf "[buildout]\nextends=profiles/crim_docker.cfg" > custom.cfg

# Install system dependencies
RUN bash bootstrap.sh -i && bash requirements.sh

# Set conda enviroment
ENV ANACONDA_HOME /opt/conda
ENV CONDA_ENVS_DIR /opt/conda/envs

RUN mkdir -p /opt/birdhouse/var/lib && mkdir -p /opt/birdhouse/var/log && mkdir -p /opt/birdhouse/etc && mkdir -p /opt/birdhouse/var/run


# Run install and fix permissions
RUN make clean install && chmod 755 /opt/birdhouse/etc && chmod 755 /opt/birdhouse/var/run && chmod 755 /opt/birdhouse/var/log && chmod 755 /opt/birdhouse/var/lib
# Volume for data, cache, logfiles, ...
VOLUME /opt/birdhouse/var/lib
VOLUME /opt/birdhouse/var/log

# Ports used in birdhouse
EXPOSE 9001 $HTTP_PORT $HTTPS_PORT $OUTPUT_PORT

# Start supervisor in foreground
ENV DAEMON_OPTS --nodaemon

# Start service ...
CMD ["make", "update-config", "start"]
