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

module.exports = new GraphQLSchema({
    query: RootQuery
})