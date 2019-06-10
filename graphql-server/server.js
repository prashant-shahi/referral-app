var express = require('express');
var express_graphql = require('express-graphql');
var { buildSchema } = require('graphql');
const axios = require('axios');
var fs = require('fs');

// Building GraphQL schema using GraphQL schema file
var schema_data = fs.readFileSync('./schema/schema.graphql');
var schema = buildSchema(schema_data.toString());

// Creating function to fetch data
// Traversal begins from salesman with the provided email identifier
var getSalesman = (args) =>{
    const email = args.email;
    const person = axios.post('http://localhost:5000/salesman',{'email':email})
        .then((response) => {                    
            const data = response.data.data.all[0];
            return data;
        })
        .catch((error) => {
            // handle error
            console.log(error);
        })
    return person;
}

// Creating function to add new Salesman
var addSalesMan = (args) => {
    payload = {
        name: args.name,
        age: args.age,
        email: args.email,
        referrer: args.referrer
    };
    const response_obj = axios.post('http://localhost:5000/create-salesman', payload)
        .then((response) => {
            const data = response.data;
            if(data['status']==="success") {
                console.log(data)
                return data.data;
            } else {
                console.log("Error: ", data['error'])
                return data
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            return  {
                status: "error",
                error: error
            };
        })
        return response_obj;
};

// Creating function to add new Sales
var addSales = (args) => {
    payload = {
        item: args.item,
        store: args.store,
        price: args.price,
        quantity: args.quantity,
        salesman_email: args.salesman_email
    }
    const response_obj = axios.post('http://localhost:5000/create-sales', payload)
        .then((response) => {
            console.log("response: ", response)
            var data = response.data;
            if(data.status=="success") {
                console.log("data: ", data)
                return data.data;
            } else {
                console.log("Error: ", data.error)
                return data
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            return {
                status: "error",
                error: error
            };
        })
        return response_obj;
}

var root = {
    addsalesman: addSalesMan,
    addsales: addSales,
    salesman: getSalesman,
};

// Create an express server and a GraphQL endpoint
var app = express();
app.use('/graphql', express_graphql({
    schema: schema,
    rootValue: root,
    graphiql: true
}));
app.listen(4000, () => console.log('Express-GraphQL server now running on http://localhost:4000/graphql'));
