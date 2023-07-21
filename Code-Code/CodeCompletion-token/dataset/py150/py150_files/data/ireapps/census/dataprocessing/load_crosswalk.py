#!/usr/bin/env python

import sys

from csvkit.unicsv import UnicodeCSVReader
from pymongo import objectid

import utils

if len(sys.argv) < 2:
    sys.exit('You must provide a state fips code and the filename of a CSV as an argument to this script.')

STATE_FIPS = sys.argv[1]
FILENAME = sys.argv[2]

collection = utils.get_geography_collection()

inserts = 0
row_count = 0

# Create dummy 2000->2010 crosswalk
if FILENAME == 'FAKE':
    for geography in collection.find({}, fields=['geoid', 'xwalk']):
        if 'xwalk' not in geography:
            geography['xwalk'] = {} 

        geography['xwalk'][geography['geoid']] = {
            'POPPCT00': 1.0,
            'HUPCT00': 1.0
        }

        collection.update({ '_id': objectid.ObjectId(geography['_id']) }, { '$set': { 'xwalk': geography['xwalk'] } }, safe=True) 
        row_count += 1
        inserts += 1
else:
    with open(FILENAME) as f:
        rows = UnicodeCSVReader(f)
        headers = rows.next()

        for row in rows:
            row_count += 1
            row_dict = dict(zip(headers, row))

            if row_dict['STATE10'] != STATE_FIPS:
                continue
            
            geography = collection.find_one({ 'geoid': row_dict['GEOID10'] }, fields=['xwalk'])

            if not geography:
                continue

            pop_pct_2000 = float(row_dict['POPPCT00']) / 100
            house_pct_2000 = float(row_dict['HUPCT00']) / 100

            if 'xwalk' not in geography:
                geography['xwalk'] = {} 

            geography['xwalk'][row_dict['GEOID00']] = {
                'POPPCT00': pop_pct_2000,
                'HUPCT00': house_pct_2000
            }

            collection.update({ '_id': objectid.ObjectId(geography['_id']) }, { '$set': { 'xwalk': geography['xwalk'] } }, safe=True) 
            inserts += 1

print "State: %s" % STATE_FIPS
print "File: %s" % FILENAME
print ' Row count: %i' % row_count
print ' Inserted: %i' % inserts

