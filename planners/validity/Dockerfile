FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y g++ make flex bison cmake git

# Clone VAL
WORKDIR /app
RUN git clone https://github.com/KCL-Planning/VAL.git

# Build VAL
WORKDIR /app/VAL
RUN mkdir build && cd build && cmake .. && make && ls -l /app/VAL/build

# Set entrypoint to the built binary
ENTRYPOINT ["/app/VAL/build/bin/Validate"]

