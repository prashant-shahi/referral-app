# Alpine base image with NodeJS v10.16.0 (lts)
FROM node:lts-alpine

MAINTAINER Prashant Shahi "coolboi567@gmail.com"

# Setting work directory
WORKDIR /usr/src/app

# Copy the source code of app to docker demon
COPY . ./

# Install npm dependencies
RUN npm install

# Expose the application on the port
EXPOSE 4000

# Run the node command
CMD ["node", "server.js"]
