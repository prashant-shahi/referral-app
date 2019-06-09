import json
import pydgraph
from flask import Flask, flash, render_template, redirect, request, url_for, Response, abort
import random

app = Flask(__name__)

# Create a client stub.
def create_client_stub():
    return pydgraph.DgraphClientStub('localhost:9080')

# Create a client.
def create_client():
    return pydgraph.DgraphClient(client_stub)

# Close the client stub.
def close_client_stub():
    client_stub.close()


client_stub = create_client_stub()
client = create_client()


# Drop All - discard all data and start from a clean slate.
def drop_all():
    op = pydgraph.Operation(drop_all=True)
    print("drop_all: ", op)
    return client.alter(op)

# Set schema.
def set_schema(schema=None):
    if schema is None:
        schema = """
            name: string @index(term)  @lang .
            email: string @index(exact) .
            sold: uid @count @reverse .
            referred: uid @count @reverse .

            invoice_no: int @index(int) .
            item: string @index(term) .
            price: int @index(int) .
            quantity: int @index(int) .
            total_amount: int @index(int) .
            store: string @index(term) .
        """
    op = pydgraph.Operation(schema=schema)
    print("set_schema: ", op)
    return client.alter(op)

# Create data using JSON.
def create_data(myobj=None):
    # Create a new transaction.
    txn = client.txn()
    try:
        if myobj is None:
            myobj = {
                "name": "Alan",
                "email": "alan@gmail.com",
                "sold": [
                  {
                    "item": "Apple iPad Pro",
                    "store": "ABC Gadgets"
                  }
                ],
                "referred": [
                  {
                    "name": "Coby",
                    "email": "coby@gmail.com",
                    "referred": [
                      {
                        "name": "Derik",
                        "email": "derik@gmail.com",
                        "sold": [
                          {
                            "item": "Ford EcoSport Titanium",
                            "store": "Car Showroom"
                          },
                          {
                            "item": "Bacon Spinach Alfredo Pizza",
                            "store": "Tasty FoodHub"
                          }
                        ]
                      }
                    ]
                  },
                  {
                    "name": "Bob",
                    "email": "bob@gmail.com",
                    "sold": [
                      {
                        "item": "Beats by Dre Pro",
                        "store": "ABC Gadgets"
                      }
                    ]
                  }
                ]
            }

        # Run mutation.
        assigned = txn.mutate(set_obj=myobj)

        # Commit transaction.
        txn.commit()

        # Get uid of the outermost object
        # assigned.uids returns a map from blank node names to uids.
        # For a json mutation, blank node names "blank-0", "blank-1", ... are used
        # for all the created nodes.
        print('assigned : ', assigned)
        print('Created data with root node with uid = {}\n'.format(assigned.uids['blank-0']))

        print('All created nodes (map from blank node names to uids):')
        for uid in assigned.uids:
            print('{} => {}'.format(uid, assigned.uids[uid]))
    finally:
        # Clean up. Calling this after txn.commit() is a no-op
        # and hence safe.
        txn.discard()
        print('\n')

# Query
def query_data(email=None, uid=None):
    variables = {'$email': email}
    if uid:
        variables ={'$uid': str(uid)}
        query = """query all($uid: string) {
        all(func: eq(uid, $uid)) {
            uid
            name
            email
            age
            referred {
                uid
                name
                email
                age
            }
            sold {
                item
                uid
                store
                invoice_no
                price
                quantity
                total_amount
            }
        }
        }"""
    elif email:
        query = """query all($email: string) {
        all(func: eq(email, $email)) {
            uid
            name
            email
            age
            referred {
                uid
                name
                email
                age
            }
            sold {
                item
                uid
                store
                invoice_no
                price
                quantity
                total_amount
            }
        }
        }"""
    else:
        return
    res = client.txn(read_only=True).query(query, variables=variables)
    print("query_data response: ", res)
    return json.loads(res.json)

# Listing referred salesman.
def referred_salesman(email=None, uid=None):
    variables = {'$email': email}
    if uid:
        variables ={'$uid': str(uid)}
        query = """query referrals($uid: string) {
        referred_salesman(func: eq(uid, $uid)) {
            referred {
                uid
                name
                email
                age
            }
        }
        }"""
    elif email:
        query = """query referrals($email: string) {
        referred_salesman(func: eq(email, $email)) {
            referred {
                uid
                name
                email
                age
            }
        }
        }"""
    else:
        return
    res = client.txn(read_only=True).query(query, variables=variables)
    print("referred_salesman response: ", res)
    return json.loads(res.json)

