import numpy as np

print("Hello world!")

# Use algovenv/Scripts/activate to activate the virtual environment in the algotrading folder
# And `deactivate` to deactivate it

# trail script
from itertools import combinations

for i in combinations(['StockA', 'StockB', 'StockC', 'Note'], 2):
    print(i)

#print(np.cov(np.dot([10, 0, 7.5, 2.5], [0,2.5,7.5,10])))
print(np.average([10, 0, 7.5, 2.5]))
print(np.dot([10, 0, 7.5, 2.5], [0,2.5,7.5,10]))

a = np.array([10, 5, 32, 3]) / 5

print(a)
print(np.square(a))