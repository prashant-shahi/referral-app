# GraphQL Server
This folder contains graphql server source code.
Language: NodeJS (Express)

# Overview
GraphQL Server is a Node.js application which is mainly consists of `express` and `express-graphql` library packages. This server is used for the functions to define *mutations* and *queries*. These functions makes use of APIs provided by the REST API server with the function parameters often passed as payload. These functions also takes in a query consisting of various fields which makes it possible for clients to obtain only the request data.

## Quick start
There are multiple ways to get this project started. Easiest would be to use [Docker](https://ddocker.com). Follow the instructions below:
```sh
git clone https://github.com/coolboi567/referral-app

cd referral-app/graphql-server

docker run -td -p 4000:4000 $(docker build -q .)
```

Alternatively, for skipping the image building time, you can use the pre-built images of this project from [Docker Hub](https://hub.docker.com/u/coolboi567/graphql-server).
```
docker run -td -p 4000:4000 coolboi567/graphql-server
```

## Screenshots
Query and Result in GraphiQL:
<p float="left">
  <img src="https://i.imgur.com/iSqDfKx.jpg">
</p>
<img src="https://i.imgur.com/KFACeId.jpg">