import json
import pydgraph
from flask import Flask, flash, render_template, redirect, request, url_for, Response, abort
import random
import datetime
from string import Template
import re, os

app = Flask(__name__)
dgraph_address = os.environ.get('DGRAPH_SERVER', 'http://localhost:9080')

# Create a client stub.
def create_client_stub():
    return pydgraph.DgraphClientStub(dgraph_address)

# Create a client.
def create_client():
    return pydgraph.DgraphClient(client_stub)

# Close the client stub.
def close_client_stub():
    client_stub.close()


client_stub = create_client_stub()
client = create_client()
NO_UID_OBJ = [ None, False ]


# Removes dot from key of an object
def removeDotFromKey(myobj):
    obj_str = json.dumps(myobj)
    new_str=re.sub(r'"(\w+).(name|age|email)"', r'"\2"', obj_str)
    newobj = json.loads(new_str)
    print("newobj: ", newobj)
    return newobj

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
def create_data(myobj=None, reference=None):
    print("In create_data func")
    # Create a new transaction.
    txn = client.txn()
    assigned = None
    try:
        if myobj is None:
            print("No myobj found. Loading the sample.")
            myobj = load_sample();
            print("create_data myobj: ", myobj)

        if reference:
            value = myobj[reference]
            object_uid = get_uid_obj(reference, value)
            print("create_data object_uid: ", object_uid)
            if isinstance(object_uid, dict):
                return object_uid

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
            return False
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
    if salesman_uid in NO_UID_OBJ or customer_uid in NO_UID_OBJ:
        print(datetime.datetime.now(), " INFO either salesman or customer not pre-registered")
        return False
    s_uid, c_uid = salesman_uid['uid'], customer_uid['uid']
    sales_uids = create_data(myobj=sales_obj)
    print("sales_uids: ", sales_uids)
    if sales_uids is None or len(sales_uids)<=0:
        return
    sales_uid = sales_uids['blank-0']
    print("sales_uid: ", sales_uid)
    print("type(sales_uid): ", type(sales_uid))
    myobj = {
        "uid": s_uid,
        "sold": {
            "uid": sales_uid
        }
    }
    print("customer-sales edge")
    print("customer create_sales myobj: ", myobj)
    uids = create_data(myobj=myobj)
    uid = uids['blank-0']
    if uids is None or len(uids)<=0:
        return
    print("salesman-sales edge")
    print("salesman create_sales myobj: ", myobj)
    myobj = {
        "uid": c_uid,
        "bought": {
            "uid": sales_uid
        }
    }
    uids = create_data(myobj=myobj)
    uid = uids['blank-0']
    if uids is None or len(uids)<=0:
        return
    return sales_uid

# (Deprecated) Creating store node.
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
def create(myobj, reference):
    print("create myobj: ", myobj)
    uids = create_data(myobj, reference)
    print("uids: ", uids)
    print("type(uids): ", type(uids))
    if uids is None:
        return
    if 'uid' in uids:
        uid = uids['uid']
        print("INFO \t Node with ", reference, " = ", myobj[reference], " already exists with uid <", uid, ">")
        return uid
    if not('blank-0' in uids):
        return
    uid = uids['blank-0']
    myobj['uid'] = uid
    print("myobj: ", myobj)
    if uids is None or len(uids)<=0:
        return
    return myobj

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
    print("uid_obj: ",uid_obj)
    if uid_obj is None:
        return json_response({
            "status": "error",
            "error": "couldn't fetch uid"
        })
    return json_response({
        "status": "success",
        "message": "successfully fetched uid",
        "data": removeDotFromKey(uid_obj)
    })

