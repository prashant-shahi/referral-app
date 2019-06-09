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
            name: string @index(term) .
            email: string @index(exact) .
            age: int @index(int) .
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
                "age": 22,
                "sold": [
                  {
                    "item": "Apple iPad Pro",
                    "store": "ABC Gadgets",
                    "invoice_no": 123431,
                    "price": 58900,
                    "quantity": 4,
                    "total_amount": 58900*4
                  }
                ],
                "referred": [
                  {
                    "name": "Coby",
                    "email": "coby@gmail.com",
                    "age": 27,
                    "referred": [
                      {
                        "name": "Derik",
                        "email": "derik@gmail.com",
                        "sold": [
                          {
                            "item": "Ford EcoSport Titanium",
                            "store": "Car Showroom",
                            "invoice_no": 431441,
                            "price": 1050000,
                            "quantity": 1,
                            "total_amount": 1050000*1
                          },
                          {
                            "item": "Bacon Spinach Alfredo Pizza",
                            "store": "Tasty FoodHub",
                            "invoice_no": 431441,
                            "price": 350,
                            "quantity": 3,
                            "total_amount": 350*3
                          }
                        ]
                      }
                    ]
                  },
                  {
                    "name": "Bob",
                    "email": "bob@gmail.com",
                    "age": 19,
                    "sold": [
                      {
                        "item": "Beats by Dre Pro",
                        "store": "ABC Gadgets",
                        "invoice_no": 5432546,
                        "price": 33300,
                        "quantity": 2,
                        "total_amount": 33300*3
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

@app.route("/create-salesman", methods=['POST'])
def register():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    uid = email = ""
    try:
        name = request_json["name"]
        email = request_json["email"]
        referrer = request_json["referrer"]
    except Exception as err:
        pass
        print(datetime.datetime.now(), "Error: not all required data provided")
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
        if uid is None:
            return json_response({
                "status": "error",
                "error": "invalid referrer id"
            })
        salesman_object = {
            'uid': uid,
            'referred': salesman_object
        }

    print("New user object: ", salesman_object)
    creation_response = create_data(salesman_object)
    print("Creation response: ", creation_response)

    return json_response({
        "status": "success",
        "message": "new salesman successfully registered"
    })

@app.route("/salesman", methods=['POST'])
def query():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    uid = email = ""
    if 'id' in request_json:
        uid = request_json["id"]
    if 'email' in request_json:
        email = request_json["email"]
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
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    uid = email = None
    if 'id' in request_json:
        uid = request_json["id"]
    if 'email' in request_json:
        email = request_json["email"]
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

@app.route("/create-sales", methods=['POST'])
def sales():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    uid = email = item = store = price = quantity = ""
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    if not('item' in request_json and 'store' in request_json and 'salesman' in request_json and 'price' in request_json and 'quantity' in request_json):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    item = request_json["item"]
    store = request_json["store"]
    price = int(request_json["price"])
    quantity = int(request_json["quantity"])
    salesman = request_json["salesman"]
    if price <= 0 and quantity <=0:
        return json_response({
            "status": "error",
            "error": "price and quantity should be positive"
        })
    invoice_no = random.sample(range(1, 9999999), 1)[0]
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
            "message": "successfully created sales under a salesman",
            "data": sales_obj
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)