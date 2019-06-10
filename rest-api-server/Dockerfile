# Alpine based python v3.6 base image
FROM python:3.6-alpine

MAINTAINER Prashant Shahi "coolboi567@gmail.com"

# Setting work directory
WORKDIR /usr/src/app

# Copying the requirements.txt file
COPY requirements.txt ./

# Installing dependencies
RUN apk update && \
	apk add --virtual .build-deps alpine-sdk && \
	apk add libc6-compat && \
	pip install --no-cache-dir -r requirements.txt && \
	apk del .build-deps

# Copying the complete source code to the work directory
COPY . .

# Exposing port 5000
EXPOSE 5000

# Running the app
CMD [ "python", "main.py" ]