# Deletes a node based on reference/value.
@app.route("/delete-node", methods=["POST"])
def delete_node():
    txn = client.txn()
    try:
        request_json = request.get_json(force=True)
        print("request_json: ", request_json)
        if request_json is None:
            return json_response({
                "status": "error",
                "error": "no payload found"
            })
        uid = reference = value = ""
        if not('uid' in request_json):
            if 'reference' in request_json:
                reference = request_json["reference"]
            if 'value' in request_json:
                value = request_json["value"]
            uid_obj = get_uid_obj(reference, value)
            if uid_obj is None:
                return json_response({
                    "status": "error",
                    "error": "couldn't fetch uid to perform deletion"
                })
            if uid_obj is False:
                return json_response({
                    "status": "error",
                    "error": "no node found with the provided specification"
                })
            uid = uid_obj['uid']
        else:
            uid = request_json['uid']
        node_obj = {
            'uid': uid
        }
        assigned = txn.mutate(del_obj=node_obj)
        txn.commit()
    finally:
        txn.discard()
    return json_response({
        "status": "success",
        "message": "Node with uid <"+uid+"> successfully deleted"
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
    name = request_json.get("name")
    email = request_json.get("email")
    age = int(request_json.get("age", 0))
    referrer = request_json.get("referrer")
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
    res = get_uid_obj("salesman.email", email)
    print("res: ", res)
    if isinstance(res, dict):
        return json_response({
            "status": "warning",
            "message": "salesman with the provided email id already exists",
            "data": res
        })
    new_obj = salesman_object
    if referrer:
        referrer_obj = get_uid_obj("salesman.email", referrer)
        if referrer_obj is None or not(isinstance(referrer_obj, dict)):
            return json_response({
                "status": "error",
                "error": "error occurred while fetching referrer id"
            })
        referrer_uid = referrer_obj['uid']
        new_obj = {
            'uid': referrer_uid,
            'referred': salesman_object
        }
    print("New user object: ", new_obj)
    uids = create_data(myobj=new_obj)
    print("uids: ", uids)
    uid = uids.get('blank-0')
    if uid is None:
        return json_response({
            "status": "error",
            "error": "unable to create salesman node"
        })
    salesman_object['uid'] = uid
    return json_response({
        "status": "success",
        "message": "successfully created new salesman",
        "data": removeDotFromKey(salesman_object)
    })

# Queries a new Salesman Node.
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
    if 'all' in query_response and len(query_response['all'])<=0:
        return json_response({
            "status": "error",
            "error": "no salesman found with specified email"
        })
    query = json.dumps(query_response)
    print("query: ",query)
    # query=re.sub(r'"\w+.name"','"name"',query)
    # query=re.sub(r'"\w+.age"','"age"',query)
    # query=re.sub(r'"\w+.email"','"email"',query)
    new_query=re.sub(r'"(\w+).(name|age|email)"', r'"\2"', query)
    newobj = json.loads(new_query)
    print("newobj: ", newobj)
    response = {
        "status": "success",
        "data": newobj
    }
    return json_response(response)

# Creating a new Store Node.
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
    print("store_obj: ", store_obj)
    res = create(store_obj, reference='store.name')
    print("res: ", res)
    if res is None:
        return json_response({
            "status": "error",
            "error": "error while creating new store"
        })
    elif isinstance(res, str) or isinstance(res, unicode):
        store_obj['uid'] = res
        return json_response({
            "status": "warning",
            "message": "store name already exists",
            "data": removeDotFromKey(store_obj)
        })
    store_obj['uid'] = res['uid']
    return json_response({
        "status": "success",
        "message": "successfully created store",
        "data": removeDotFromKey(store_obj)
    })

# Creating a new Sales Node and child nodes
# If child nodes are already present, sales node simply creates an edge to/from 
@app.route("/create-sales", methods=['POST'])
def sales():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    invoice_no = request_json.get("invoice_no")
    item = request_json.get("item")
    store = request_json.get("store")
    location = request_json.get("location")
    price = int(request_json.get("price", 0))
    quantity = int(request_json.get("quantity", 0))
    salesman_email = request_json.get("salesman_email")
    customer_email = request_json.get("customer_email")
    categories = request_json.get("category")
    total_amount = int(request_json.get("total_amount", price*quantity))
    if not(item and store and salesman_email and customer_email and categories):
        return json_response({
            "status": "error",
            "error": "required fields not provided"
        })
    if not invoice_no:
        invoice_no = random.sample(range(1, 9999999), 1)[0]
    category = []
    out_category = []
    output_obj = {}
    print("categories: ", categories)
    for cat in categories:
        cat_uid = get_uid_obj("category.name", cat);
        if cat_uid is None or cat_uid is False:
            category.append({'category.name': cat})
            out_category.append({'name': cat})
        else:
            category.append({'uid': cat_uid["uid"]})
            out_category.append({'uid': cat_uid["uid"], 'name': cat})
    store_uid = get_uid_obj("store.name", store);
    out_store = {"uid": store_uid["uid"],"name": store,"location": location} if store_uid else {"name": store,"location": location}
    store = {"uid": store_uid["uid"]} if store_uid else {"store.name": store,"location": location}
    product_uid = get_uid_obj("product.name", item);
    out_item = {"uid": product_uid["uid"], 'name': item}  if product_uid else {"name": item}
    item = {"uid": product_uid["uid"]} if product_uid else {"product.name": item}
    print("category: ", category)
    item["category"] = category
    sales_obj = {
        "invoice_no": invoice_no,
        "item": item,
        "store": store,
        "price": price,
        "quantity": quantity,
        "total_amount": total_amount
    }
    print("out_category: ", out_category)
    out_item['category']=out_category
    output_obj = {
        "invoice_no": invoice_no,
        "item": [out_item],
        "store": [out_store],
        "price": price,
        "quantity": quantity,
        "total_amount": total_amount
    }
    print("\noutput_obj: ", str(output_obj))
    print("\nsales_obj: ", str(sales_obj))
    uid = create_sales(customer_email, sales_obj, salesman_email)
    if uid is None:
        return json_response({
            "status": "error",
            "error": "error occurred while creating sales"
        })
    if uid is False:
        return json_response({
            "status": "error",
            "error": "customer/salesman is not pre-registered"
        })
    sales_obj['uid'] = uid
    output_obj['uid'] = uid
    return json_response({
        "status": "success",
        "message": "successfully created sales under a salesman",
        "data": output_obj
    })

# Creates Salesman Node.
@app.route("/create-customer", methods=['POST'])
def create_customer():
    request_json = request.get_json(force=True)
    print("request_json: ", request_json)
    if request_json is None:
        return json_response({
            "status": "error",
            "error": "no payload found"
        })
    name = request_json.get("name")
    email = request_json.get("email")
    age = int(request_json.get("age", 0))
    if not(name and email and age):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    customer_object = {
        'customer.email': email,
        'customer.name': name,
        'customer.age': age,
    }
    res = get_uid_obj("customer.email", email)
    print("res: ", res)
    if isinstance(res, dict):
        return json_response({
            "status": "warning",
            "message": "customer with the provided email id already exists",
            "data": removeDotFromKey(res)
        })
    uids = create_data(myobj=customer_object)
    print("uids: ", uids)
    uid = uids.get('blank-0')
    if uid is None:
        return json_response({
            "status": "error",
            "error": "unable to create salesman node"
        })
    customer_object['uid'] = uid
    print("customer_object: ", customer_object)
    return json_response({
        "status": "success",
        "message": "successfully created new salesman",
        "data": removeDotFromKey(customer_object)
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)