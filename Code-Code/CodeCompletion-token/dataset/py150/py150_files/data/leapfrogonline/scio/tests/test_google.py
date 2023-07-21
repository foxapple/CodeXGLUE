import unittest

from lxml import etree
from nose.tools import eq_

import scio
from scio import gen
import helpers


class StubClient(scio.Client):
    sent = []

    def send(self, method, request):
        self.sent.append((method, request))


class TestBase(unittest.TestCase):
    clientClass = StubClient

    def setUp(self):
        StubClient.sent = []


class TestStatic(TestBase):

    def clientClass(self, wsdl):
        cl = scio.Client(wsdl)
        code = gen.gen(cl)
        ns = {}
        exec code in ns
        cls = type('StaticStub', (StubClient, ns['Client']), {})
        return cls()


class TestOldAdwords(TestBase):
    def test_parse_adwords(self):
        self.clientClass(helpers.support('adwords_campaignservice.wsdl', 'r'))

    def test_method_call_with_headers(self):
        client = self.clientClass(helpers.support('adwords_campaignservice.wsdl', 'r'))
        client.service.getCampaign(id=1,
                                   useragent="foo (mozilla)",
                                   email="bar@foo.com",
                                   clientEmail="buz@baz.com",
                                   clientCustomerId="5",
                                   developerToken="99dt",
                                   applicationToken="12at"
                                   )
        print StubClient.sent
        request = StubClient.sent[0][1].data
        print request
        assert 'email>' in request
        assert 'bar@foo.com' in request
        assert '99dt' in request
        assert '12at' in request
        assert 'foo (mozilla)'

    def test_get_all_campaigns(self):
        client = self.clientClass(helpers.support('adwords_campaignservice.wsdl', 'r'))
        client.service.getAllAdWordsCampaigns(dummy=0,
                                              useragent="foo (mozilla)",
                                              email="bar@foo.com",
                                              clientEmail="buz@baz.com",
                                              clientCustomerId="5",
                                              developerToken="99dt",
                                              applicationToken="12at")
        request = StubClient.sent[0][1].data
        print request
        assert 'getAllAdWordsCampaigns' in request
        parsed = etree.fromstring(request)
        assert parsed[1][0][0].tag == '{https://adwords.google.com/api/adwords/v12}dummy'

    def test_header_unmarshalling(self):
        client = scio.Client(
            helpers.support('adwords_trafficestimatorservice.wsdl', 'r'))
        response = helpers.support('adwords_response_example.xml', 'r').read()
        result, headers = client.handle_response(
            client.service.estimateKeywordList.method,
            response)
        print result
        print headers
        assert headers['operations'] == 1
        assert headers['responseTime'] == 10636
        assert headers['units'] == 1
        assert 'eb21e6667abb131c117b58086f75abbd' in headers['requestId']


class TestAdwordsv201101(TestBase):

    cm_tns = "https://adwords.google.com/api/adwords/cm/v201101"
    mcm_tns = "https://adwords.google.com/api/adwords/mcm/v201101"
    account = 'some.sandbox@example.com'
    auth_token = 'XXX'
    headers = dict(authToken=auth_token,
                   developerToken='%s++USD' % account)

    def test_serviced_accounts_service(self):
        # checking that elements in request are produced with
        # the correct namespaces attached.
        client = self.clientClass(
            helpers.support('ServicedAccountService.wsdl', 'r'))
        asel = client.type.ServicedAccountSelector(
            enablePaging=False)
        client.service.get(selector=asel, **self.headers)
        request = StubClient.sent[0][1].data
        print request
        parsed = etree.fromstring(request)
        assert parsed.find('.//{%s}authToken' % self.cm_tns) is not None
        assert parsed.find('.//{%s}authToken' % self.cm_tns).text == self.auth_token
        assert parsed.find('.//{%s}RequestHeader' % self.mcm_tns) is not None

    def test_infoservice_daterange_namespace(self):
        client = self.clientClass(helpers.support('InfoService.wsdl', 'r'))
        isel = client.type.InfoSelector(
            dateRange=client.type.DateRange(
                min='20111101', max='20111130'),
            apiUsageType='UNIT_COUNT')
        eq_(client.type.InfoSelector._namespace,
            "https://adwords.google.com/api/adwords/info/v201101")
        # container assigned to part in new namespace takes on
        # namespace from the context it is assigned to
        eq_(isel.dateRange._namespace,
            "https://adwords.google.com/api/adwords/info/v201101")
        # ... items in the type container keep their namespace
        eq_(isel.dateRange.min._namespace,
            "https://adwords.google.com/api/adwords/cm/v201101")


class TestOldAdwordsStatic(TestOldAdwords, TestStatic):
    pass


class TestAdwordsv201101Static(TestAdwordsv201101, TestStatic):
    pass
