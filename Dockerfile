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
RUN conda config --prepend channels conda-forge
RUN conda install -c conda-forge python=3.10

RUN conda env update --name oxenv --file req.yml
RUN source activate oxenv

COPY . .
CMD ["python", "main.py"]