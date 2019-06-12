# REST API Server
This folder contains REST API server source code.
Language: Python (Flask)

## Overview
REST API Server is a Flask(Python) application which provides APIs for GraphQL Server. This server uses Dgraph Graph Database for storing data. These APIs performs CRUD Operations with Dgraph and return back data. Using GraphQL alongside with Dgraph makes it a lot easier for everyone, since the Schema remain very identical for GraphQL and Dgraph.

## Quick start
There are multiple ways to get this project started. Easiest would be to use [Docker](https://ddocker.com). Follow the instructions below:
```sh
git clone https://github.com/coolboi567/referral-app

cd referral-app/rest-api-server

docker run -td -p 5000:5000 $(docker build -q .)
```

Alternatively, for skipping the image building time, you can use the pre-built images of this project from [Docker Hub](https://hub.docker.com/u/coolboi567/rest-server).
```
docker run -td -p 5000:5000 coolboi567/rest-server
```

## Screenshots
Query and Result in Ratel(Dgraph):
<p float="left">
  <img src="https://i.imgur.com/r6goVDa.jpg" width="45%">
  <img src="https://i.imgur.com/RmdjkAy.jpg" width="45%">
</p>