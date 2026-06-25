FROM node:22-alpine

WORKDIR /app

# На хостах без рабочего IPv6 Node залипает на AAAA-адресах реестра npm
# (ETIMEDOUT). Принудительно предпочитаем IPv4 и даём npm запас по ретраям.
ENV NODE_OPTIONS=--dns-result-order=ipv4first

COPY package.json ./
RUN npm install --fetch-retries=5 --fetch-retry-maxtimeout=120000 --fetch-timeout=600000

COPY . .

CMD ["npm", "run", "dev"]
