#put all your imports

#define all your variables and functions

#maybe define a second counter variable if you want here

#eg:
c2 = 0

#before the while true loop put this

with open("datafile.txt", "w") as file:
    file.write("Values 1, Value2, Value 3, etc\n")

#start while true loop

#make sure your secondary counter (if defined) is being incremented each loop iteration

c2 = c2 + 1

if c2 > 10: #here you used whichever counter you want to choose how frequently you want measurements
    with open("datafile.txt", "a") as file:
        file.write("{:d},{:.3f}\n".format(value1, value2, value3, etc))
    c2 = 0 #alwayse make sure your counter is alwayse reset after writing values
    

