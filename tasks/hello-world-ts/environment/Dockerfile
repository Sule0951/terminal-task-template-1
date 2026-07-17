FROM ubuntu:24.04

WORKDIR /app

# Toolchain the agent (and verifier) need to build and test the React component.
RUN apt-get update \
    && apt-get install -y curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Install bun and expose it on PATH for all subsequent shells.
RUN curl -fsSL https://bun.sh/install | bash
ENV BUN_INSTALL="/root/.bun"
ENV PATH="/root/.bun/bin:${PATH}"

# Install react/react-dom at the filesystem root so both /app (agent) and
# /tests (verifier) resolve them by walking up to /node_modules.
RUN cd / && bun add react react-dom
