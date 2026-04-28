FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies identical to Apptainer specification, adjusted for Ubuntu 22.04
RUN apt-get update && \
    apt-get -y install --no-install-recommends cmake make g++ pypy3 default-jre-headless zlib1g-dev git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /planner

# Clone the exact IPC 2023 DecStar repository
RUN git clone https://github.com/ipc2023-classical/planner15.git . && \
    git checkout latest

# Import CPLEX Installer provided by user
COPY planners/decstar/cplex_studio2212.linux_x86_64.bin /planner/cplex.bin
RUN chmod +x /planner/cplex.bin

# Silently install CPLEX
RUN /planner/cplex.bin -DLICENSE_ACCEPTED=TRUE -i silent

# Configure environment based on CPLEX v22.12
ENV DOWNWARD_CPLEX_ROOT=/opt/ibm/ILOG/CPLEX_Studio2212/cplex/
ENV DOWNWARD_CPLEX_CONCERT64=/opt/ibm/ILOG/CPLEX_Studio2212/concert/
ENV PATH="/planner/third-party/bliss-0.73:$PATH"
ENV DOWNWARD_COIN_ROOT=/opt/coin/

# Build Bliss
RUN cd third-party/bliss-0.73 && \
    make clean && make && make lib

# Build OSI linked to CPLEX 22.12
RUN cd third-party/Osi-0.108.6 && \
    ./configure CC="gcc"  CFLAGS="-pthread -Wno-long-long" \
            CXX="g++" CXXFLAGS="-pthread -Wno-long-long" \
            LDFLAGS="-L$DOWNWARD_CPLEX_ROOT/lib/x86-64_linux/static_pic" \
            --without-lapack --enable-static=yes \
            --prefix="$DOWNWARD_COIN_ROOT" \
            --disable-bzlib  \
            --with-cplex-incdir=$DOWNWARD_CPLEX_ROOT/include/ilcplex \
            --with-cplex-lib="-lcplex -lm -ldl" && \
    make && make install

# Build DecStar Fast-Downward Core
RUN pypy3 build.py release64

WORKDIR /workspace
# bust cache 2
ARG CACHEBUST=1
COPY planners/decstar/planner_exec /planner_exec
RUN chmod +x /planner_exec

ENTRYPOINT ["/planner_exec"]
