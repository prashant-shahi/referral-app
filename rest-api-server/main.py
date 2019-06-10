import json
import pydgraph
from flask import Flask, flash, render_template, redirect, request, url_for, Response, abort
import random
import datetime
from string import Template

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

# Loading sample data.
def load_sample():
    try:
        myobj = json.load(open('./sample-data.json'))
        return myobj
    except Exception as err:
        pass
        print(datetime.datetime.now(), "error: ", err)
        return

# Set schema.
def set_schema(schema=None):
    if schema is None:
        schema = open('./schema.dgraph').read()
        print("schema: \n", schema)
    op = pydgraph.Operation(schema=schema)
    print("set_schema: ", op)
    return client.alter(op)

# Create data using JSON.
# If myobj parameter is not passed, loads the sample data.
def create_data(myobj=None):
    print("In create_data func")
    # Create a new transaction.
    txn = client.txn()
    assigned = None
    try:
        if myobj is None:
            print("No myobj found. Loading the sample.")
            myobj = load_sample();
            print("create_data myobj: ", myobj)

        # Run mutation.
        assigned = txn.mutate(set_obj=myobj)

        # Commit transaction.
        txn.commit()

        # Get uid of the outermost object
        # assigned.uids returns a map from blank node names to uids.
        # For a json mutation, blank node names "blank-0", "blank-1", ... are used
        print('assigned : ', assigned)
        print('Created data with root node with uid = {}\n'.format(assigned.uids['blank-0']))

        print('All created nodes (map from blank node names to uids):')
        for uid in assigned.uids:
            print('{} => {}'.format(uid, assigned.uids[uid]))
    except Exception as err:
        pass
        print("ERROR: ", err)
        return
    finally:
        # Clean up. Calling this after txn.commit() is a no-op
        # and hence safe.
        txn.discard()
        print('\n')

    return assigned.uids

# Queries data wrt uid/salesman.email while taking Salesman node as root node.
def query_data(email=None, uid=None):
    print("Inside query_data func")
    variables = query = ""
    if uid:
        variables = {'uid': uid}
        query = """query all{
        all(func: uid($uid)) {
            uid
            salesman.name
            salesman.email
            salesman.age
            referred {
                uid
                salesman.name
                salesman.email
                salesman.age
            }
            sold {
                uid
                item {
                    uid
                    product.name
                    category {
                        uid
                        category.name
                    }
                }
                store {
                    uid
                    store.name
                    location
                }
                invoice_no
                price
                quantity
                total_amount
                ~bought {
                    customer.name
                    customer.email
                    customer.age
                }
            }
        }
        }"""
        template = Template(query)
        query = template.substitute(variables)
    elif email:
        variables = {'email': '"'+email+'"'}
        query = """query all {
        all(func: eq(salesman.email, $email)) {
            uid
            salesman.name
            salesman.email
            salesman.age
            referred {
                uid
                salesman.name
                salesman.email
                salesman.age
            }
            sold {
                uid
                item {
                    uid
                    product.name
                    category {
                        uid
                        category.name
                    }
                }
                store {
                    uid
                    store.name
                    location
                }
                invoice_no
                price
                quantity
                total_amount
                ~bought {
                    customer.name
                    customer.email
                    customer.age
                }
            }
        }
        }"""
        template = Template(query)
        query = template.substitute(variables)
    else:
        return
    print("variables: ", variables)
    print("query: ", query)
    res = client.txn(read_only=True).query(query)
    print("query_data response: ", res)
    return json.loads(res.json)

