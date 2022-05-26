FROM node:8-alpine

RUN apk update && \
    apk upgrade && \
    apk add --update ca-certificates && \
    apk add chromium --update-cache --repository http://nl.alpinelinux.org/alpine/edge/community \
    rm -rf /var/cache/apk/*
# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./

# RUN npm install -g yarn
RUN yarn
# If you are building your code for production
# RUN npm install --only=production

# Bundle app source
COPY src/ ./src
COPY credentials.json ./
COPY example.js ./
COPY index.js ./

EXPOSE 3000
# CMD "/usr/src/app/node_modules/.bin/nodemon --watch /usr/src/app/src -e js /usr/src/app/src/index.js"
CMD ["npm", "start"]