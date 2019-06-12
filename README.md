# Referral App
This project is an application with a **GraphQL Server**(Node/Express) which provides *mutation* and *query* functions that calls **REST API Server**(Python/Flask) which fetches data stored in the **Dgraph** Graph Database.

### GraphQL Server
GraphQL Server is a Node.js application which is mainly consists of `express` and `express-graphql` library packages. This server is used for the functions to define *mutations* and *queries*. These functions makes use of APIs provided by the REST API server with the function parameters often passed as payload. These functions also takes in a query consisting of various fields which makes it possible for clients to obtain only the request data.

### REST API Server
REST API Server is a Flask(Python) application which provides APIs for GraphQL Server. This server uses Dgraph Graph Database for storing data. These APIs performs CRUD Operations with Dgraph and return back data. Using GraphQL alongside with Dgraph makes it a lot easier for everyone, since the Schema remain very identical for GraphQL and Dgraph.

## Quick start
There are multiple ways to get this project started. Easiest would be to use [Docker Compose](https://docs.docker.com/compose/). Follow the instructions below:
```sh
git clone https://github.com/coolboi567/referral-app

cd referral-app

docker-compose up -d
```

Alternatively, for skipping the image building time, you can use different docker-compose file which pulls in the built images of this project from [Docker Hub](https://hub.docker.com/u/coolboi567).
```
docker-compose -f docker-compose-no-build.yaml up -d
```

Now, load the schema and sample data into Dgraph using the API end point created for the same.
```sh
curl -XGET http://localhost:5000/setup
```

Go to `http://localhost:4000/graphql` to access the GraphiQL
```
open http://localhost:4000/graphql
```

You can also use Ratel(Dgraph UI for mutation/query/schema alteration) available at `http://localhost:8000` to view and modify data/schema in Dgraph.


## Screenshots
Query and Result in GraphiQL:
<p float="left">
  <img src="https://i.imgur.com/r6goVDa.jpg" width="45%">
  <img src="https://i.imgur.com/RmdjkAy.jpg" width="45%">
</p>

Query and Result in Ratel(Dgraph):
<p float="left">
  <img src="https://i.imgur.com/iSqDfKx.jpg">
</p>
<img src="https://i.imgur.com/KFACeId.jpg">