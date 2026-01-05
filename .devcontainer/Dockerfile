FROM mcr.microsoft.com/devcontainers/python:3.12

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

WORKDIR /workspace
