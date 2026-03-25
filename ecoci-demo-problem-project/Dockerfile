FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
  curl \
  git \
  nodejs \
  npm

COPY package.json .
RUN npm install

COPY src ./src

CMD ["node", "src/index.js"]
