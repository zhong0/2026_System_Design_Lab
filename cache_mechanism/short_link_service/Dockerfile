FROM rockylinux:9

RUN dnf update -y

RUN dnf groupinstall -y "Development Tools"
RUN dnf install -y \
    wget \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel

WORKDIR /tmp
RUN wget https://www.python.org/ftp/python/3.12.9/Python-3.12.9.tgz && \
    tar xzf Python-3.12.9.tgz && \
    cd Python-3.12.9 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.12.9 Python-3.12.9.tgz

RUN ln -s /usr/local/bin/python3.12 /usr/local/bin/python && \
    ln -s /usr/local/bin/pip3.12 /usr/local/bin/pip

RUN pip install --upgrade pip==26.0

RUN dnf remove -y wget || true
RUN dnf clean all

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

EXPOSE 1002

CMD ["python", "main.py"]