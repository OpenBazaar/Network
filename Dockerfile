FROM debian:8.5
MAINTAINER eiabea <developer@eiabea.com>

# Install required Debian packages
RUN set -ex \
  && apt-get update -q \
  && apt-get upgrade -y -q \
  && apt-get install -y -q git autoconf pkg-config libtool build-essential libssl-dev libffi-dev python-dev openssl python-pip libzmq3-dev

# Install cryptography and pylint
WORKDIR /
RUN pip install cryptography

# Install libzmq from github
RUN git clone https://github.com/zeromq/libzmq
WORKDIR /libzmq
RUN set -ex \
  && ./autogen.sh \
  && ./configure \
  && make \
  && make check \
  && make install \
  && ldconfig

# Install python packages
RUN pip install --upgrade cffi
RUN pip install pynacl

# Install Openbazaar-Server from github
WORKDIR /
RUN git clone https://github.com/OpenBazaar/OpenBazaar-Server.git
WORKDIR /OpenBazaar-Server/
RUN pip install -r requirements.txt

# Copy entrypoint script and mark it executable
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create Openbazaar user and set correct permissions
RUN adduser --disabled-password --gecos \"\" openbazaar
RUN chown -R openbazaar:openbazaar /OpenBazaar-Server

VOLUME /root/.openbazaar
VOLUME /ssl

EXPOSE 18466
EXPOSE 18467
EXPOSE 18469
EXPOSE 18470

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD python openbazaard.py start -a 0.0.0.0