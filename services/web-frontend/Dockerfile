FROM node:18-slim


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        bash \
    && curl -1sLf https://artifacts-cli.infisical.com/setup.deb.sh | bash \
    && apt-get update \
    && apt-get install -y infisical \
    && rm -rf /var/lib/apt/lists/*

COPY ./package.json ./app/
COPY ./tsconfig.json ./app/
COPY ./webpack.config.js ./app/
WORKDIR /app
RUN npm install

# Окружение по умолчанию, если не переопределено в docker-compose
ENV NODE_ENV=production \
    LOGS_ENDPOINT=/logs \
    SERVICE_NAME=web-frontend \
    SOCKET_URL=http://localhost \
    SOCKET_PATH=/socket.io \
    LOGS_BATCH_SIZE=10 \
    REACT_APP_SOCKET_URL=http://localhost \
    REACT_APP_SOCKET_PATH=/socket.io \
    REACT_APP_LOGS_ENDPOINT=/logs \
    REACT_APP_SERVICE_NAME=web-frontend \
    REACT_APP_LOGS_BATCH_SIZE=10

COPY ./entrypoint-docker.sh /usr/local/bin/entrypoint-docker.sh
RUN chmod +x /usr/local/bin/entrypoint-docker.sh

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/entrypoint-docker.sh"]
