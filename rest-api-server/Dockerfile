# Alpine base image with python v3.6
FROM python:3.6-alpine

MAINTAINER Prashant Shahi "coolboi567@gmail.com"

# Setting work directory
WORKDIR /usr/src/app

# Copying requirements.txt to docker demon
COPY requirements.txt ./

# Installing dependencies
RUN apk update && \
	apk add build-base python-dev libc6-compat && \
	pip install -U -r requirements.txt && \
	pip install --no-cache-dir -r requirements.txt

# Copying the complete source code to the work directory
COPY . ./

# Exposing port 5000
EXPOSE 5000

# Running the app
CMD [ "python", "main.py" ]