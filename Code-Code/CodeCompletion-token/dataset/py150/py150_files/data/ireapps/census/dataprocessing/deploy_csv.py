#!/usr/bin/env python
"""
If data for a state is loaded into the Mongo DB (as in during the normal data processing pipeline), this script
can generate CSV exports collecting data for a specific SF1 table for all geographies of a given SUMLEV for a state.
Normally writes directly to S3, but is factored so that it shouldn't be hard to use to generate files on a local
file system.
"""
import sys

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from cStringIO import StringIO

import config
import utils
import gzip

import eventlet
eventlet.monkey_patch()

from csvkit.unicsv import UnicodeCSVWriter

POLICIES = ['public-read', 'private'] # should we add others?

def get_2000_top_level_counts(geography):
    try:
        pop2000 = geography['data']['2000']['P1']['P001001']
        hu2000 = geography['data']['2000']['H1']['H001001']
        return pop2000,hu2000
    except KeyError:
        return '',''
METADATA_HEADERS = ['STATE','COUNTY', 'CBSA', 'CSA', 'NECTA', 'CNECTA', 'NAME', 'POP100', 'HU100']

def deploy_table(state_fips, sumlev, table_id, policy='private'):

    if policy not in POLICIES:
        policy = 'private'
    s = StringIO()
    gz = gzip.GzipFile(fileobj=s, mode='wb')
    write_table_data(gz,state_fips,sumlev, table_id)
    gz.close()
    tokens = {'sumlev': sumlev, 'state': state_fips, 'table_id': table_id }
    c = S3Connection()
    bucket = c.get_bucket(config.S3_BUCKETS[ENVIRONMENT])
    k = Key(bucket)
    k.key = '%(state)s/all_%(sumlev)s_in_%(state)s.%(table_id)s.csv' % (tokens)
    k.set_contents_from_string(s.getvalue(), headers={ 'Content-encoding': 'gzip', 'Content-Type': 'text/csv' }, policy=policy)
    print "S3: wrote ",k.key," to ", ENVIRONMENT, " using policy ", policy

def write_table_data(flo, state_fips, sumlev, table_id):
    """Given a File-Like Object, write a table to it"""
    w = UnicodeCSVWriter(flo)

    metadata = fetch_table_label(table_id)

    header = ['GEOID', 'SUMLEV'] + METADATA_HEADERS + ['POP100.2000','HU100.2000']
    for key in sorted(metadata['labels']):
        header.extend([key,"%s.2000" % key])
    w.writerow(header)

    query = {'sumlev': sumlev, 'metadata.STATE': state_fips }
    collection = utils.get_geography_collection()
    for geography in collection.find(query):
        row = [geography['geoid'],geography['sumlev']]

        for h in METADATA_HEADERS:
            row.append(geography['metadata'][h])

        pop2000,hu2000 = get_2000_top_level_counts(geography)
        row.extend([pop2000,hu2000])

        for key in sorted(metadata['labels']):
            try:
                row.append(geography['data']['2010'][table_id][key])
            except KeyError, e:
                if table_id.startswith('PCO'):
                    print "No data for %s at %s" % (table_id, sumlev)
                    return
                raise e # don't otherwise expect this error, so raise it...
            try:
                row.append(geography['data']['2000'][table_id][key])
            except KeyError:
                row.append('')
        w.writerow(row)
    

def fetch_tables_and_labels():
    lc = utils.get_label_collection()
    return lc.find_one({'dataset': 'SF1'},fields=['tables'])['tables']

def fetch_table_label(table_id):
    return fetch_tables_and_labels()[table_id]

# BEGIN MAIN OPERATION
if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('You must specify 3 or 4 arguments to this script.\n%% %s [2 digit state FIPS code] [3 digit summary level] [staging|production] [policy (opt string default \'private\')]' % sys.argv[0])

    STATE_FIPS = sys.argv[1]
    SUMLEV = sys.argv[2]
    ENVIRONMENT = sys.argv[3]
    try:
        policy = sys.argv[4]
        if policy not in POLICIES:
            policy = 'private'
    except:
        policy='private'

    if SUMLEV not in config.SUMLEVS:
        sys.exit("Second argument must be a valid summary level as defined in config.SUMLEVS")

    # TODO 
    # this needs to be findable... ${DATAPROCESSING_DIR}/sf1_2010_data_labels.csv
    # reduce duplication between make_sf_data_2010_headers.py and utils.py
    # import a padded_label from utils... 
    tables = fetch_tables_and_labels()

    # non-eventlety
    for table_id in sorted(tables):
        deploy_table(STATE_FIPS, SUMLEV, table_id,policy)
        
    # eventlety
    # pile = eventlet.GreenPile(64)
    # for table_id in sorted(tables):
    #     pile.spawn(deploy_table, STATE_FIPS, SUMLEV, table_id,policy)
    # # Wait for all greenlets to finish
    # list(pile)