# Listing sales by a salesman.
def fetch_sales(email=None, uid=None):
    variables = {'$email': email}
    if uid is not None:
        variables ={'$uid': str(uid)}
        query = """query referrals($uid: string) {
        sales(func: eq(uid, $uid)) {
            name
            uid
            email
            sold {
                item
                uid
                store
                invoice_no
                price
                quantity
                total_amount
            }
            referred {
                name
                uid
                email
            }
        }
        }"""
    elif email is not None:
        query = """query referrals($email: string) {
        sales(func: eq(email, $email)) {
            name
            uid
            email
            sold {
                item
                uid
                store
                invoice_no
                price
                quantity
                total_amount
            }
            referred {
                name
                uid
                email
            }
        }
        }"""
    else:
        return
    res = client.txn(read_only=True).query(query, variables=variables)
    print("referred_salesman response: ", res)
    return json.loads(res.json)

def fetch_salesman_uid(email="alan@gmail.com"):
    query_response = query_data(email=email)
    print(query_response)
    if len(query_response['all']) <= 0:
        return
    salesman_obj = query_response['all'][0]
    print(salesman_obj)
    uid = salesman_obj['uid']
    print(uid)
    return uid

# Creating sales.
def create_sales(salesman, sales_obj):
    print("sales_obj: ", sales_obj)
    print("salesman email: ", salesman)
    salesman_uid = fetch_salesman_uid(email=salesman)
    if salesman_uid is None:
        return
    myobj = {
        "uid": salesman_uid,
        "sold": sales_obj
    }

    print("create_sales myobj: ", myobj)
    create_data(myobj=myobj)
    return True

# JSON response
def json_response(object):
    return Response(json.dumps(object), mimetype="application/json")

@app.route("/")
def index():
    return json_response({
        "server": "up"
    })

@app.route("/setup")
def setup():
    drop_all()
    set_schema()
    create_data()
    return json_response({
        "status": "success",
        "message": "Setup complete"
    })

@app.route("/register", methods=['POST'])
def register():
    name = request.values.get("name")
    email = request.values.get("email")
    referrer = request.values.get("referrer")

    if not(name and email):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    salesman_object = {
        'email': email,
        'name': name,
    }
    if referrer is not None:
        uid = fetch_salesman_uid(referrer)
        user_object = {
            'uid': uid,
            'referred': user_object
        }

    print("New user object: ", user_object)
    creation_response = create_data(user_object)
    print("Creation response: ", creation_response)

    return json_response({
        "status": "success",
        "message": "new salesman successfully registered"
    })

@app.route("/query", methods=['POST'])
def query():
    uid = request.values.get("id")
    email = request.values.get("email")
    query_response = None
    if uid:
        print("query uid")
        query_response = query_data(uid=uid)
    elif email:
        print("query email")
        query_response = query_data(email=email)
    if query_response is None:
        return json_response({
            "status": "error",
            "error": "invalid arguments passed"
        })
    response = {
        "status": "success",
        "data": query_response
    }
    return json_response(response)

@app.route("/referrals", methods=['POST'])
def salesman_referrals():
    uid = request.values.get("id")
    email = request.values.get("email")
    query_response = None
    if uid:
        print("referrals uid")
        query_response = referred_salesman(uid=uid)
    elif email:
        print("referrals email")
        query_response = referred_salesman(email=email)
    if query_response is None:
        return json_response({
            "status": "error",
            "error": "invalid arguments passed"
        })
    return json_response({
        "status": "success",
        "data": query_response
    })

@app.route("/fetch-sales", methods=['POST'])
def get_sales():
    uid = request.values.get("id")
    email = request.values.get("email")
    query_response = None
    if uid:
        print("referrals uid")
        query_response = fetch_sales(uid=uid)
    elif email:
        print("referrals email")
        query_response = fetch_sales(email=email)
    if query_response is None:
        return json_response({
            "status": "error",
            "error": "invalid arguments passed"
        })
    return json_response({
        "status": "success",
        "data": query_response
    })

@app.route("/sales", methods=['POST'])
def sales():
    item = request.values.get("item")
    store = request.values.get("store")
    price = int(request.values.get("price"))
    quantity = int(request.values.get("quantity"))
    salesman = request.values.get("salesman")
    if not(item and store and price and quantity and salesman):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    if price <= 0 and quantity <=0:
        return json_response({
            "status": "error",
            "error": "price and quantity should be positive"
        })
    invoice_no = random.sample(range(1, 9999999), 1)
    sales_obj = {
        "invoice_no": invoice_no,
        "item": item,
        "store": store,
        "price": price,
        "quantity": quantity,
        "total_amount": price*quantity
    }
    res = create_sales(salesman, sales_obj)
    if res is None:
        return json_response({
            "status": "error",
            "error": "error occurred while creating sales"
        })
    elif res is True:
        return json_response({
            "status": "success",
            "message": "successfully created sales under a salesman"
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)