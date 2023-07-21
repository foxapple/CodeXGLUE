#!/bin/python

#-------------------------------------------------------------------
#   The idea here is to overwrite the .vimTimes file by first 
#   reading all the data from it and then updating it with the
#   new data just added by vim.
#-------------------------------------------------------------------

f = open("/home/ejalbert/.vimTimes", "r")

times = dict() 
end = 0
start = 0

for line in f.readlines():
    split = line.split()
    if split[0][0] == '.':
        times[split[0]] = int(float(split[1]))
    elif split[0] == "exit":
        end = int(float(split[1]))
    elif split[0] == "open":
        start = int(float(split[1]))
    if end != 0 and start != 0:
        key =split[2][split[2].rfind('.'):] 
        if key in times:
            times[key] += end - start
        else:
            times[key] = end - start
        end = 0
        start = 0
f.close()

f = open("/home/ejalbert/.vimTimes", "w")

for key in times:
    f.write('%-30s %d \n' % (key, int(float(times[key]))))


