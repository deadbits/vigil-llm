FROM python:3.10-slim as builder

# Set the working directory in the container
WORKDIR /app

# Install the necessary build tools, dependencies, git, git-lfs, and YARA prerequisites
RUN apt-get update && apt-get install -y \
    automake \
    autoconf \
    build-essential \
    libtool \
    libc-dev \
    make \
    flex \
    gcc \
    pkg-config \
    libssl-dev \
    curl \
    unzip \
    git \
    git-lfs \
    bison \
    && rm -rf /var/lib/apt/lists/*

# Download and install YARA from source
RUN echo "Installing YARA from source ..." \
    && curl -Lo yara.zip https://github.com/VirusTotal/yara/archive/refs/tags/v4.3.2.zip \
    && unzip yara.zip \
    && cd yara-4.3.2 \
    && ./bootstrap.sh \
    && ./configure \
    && make \
    && make install \
    && make check

RUN echo "Installing pytorch deps" && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

FROM builder as vigil
# Copy vigil into the container
COPY . .

# Install Python dependencies including PyTorch CPU
RUN echo "Installing Python dependencies ... " \
    && pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the API server
EXPOSE 5000

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh", "python", "vigil-server.py", "-c", "conf/server.conf"]
