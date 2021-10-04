from datetime import datetime, timedelta, tzinfo
import numpy as np

print("Hello world!")

# Use algovenv/Scripts/activate to activate the virtual environment in the algotrading folder
# And `deactivate` to deactivate it

# trail script
#from itertools import combinations
#
#for i in combinations(['StockA', 'StockB', 'StockC', 'Note'], 2):
#    print(i)

#print(np.cov(np.dot([10, 0, 7.5, 2.5], [0,2.5,7.5,10])))
##print(np.average([10, 0, 7.5, 2.5]))
#print(np.dot([10, 0, 7.5, 2.5], [0,2.5,7.5,10]))

a = np.array([10, 5, 32, 3]) / 5

#print(a)
#print(np.square(a))

#print(round(19.4545, 2))
some_date = datetime.now()
print(some_date)
some_date.utcnow()
print(some_date)
print(some_date.utcnow())
some_date = some_date.utcnow()
a = 0
for i in range(1000):
    a += i
then_date = datetime.now()
print(then_date - some_date)
secs = (then_date - some_date).total_seconds()
then_date.utcnow
print(secs)
print(type(secs))
print(secs > 60)
#print(datetime.now(tzinfo.utcoffset(timedelta())))
#import pytz
#a_date = datetime.strptime

print(then_date.utcfromtimestamp(11))
print("last")

print(datetime.now() - timedelta(hours=11))
print(datetime.utcnow)

#aus_date = datetime("2021-10-04 18:56:12.217000+11:00")
#print(aus_date)
