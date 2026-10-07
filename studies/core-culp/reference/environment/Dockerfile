FROM registry.codeocean.com/codeocean/miniconda3:4.3.30-python3.6.3-ubuntu16.04

ARG DEBIAN_FRONTEND=noninteractive

RUN pip install --upgrade --no-cache-dir --upgrade-strategy=only-if-needed \
      networkx==2.1 \
      pandas==0.23.1 \
      scikit-learn==0.19.2
