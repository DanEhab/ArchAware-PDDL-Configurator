FROM ubuntu:22.04

WORKDIR /opt/madagascar

RUN apt-get update && apt-get install -y \
    build-essential python3

# Copy the Madagascar specific configuration binary (MpC)
COPY planners/madagascar/MpC /usr/local/bin/madagascar
RUN chmod +x /usr/local/bin/madagascar

WORKDIR /workspace

# bust cache 2
ARG CACHEBUST=1
COPY planners/madagascar/planner_exec /planner_exec
RUN chmod +x /planner_exec

ENTRYPOINT ["/planner_exec"]
