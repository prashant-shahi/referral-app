const express = require('express');
const graphqlHTTP =  require('express-graphql');
const { buildSchema } = require('graphql');

// Creates schema using GraphQL schema language
var schema = buildSchema(`
    type Query {
        welcome: String
    }
`);

// The root provides a resolver function for each API endpoint
var root = {
    welcome: () => 'Welcome to GraphQL world!',
};  

const app = express();

// Setting route for GraphiQL at /graphql
app.use('/graphql', graphqlHTTP({
    schema,
    rootValue: root,
    graphiql:true
}));

// Running server and listening on port 4000
app.listen(4000,() => {
    console.log('now listening for requests on port 4000');
});