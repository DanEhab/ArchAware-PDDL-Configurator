FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# install dependencies
RUN apt-get update && apt-get install -y \
    git cmake g++ python3 python3-pip build-essential 

# Downward clone & build
WORKDIR /opt
RUN git clone https://github.com/aibasel/downward.git && \
    cd downward && \
    python3 build.py -j2

# Workspace for input & output
WORKDIR /workspace

# bust cache 2
ARG CACHEBUST=4
COPY planners/lama/planner_exec /planner_exec
RUN chmod +x /planner_exec

# Entry point set
ENTRYPOINT ["/planner_exec"]
