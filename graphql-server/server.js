var express = require('express');
var express_graphql = require('express-graphql');
var { buildSchema } = require('graphql');
const axios = require('axios');
var fs = require('fs');

// Building GraphQL schema using GraphQL schema file
var schema_data = fs.readFileSync('./schema/schema.graphql');
var schema = buildSchema(schema_data.toString());

const rest_server = "http://"+process.env.REST_SERVER || "http://localhost:5000"

// Creating function to fetch data
// Traversal begins from salesman with the provided email identifier
var getSalesman = (args) =>{
    const payload = {
        email: args.email,
    };
    const response_obj = axios.post(rest_server+'/salesman', payload)
        .then((response) => {
            const data = response.data;
            if(data['status']==="success") {
                console.log(JSON.stringify(data))
                return data.data.all[0];
            } else if(data['status']==="warning") {
                console.log(data)
                return data.data
            } else if(data['status']==="error") {
                console.log("Error: ", data['error'])
                throw data['error']
            } else {
                throw "Unexpected error occurred"
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            throw error
        })
        return response_obj;
}

// Creating function to add new Salesman
var addSalesMan = (args) => {
    const payload = {
        name: args.name,
        age: args.age,
        email: args.email,
        referrer: args.referrer
    };
    const response_obj = axios.post(rest_server+'/create-salesman', payload)
        .then((response) => {
            const data = response.data;
            if(data['status']==="success") {
                console.log(data)
                return data.data;
            } else if(data['status']==="warning") {
                console.log(data)
                throw data["message"]
                return data.data
            } else {
                console.log("Error: ", data['error'])
                throw data['error']
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            throw error
        })
        return response_obj;
};

// Creating function to add new Sales
var addSales = (args) => {
    const payload = {
        item: args.item,
        category: args.category,
        invoice_no: args.invoice_no,
        store: args.store,
        location: args.location,
        price: args.price,
        quantity: args.quantity,
        total_amount: args.total_amount,
        salesman_email: args.salesman_email,
        customer_email: args.customer_email
    }
    const response_obj = axios.post(rest_server+'/create-sales', payload)
        .then((response) => {
            const data = response.data;
            if(data['status']==="success") {
                console.log(data)
                return data.data;
            } else if(data['status']==="warning") {
                console.log(data)
                throw data["message"]
                return data.data
            } else {
                console.log("Error: ", data['error'])
                throw data['error']
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            throw error
        })
        return response_obj;
}

// Creating function to add new Customer
var addCustomer = (args) => {
    const payload = {
        name: args.name,
        age: args.age,
        email: args.email
    };
    const response_obj = axios.post(rest_server+'/create-customer', payload)
        .then((response) => {
            const data = response.data;
            if(data['status']==="success") {
                console.log(data)
                return data.data;
            } else if(data['status']==="warning") {
                console.log(data)
                throw data["message"]
                return data.data
            } else {
                console.log("Error: ", data['error'])
                throw data['error']
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            throw error
        })
        return response_obj;
};

// Creating function to add new Salesman
var deleteNode = (args) => {
    const payload = {
        reference: args.reference,
        value: args.value
    };
    const response_obj = axios.post(rest_server+'/delete-node', payload)
        .then((response) => {
            const data = response.data;
            if(data['status']==="success") {
                console.log(data)
                return data;
            } else {
                console.log("Error: ", data['error'])
                return data;
            }
        })
        .catch((error) => {
            // handle error
            console.log("ERROR: ", error);
            throw error
        })
        return response_obj;
};

var root = {
    addsalesman: addSalesMan,
    addcustomer: addCustomer,
    addsales: addSales,
    deletenode: deleteNode,
    salesman: getSalesman
};

// Create an express server and a GraphQL endpoint
var app = express();
app.use('/graphql', express_graphql({
    schema: schema,
    rootValue: root,
    graphiql: true
}));
app.listen(4000, () => console.log('Express-GraphQL server now running on http://localhost:4000/graphql'));