# Fetching uid of any node wrt any reference and value using Template.
def get_uid_obj(reference=None, value=None):
    if  not(reference and value):
        return
    query = """query getuid{
        get_uid(func: eq($reference, $value)) {
            uid
            $reference
        }
    }"""
    template = Template(query)

    try:
        # Substitute value of $reference and value
        query = template.substitute({'reference': reference, 'value': '"'+value+'"'})

        #variables = {'$value': value}
        res = client.txn(read_only=True).query(query)
        query_response = json.loads(res.json)
        if len(query_response['get_uid']) <= 0:
            return
        print("query_response: ", query_response)
        uid_obj = query_response['get_uid'][0]
        print("uid_obj: ", uid_obj)
        return uid_obj
    except Exception as err:
        print(datetime.datetime.now(), "Error: ", err)
        return

# Creating sales node.
def create_sales(customer_email, sales_obj, salesman_email):
    print("sales_obj: ", sales_obj)
    print("salesman email: ", )
    print("customer email: ", customer_email)
    salesman_uid = get_uid_obj("salesman.email", salesman_email)
    customer_uid = get_uid_obj("customer.email", customer_email)
    if salesman_uid is None or customer_uid is None:
        print(datetime.datetime.now(), " INFO either salesman or customer not pre-registered")
        return
    s_uid, c_uid = salesman_uid['uid'], customer_uid['uid']
    myobj = {
        "uid": salesman_uid,
        "sold": sales_obj
    }
    print("salesman create_sales myobj: ", myobj)
    uids = create_data(myobj=myobj)
    uid = uids['blank-0']
    if uids is None or len(uids)<=0:
        return
    myobj = {
        "uid": customer_uid,
        "bought": {
            "uid": uid
        }
    }
    print("customer create_sales myobj: ", myobj)
    uids = create_data(myobj=myobj)
    if uids is None and len(uids)<=0:
        return
    return uid

# Creating store node.
def create_store(store_obj):
    print("store_obj: ", store_obj)
    store_name = store_obj['store.name']
    store_uid = get_uid_obj("store.name", store_name)
    if store_uid is not None:
        print("WARN: Store with name ", store_name, " already exists with uid <", store_uid, ">")
        return True
    print("create_store myobj: ", store_obj)
    uids = create_data(myobj=store_obj)
    uid = uids['blank-0']
    if uids is None and len(uids)<=0:
        return
    return uid

# Generic node creation.
def create(myobj):
    print("store_obj: ", sales_obj)
    store_name = sales_obj['store.name']
    store_uid = get_uid_obj("store.name", store_name)
    if store_uid is not None:
        print("WARN: Store with name ", store_name, " already exists with uid <", store_uid, ">")
        return
    print("create_store myobj: ", store_obj)
    uids = create_data(myobj=store_obj)
    uid = uids['blank-0']
    if uids is not None and len(uids)>0:
        return uid
    return

# JSON response for app routes' return.
def json_response(object):
    return Response(json.dumps(object), mimetype="application/json")

# Verifies that the server is up.
@app.route("/")
def index():
    return json_response({
        "server": "up"
    })

# Clears all existing data in Dgraph.
@app.route("/clear-all")
def clear_all():
    res = drop_all()
    print(res)
    return json_response({
        "status": "success",
        "message": "All existing data cleared"
    })

# Clears data, sets up schema, and loads sample data.
@app.route("/setup")
def setup():
    drop_all()
    set_schema()
    create_data()
    return json_response({
        "status": "success",
        "message": "Setup complete"
    })

# Fetches uid of any node wrt any pair of reference and value.
@app.route("/get-uid", methods=["POST"])
def getuid():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    reference = value = ""
    if 'reference' in request_json:
        reference = request_json["reference"]
    if 'value' in request_json:
        value = request_json["value"]
    uid_obj = get_uid_obj(reference, value)
    if uid_obj is None:
        return json_response({
            "status": "error",
            "error": "couldn't fetch uid"
        })
    return json_response({
        "status": "success",
        "message": "successfully fetched uid",
        "data": uid_obj
    })

