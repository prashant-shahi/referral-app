const express = require('express');
const graphqlHTTP =  require('express-graphql');

// Loading schema from the script
const schema = require('./schema/schema.js');

const app = express();

// Setting route for GraphiQL at /graphql
app.use('/graphql', graphqlHTTP({
    schema,
    graphiql:true
}));

// Running server and listening on port 4000
app.listen(4000,() => {
    console.log('now listening for requests on port 4000');
});
