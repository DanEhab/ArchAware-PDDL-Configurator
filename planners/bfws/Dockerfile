FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# Update and install all necessary dependencies identically to the IPC-2018 Singularity_AGL track
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    cmake \
    build-essential \
    ca-certificates \
    xutils-dev \
    scons \
    gcc-multilib \
    flex \
    bison \
    python2.7 \
    python-dev \
    libboost-dev \
    libjudy-dev \
    libboost-python-dev \
    libboost-program-options-dev \
    g++-multilib \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Fix python parsing references for IPC old builds
RUN ln -sf /usr/bin/python2.7 /usr/bin/python

# Setup the planner directory with the source files
WORKDIR /planner
COPY planners/bfws/LAPKT-public.tar.bz2 /planner/
COPY planners/bfws/Fast-Downward-2018-2.tar.bz2 /planner/
COPY planners/bfws/BFWS /planner/BFWS/
COPY planners/bfws/h2-fd-preprocessor /planner/h2-fd-preprocessor/

ENV LAPKT_PATH=/planner/LAPKT-public

# Extract and build LAPKT
RUN tar xjf LAPKT-public.tar.bz2 && \
    cd $LAPKT_PATH/external/libff && \
    make clean && \
    make depend && \
    make

# Build BFWS (FF and FD version)
RUN cd /planner/BFWS/ff-version && \
    scons -j4 && \
    cd /planner/BFWS/fd-version && \
    python2.7 ./build.py

# Build Fast Downward 2018-2
RUN tar xjf Fast-Downward-2018-2.tar.bz2 && \
    cd /planner/Fast-Downward-2018-2 && \
    python2.7 ./build.py release32 -j4

# Build h2-preprocessor
RUN cd /planner/h2-fd-preprocessor && \
    mkdir -p builds/release32 && \
    cd builds/release32 && \
    cmake ../../ && \
    make -j4

# Setup Execution Environment
WORKDIR /workspace
COPY planners/bfws/planner_exec /planner_exec
RUN chmod +x /planner_exec

ENTRYPOINT ["/planner_exec"]
