# syntax=docker/dockerfile:1
FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV TOOLS_PREFIX=/opt/fpga-tools
ENV PATH="${TOOLS_PREFIX}/bin:/root/.cargo/bin:${PATH}"

# Install dependencies
RUN apt-get -y update && apt-get -y upgrade && \
    apt-get -y install --no-install-recommends \
        python3 python3-pip python3-venv git build-essential make curl \
        flex bison zlib1g-dev clang libreadline-dev gawk tcl-dev libffi-dev \
        graphviz xdot pkg-config libboost-all-dev cmake libeigen3-dev tclsh \
        ant default-jre swig google-perftools python3-dev uuid uuid-dev \
        libfl-dev wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
RUN python3 -m venv /venv
ENV PATH="/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Build and install Synlig
RUN git clone https://github.com/chipsalliance/synlig.git && \
    cd synlig && \
    pip3 install --break-system-packages orderedmultidict && \
    git submodule sync && \
    git submodule update --init --recursive && \
    make install -j $(nproc) PREFIX=${TOOLS_PREFIX} && \
    ln -s ${TOOLS_PREFIX}/bin/synlig ${TOOLS_PREFIX}/bin/yosys && \
    cd /workspace && rm -rf synlig

# Build and install prjoxide
RUN git clone --recursive https://github.com/gatecat/prjoxide.git && \
    cd prjoxide/libprjoxide && \
    cargo install --path prjoxide && \
    cd /workspace && rm -rf prjoxide

# Build and install nextpnr-nexus
RUN git clone https://github.com/YosysHQ/nextpnr.git && \
    cd nextpnr && \
    mkdir -p build && cd build && \
    cmake .. -DARCH=nexus -DOXIDE_INSTALL_PREFIX="${HOME}/.cargo" && \
    cmake --build . -j $(nproc) && \
    cmake --install . --prefix ${TOOLS_PREFIX} && \
    cd /workspace && rm -rf nextpnr

# Copy project files
COPY . .

# Build bitstreams
RUN LANES=2 VIDEO_FORMAT=720p60 NEXTPNR_ARGS="--placer-heap-timingweight 50" make all && \
    LANES=2 VIDEO_FORMAT=1080p30 NEXTPNR_ARGS="--placer-heap-timingweight 50" make -B all && \
    LANES=2 VIDEO_FORMAT=1080p60 NEXTPNR_ARGS="--placer-heap-timingweight 50" make -B all && \
    PATTERN_GEN=1 LANES=2 VIDEO_FORMAT=720p60 NEXTPNR_ARGS="--placer-heap-timingweight 50" make -B all && \
    PATTERN_GEN=1 LANES=2 VIDEO_FORMAT=1080p30 NEXTPNR_ARGS="--placer-heap-timingweight 50" make -B all && \
    PATTERN_GEN=1 LANES=2 VIDEO_FORMAT=1080p60 NEXTPNR_ARGS="--placer-heap-timingweight 50" make -B all
