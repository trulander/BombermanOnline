FROM node:18-alpine



COPY ./package.json ./app/
COPY ./tsconfig.json ./app/
COPY ./webpack.config.js ./app/
WORKDIR /app
RUN npm install

# Используем режим разработки для фронтенда
#RUN npm run build
#
#EXPOSE 3000

CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "3000"]
