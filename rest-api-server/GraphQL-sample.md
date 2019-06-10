# Mutation
## Create Customer
```graphql
mutation{
  addcustomer(name: "cus", age: 22, email: "customer@gmail.com"){
    uid
    name
    age
    email
  }
}
```

## Create Salesman
```graphql
mutation{
  addsalesman(name: "sal", age: 22, email: "sal@gmail.com"){
    uid
    name
    age
    email
  }
}
```

## Create Sales
```graphql
mutation{
  addsales(item: "Prestige Induction", store:"ABC Kitchenware", location: "BTM Layout, Bangalore", category: ["Kitchenware", "Electronics"], quantity: 2, price: 2100, customer_email: "cus@gmail.com", salesman_email:"sal@gmail.com") {
    uid
    invoice_no
    item{
      uid
      name
      category{
        uid
        name
      }
    }
    price
    quantity
    total_amount
    store{
      uid
      name
      location
    }
  }
}
```

## Delete node
```graphql
mutation {
  deletenode(reference, value){

  }
}
```


## Querying using Salesman
```graphql
query{
  salesman(email:"alan@gmail.com"){
    uid
    name
    age
    email
    sold{
      uid
      item{
        uid
        name
        category {
          uid
          name
        }
      }
      invoice_no
      quantity
      price
      total_amount
      store{
        name
        location
      }
    }
    referred{
      uid
      name
      age
      email
    }
  }
}
```