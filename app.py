import pydgraph

def main():
    # Create a client stub
    client_stub = pydgraph.DgraphClientStub('localhost:9080')
    # Create a client
    client = pydgraph.DgraphClient(client_stub)

    # Drop all
    client.alter(pydgraph.Operation(drop_all=True))

    # Update schema
    schema = """
    email: string @index(exact) .
    name: string @index(term) .
    age: int .
    referred: uid @count @reverse .
    """

    op = pydgraph.Operation(schema=schema)
    client.alter(op)

    # Mutate
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
    txn = client.txn()
    try:
        assigned = txn.mutate(set_obj=myobj)
        txn.commit()

        print(assigned.uids)
    finally:
        txn.discard()

    # Query
    res = client.txn(read_only=True).query("""query all($a: string) {
    all(func: eq(email, $a)) {
        uid
        name
        email
        age
        referred {
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
    }
    }""", variables={'$a': 'arya@got.com'})

    print(res.json)

    # Close the client stub.
    client_stub.close()


if __name__ == '__main__':
    main()