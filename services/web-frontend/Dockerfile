FROM node:18-alpine

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
    LOGS_BATCH_SIZE=10

# Экспортируем порт 3000
EXPOSE 3000

# Команда запуска
CMD ["npm", "start"]
