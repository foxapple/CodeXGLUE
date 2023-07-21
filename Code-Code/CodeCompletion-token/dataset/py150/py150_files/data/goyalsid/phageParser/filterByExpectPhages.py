## March 7 2015

import time, os
from parsers.phage_file_2_2_30 import PhageDBReader

for fn in os.listdir("data/phages"):
    ext = fn.index('.')
    outfile = fn.replace(fn[ext+1:],("csv"))
    
    if __name__ == '__main__':
        current_milli_time = lambda: int(round(time.time() * 1000))
        parser = PhageDBReader('data/'+'phages/'+fn)
        # parser.write('output/blast-phagesdb.%s.csv' % current_milli_time())

        parser.filterByExpect('output/%s' % outfile)
