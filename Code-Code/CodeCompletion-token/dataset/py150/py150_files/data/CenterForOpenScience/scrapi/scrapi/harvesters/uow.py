'''
Harvester for Research Online @ University of Wollongong for the SHARE project

Example API call: http://ro.uow.edu.au/do/oai/?verb=ListRecords&metadataPrefix=oai_dc
'''
from __future__ import unicode_literals

from scrapi.base import OAIHarvester


class UowHarvester(OAIHarvester):
    short_name = 'uow'
    long_name = 'Research Online @ University of Wollongong'
    url = 'http://ro.uow.edu.au'

    base_url = 'http://ro.uow.edu.au/do/oai/'
    property_list = ['date', 'source', 'identifier', 'type', 'format', 'setSpec']
    timezone_granularity = True
