import pydgraph

def main():
    # Create a client stub
    client_stub = pydgraph.DgraphClientStub('localhost:9080')
    # Create a client
    client = pydgraph.DgraphClient(client_stub)

    # Drop all
    client.alter(pydgraph.Operation(drop_all=True))

    # Close the client stub.
    client_stub.close()


if __name__ == '__main__':
    main()