# Creates Salesman Node.
@app.route("/create-salesman", methods=['POST'])
def register():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    uid = name = email = age = referrer = ""
    try:
        name = request_json["name"]
        email = request_json["email"]
        age = request_json["age"]
        referrer = request_json["referrer"]
    except Exception as err:
        pass
        print(datetime.datetime.now(), "Error: not all required data provided")
    if not(name and email and age):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    salesman_object = {
        'salesman.email': email,
        'salesman.name': name,
        'salesman.age': age,
    }
    user_obj = salesman_object
    if referrer is not None:
        uid_obj = get_uid_obj("salesman.email", referrer)
        uid = uid_obj['uid']
        print("uid: ", uid)
        if uid is None:
            return json_response({
                "status": "error",
                "error": "invalid referrer id"
            })
        salesman_object = {
            "uid": uid,
            "referred": user_obj
        }
    print("New user object: ", salesman_object)
    uids = create_data(salesman_object)
    if uids is None:
        return json_response({
            "status": "error",
            "error": "error occurred while creating the salesman"
        })
    print("uids: ", uids)
    if uids is not None and len(uids)>0:
        uid = uids['blank-0']
        user_obj['uid'] = uid
    return json_response({
        "status": "success",
        "message": "new salesman successfully registered",
        "data": user_obj
    })

# Creates Salesman Node.
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
    if 'uid' in request_json:
        uid = request_json["uid"]
    if 'email' in request_json:
        email = request_json["email"]
    query_response = None
    if uid:
        print("query uid: ", uid)
        query_response = query_data(uid=uid)
    elif email:
        print("query email: ", email)
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

@app.route("/create-store", methods=['POST'])
def store_creation():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    uid = store_name = location = ""
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    if not('store_name' in request_json and 'location' in request_json):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    store_name = request_json["store_name"]
    location = request_json["location"]
    store_obj = {
        "store.name": store_name,
        "location": location
    }
    uid = create_store(store_obj)
    if uid is None:
        return json_response({
            "status": "error",
            "error": "error while creating store"
        })
    elif uid is True:
        return json_response({
            "status": "error",
            "error": "store with same name already exists"
        })
    store_obj['uid'] = uid
    return json_response({
        "status": "success",
        "message": "successfully created store",
        "data": store_obj
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
    if not('item' in request_json and 'location' in request_json and 'store' in request_json and 'customer_email' in request_json and 'salesman_email' in request_json and 'price' in request_json and 'quantity' in request_json  and 'categories' in request_json):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    item = request_json["item"]
    store = request_json["store"]
    location = request_json["location"]
    price = int(request_json["price"])
    quantity = int(request_json["quantity"])
    salesman_email = request_json["salesman_email"]
    customer_email = request_json["customer_email"]
    categories = request_json["categories"]
    if price <= 0 and quantity <=0:
        return json_response({
            "status": "error",
            "error": "price and quantity should be positive"
        })
    invoice_no = random.sample(range(1, 9999999), 1)[0]
    category_list = []
    for cat in categories:
        cat_uid = get_uid_obj("category.name", cat);
        if cat_uid is None:
            category_list.append(dict({'category.name': cat}))
        else:
            category_list.append(dict({'uid': cat_uid["uid"]}))
    store_uid = get_uid_obj("store.name", store);
    if store_uid is not None:
        store = {
            "uid": store_uid["uid"]
        }
    else:
        store = {
            "store.name": store,
            "location": location
        }
    print("category_list: ", category_list)
    sales_obj = {
        "invoice_no": invoice_no,
        "item": {
            "product.name": item,
            "category": category_list,
        },
        "store": store,
        "price": price,
        "quantity": quantity,
        "total_amount": price*quantity
    }
    uid = create_sales(customer_email, sales_obj, salesman_email)
    if uid is None:
        return json_response({
            "status": "error",
            "error": "error occurred while creating sales"
        })
    sales_obj['uid'] = uid
    return json_response({
        "status": "success",
        "message": "successfully created sales under a salesman",
        "data": sales_obj
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)