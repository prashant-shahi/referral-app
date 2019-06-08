import json
import pydgraph
from flask import Flask, flash, render_template, redirect, request, url_for, Response, abort

app = Flask(__name__)

def json_response(object):
    return Response(json.dumps(object), mimetype="application/json")

# Create a client stub.
def create_client_stub():
    return pydgraph.DgraphClientStub('localhost:9080')

# Create a client.
def create_client(client_stub):
    return pydgraph.DgraphClient(client_stub)

# Close the client stub.
def close_client_stub(client_stub):
    client_stub.close()

# Drop All - discard all data and start from a clean slate.
def drop_all(client):
    op = pydgraph.Operation(drop_all=True)
    print("Op: ", op)
    return client.alter(op)

# Set schema.
def set_schema(client, schema=None):
    if schema is None:
        schema = """
            email: string @index(exact) .
            name: string @index(term) .
            age: int .
            referred: uid @count @reverse .
        """
    op = pydgraph.Operation(schema=schema)
    return client.alter(op)

# Create data using JSON.
def create_data(client, myobj=None):
    # Create a new transaction.
    txn = client.txn()
    try:
        if myobj is None:
            myobj = {
                'name': 'Arya',
                'email': 'arya@got.com',
                'age': 18,
                'referred': [
                    {
                        'name': 'Bran',
                        'email': 'bran@got.com',
                        'age': 21
                    },
                    {
                        'name': 'Catelyn',
                        'email': 'catelyn@got.com',
                        'age': 39,
                        'referred': [
                            {
                               'name': 'Ned',
                                'email': 'ned@got.com',
                                'age': 41
                            }
                        ]
                    },
                    {
                        'name': 'Jon',
                        'email': 'jon@got.com',
                        'age': 26,
                        'referred': [
                            {
                               'name': 'Daenerys',
                                'email': 'daenerys@got.com',
                                'age': 28,
                                'referred': [
                                    {
                                       'name': 'Jorah',
                                        'email': 'jorah@got.com',
                                        'age': 30
                                    },
                                    {
                                       'name': 'Khal',
                                        'email': 'khal@got.com',
                                        'age': 32
                                    }
                                ]
                            },
                            {
                               'name': 'Ygritte',
                                'email': 'ygritte@got.com',
                                'age': 24
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
def query_data(client, query=None, email=None):
    if query == None:
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
        }
        }"""
    variables = {'$email': email}
    if email == None:
        variables = {'$email': 'arya@got.com'}
    res = client.txn(read_only=True).query(query, variables=variables)

    return json.loads(res.json)

def fetch_uid_func(email="arya@got.com"):
    query_response = query_data(client, email=email)
    print(query_response)
    if len(query_response['all']) <= 0:
        return
    user_obj = query_response['all'][0]
    print(user_obj)
    uid = user_obj['uid']
    print(uid)
    return uid

@app.route("/")
def index():
    return json_response({
        "server": "healthy"
    })

@app.route("/clear-all")
def clear_all():
    res = drop_all(client)
    print(res)
    return json_response({
        "status": "success",
        "message": "All"
    })

@app.route("/schema")
def schema():
    res = set_schema(client)
    print(res)
    return json_response({
        "status": "success",
        "message": "Schema has been successfully added"
    })

@app.route("/load-sample-data")
def load_sample():
    res = create_data(client)
    print(res)
    return json_response({
        "status": "success",
        "message": "Successfully loaded sample data"
    })

@app.route("/register", methods=['POST'])
def register():
    referrer = request.values.get("referrer")
    name = request.values.get("name")
    email = request.values.get("email")
    age = request.values.get("age")

    if not(name and email and age):
        return json_response({
            "status": "error",
            "error": "not all required data provided"
        })
    user_object = {
        'email': email,
        'name': name,
        'age': int(age)
    }
    if referrer is not None:
        uid = fetch_uid_func(referrer)
        user_object = {
            'uid': uid,
            'referred': user_object
        }

    print("New user object: ", user_object)
    creation_response = create_data(client, user_object)
    print("Creation response: ", creation_response)

    return json_response({
        "status": "success",
        "message": "User successfully registered"
    })

@app.route("/query")
def query():
    email = 'daenerys@got.com'
    query_response = query_data(client, email=email)
    response = {
        "status": "success",
        "data": query_response
    }
    return json_response(response)

@app.route("/fetch-uid", methods=['POST'])
def fetch_uid():
    email = request.values.get("email")
    uid = fetch_uid_func(email)
    if uid is None:
        return json_response({
            "status": "error",
            "error": "unregistered email id"
        })
    return json_response({
        "status": "success",
        "data": uid
    })

client_stub = create_client_stub()
client = create_client(client_stub)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)