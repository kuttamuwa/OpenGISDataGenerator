# syntax=docker/dockerfile:1
FROM ubuntu:18.04
WORKDIR /app
COPY req.yml req.yml

# Anaconda
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN apt-get update -y
RUN apt-get install -y wget

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh
RUN conda --version

RUN conda env create --file req.yml python=3.10
COPY . .
CMD ["python", "main.py"]