# Salesman node
name: string @index(term) .
email: string @index(exact) .
age: int @index(int) .
sold: uid @count @reverse .
referred: uid @count @reverse .

# Sales node
invoice_no: int @index(int) .
item: string @index(term) .
price: int @index(int) .
quantity: int @index(int) .
total_amount: int @index(int) .
store: string @index(term) .