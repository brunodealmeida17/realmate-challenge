FROM alpine:3.21

ENV NODE_VERSION 22.14.0

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build"]
