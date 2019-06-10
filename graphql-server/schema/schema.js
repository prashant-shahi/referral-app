const graphql = require('graphql');
const axios = require('axios');

const { 
    GraphQLObjectType,
    GraphQLString, 
    GraphQLSchema,
    GraphQLID,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull
 } = graphql;

const Sales = new GraphQLObjectType({
    name: 'sales',
    fields: () => ({
        uid: {type: GraphQLID },
        invoice_no: {type: GraphQLInt},
        item: {type: GraphQLString},
        quantity: {type: GraphQLInt},        
        price: {type: GraphQLInt},
        store: {type: GraphQLString},  
        total_amount: {type: GraphQLInt},    
    })
});

const SalesMan = new GraphQLObjectType({
    name: 'salesman',
    fields: () => ({
        uid: {type: GraphQLString },
        name: {type: GraphQLString},
        age: {type: GraphQLInt},
        email: {type: GraphQLString},
        sold: {type: new GraphQLList(Sales)},
        referred: {
            type: new GraphQLList(SalesMan)
        }
    })
});

const RootQuery = new GraphQLObjectType({
    name: 'RootQueryType',
    fields: {
        getSalesman: {
            type: SalesMan,
            args: {
                email: {type: GraphQLString}
            },
            resolve(parent, args) {
                // resolves the specific fields in query to values                                    
                const person = axios.post('http://192.168.1.117:5000/salesman',{'email':args.email})
                .then((response) => {                    
                    const data = response.data.data.all[0];
                    //data['age']='77';
                    console.log(data)
                    return data;
                })
                .catch((error) => {
                    // handle error
                    console.log(error);
                })
                return person;
            }
        },
        getSales: {
            type: SalesMan,
            args: {
                email: {type: GraphQLString}
            },
            resolve(parent, args){
                // resolves the specific fields in query to values
                console.log(args.email); 
                const person = axios.post('http://192.168.1.117:5000/salesman',{'email':args.email})
                .then((response) => {                    
                    const data = response.data.data.all[0];
                    delete data['referred'];                    
                    console.log(data)
                    return data;
                })
                .catch((error) => {
                    // handle error
                    console.log(error);
                })
                return person;
            }
        },
        
    }
});

const Mutation = new GraphQLObjectType({
    name: 'Mutation',
    fields: {
        addSalesMan:{
            type: SalesMan,
            args: {
                name: {type: new GraphQLNonNull(GraphQLString)},
                age: {type: new GraphQLNonNull(GraphQLInt)},
                email: {type: new GraphQLNonNull(GraphQLString)},
                referrer: {type: GraphQLString },
            },
            resolve(parent, args) {
                // resolves the specific fields in query to values
                payload = {
                    name: args.name,
                    age: args.age,
                    email: args.email,
                    referrer: args.referrer
                }
                const response_obj = axios.post('http://192.168.1.117:5000/create-salesman', payload)
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
            }
        },
        addSales:{
            type: Sales,
            args: {
                item: {type: new GraphQLNonNull(GraphQLString)},
                store: {type: new GraphQLNonNull(GraphQLString)},
                price: {type: new GraphQLNonNull(GraphQLInt)},
                quantity: {type: new GraphQLNonNull(GraphQLInt)},
                salesman_email: {type: new GraphQLNonNull(GraphQLString)},
            },
            resolve(parent, args){
                // resolves the specific fields in query to values
                payload = {
                    item: args.item,
                    store: args.store,
                    price: args.price,
                    quantity: args.quantity,
                    salesman_email: args.salesman_email
                }
                const response_obj = axios.post('http://192.168.1.117:5000/create-sales', payload)
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
        },

    }
})

module.exports = new GraphQLSchema({
    query: RootQuery,
    mutation: Mutation
})