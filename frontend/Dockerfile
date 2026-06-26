FROM node:22-alpine AS build

WORKDIR /app

# На хостах без рабочего IPv6 Node залипает на AAAA-адресах реестра npm
# (ETIMEDOUT). Принудительно предпочитаем IPv4 и даём npm запас по ретраям.
ENV NODE_OPTIONS=--dns-result-order=ipv4first

COPY package.json ./
RUN npm install --fetch-retries=5 --fetch-retry-maxtimeout=120000 --fetch-timeout=600000

COPY . .

# Vite подставляет VITE_*-переменные в бандл на этапе сборки.
ARG VITE_API_BASE_URL=/api
ARG VITE_SMARTCAPTCHA_SITEKEY=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_SMARTCAPTCHA_SITEKEY=$VITE_SMARTCAPTCHA_SITEKEY

RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
