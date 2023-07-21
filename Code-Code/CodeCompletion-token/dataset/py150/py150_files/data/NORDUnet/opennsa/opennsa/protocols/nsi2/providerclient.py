"""
Web Service protocol for OpenNSA.

Note: This is the provider client, i.e. it speak to requester services

Author: Henrik Thostrup Jensen <htj@nordu.net>
Copyright: NORDUnet (2011-2013)
"""

from opennsa import constants as cnt
from opennsa.shared import xmlhelper
from opennsa.protocols.shared import minisoap, httpclient
from opennsa.protocols.nsi2 import helper, queryhelper
from opennsa.protocols.nsi2.bindings import actions, nsiconnection, p2pservices



class ProviderClient:

    def __init__(self, ctx_factory=None):

        self.ctx_factory = ctx_factory


    def _genericConfirm(self, element_name, requester_url, action, correlation_id, requester_nsa, provider_nsa, connection_id):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        confirm = nsiconnection.GenericConfirmedType(connection_id)
        body_element   = confirm.xml(element_name)

        payload = minisoap.createSoapPayload(body_element, header_element)

        def gotReply(data):
            # for now we just ignore this, as long as we get an okay
            return

        d = httpclient.soapRequest(requester_url, action, payload, ctx_factory=self.ctx_factory)
        d.addCallbacks(gotReply) #, errReply)
        return d


    def _genericFailure(self, requester_url, action, message_name, requester_nsa, provider_nsa, correlation_id,
                        connection_id, connection_states, err):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        active, version, consistent = connection_states[3]
        data_plane_state = nsiconnection.DataPlaneStatusType(active, version, consistent)
        connection_states = nsiconnection.ConnectionStatesType(connection_states[0], connection_states[1], connection_states[2], data_plane_state)

        se = helper.createServiceException(err, provider_nsa)

        failure = nsiconnection.GenericFailedType(connection_id, connection_states, se)

        body_element = failure.xml(message_name)

        payload = minisoap.createSoapPayload(body_element, header_element)

        def gotReply(data):
            # for now we just ignore this, as long as we get an okay
            return

        d = httpclient.soapRequest(requester_url, action, payload, ctx_factory=self.ctx_factory)
        d.addCallbacks(gotReply) #, errReply)
        return d


    def reserveConfirmed(self, nsi_header, connection_id, global_reservation_id, description, criteria):

        header_element = helper.createRequesterHeader(nsi_header.requester_nsa, nsi_header.provider_nsa, correlation_id=nsi_header.correlation_id)

        schedule = nsiconnection.ScheduleType(
            xmlhelper.createXMLTime(criteria.schedule.start_time) if criteria.schedule.start_time is not None else None,
            xmlhelper.createXMLTime(criteria.schedule.end_time)   if criteria.schedule.end_time   is not None else None
        )

        sd = criteria.service_def

        # we only support p2p for now
        p2p = p2pservices.P2PServiceBaseType(sd.capacity, sd.directionality, sd.symmetric, sd.source_stp.urn(), sd.dest_stp.urn(), None, [])

        criteria = nsiconnection.ReservationConfirmCriteriaType(criteria.revision, schedule, cnt.EVTS_AGOLE, str(p2pservices.p2ps), p2p)

        reserve_conf = nsiconnection.ReserveConfirmedType(connection_id, global_reservation_id, description, criteria)

        body_element = reserve_conf.xml(nsiconnection.reserveConfirmed)
        payload = minisoap.createSoapPayload(body_element, header_element)

        def gotReply(data):
            # we don't really do anything about these
            return ""

        d = httpclient.soapRequest(nsi_header.reply_to, actions.RESERVE_CONFIRMED, payload, ctx_factory=self.ctx_factory)
        d.addCallbacks(gotReply) #, errReply)
        return d


    def reserveFailed(self, nsi_header, connection_id, connection_states, err):

        return self._genericFailure(nsi_header.reply_to, actions.RESERVE_FAILED, nsiconnection.reserveFailed,
                                    nsi_header.requester_nsa, nsi_header.provider_nsa, nsi_header.correlation_id,
                                    connection_id, connection_states, err)


    def reserveCommitConfirmed(self, requester_url, requester_nsa, provider_nsa, correlation_id, connection_id):

        return self._genericConfirm(nsiconnection.reserveCommitConfirmed, requester_url, actions.RESERVE_COMMIT_CONFIRMED,
                                    correlation_id, requester_nsa, provider_nsa, connection_id)


    def reserveCommitFailed(self, nsi_header, connection_id, connection_states, err):

        return self._genericFailure(nsi_header.reply_to, actions.RESERVE_COMMIT_FAILED, nsiconnection.reserveCommitFailed,
                                    nsi_header.requester_nsa, nsi_header.provider_nsa, nsi_header.correlation_id,
                                    connection_id, connection_states, err)


    def reserveAbortConfirmed(self, requester_url, requester_nsa, provider_nsa, correlation_id, connection_id):

        return self._genericConfirm(nsiconnection.reserveAbortConfirmed, requester_url, actions.RESERVE_ABORT_CONFIRMED,
                                    correlation_id, requester_nsa, provider_nsa, connection_id)


    def provisionConfirmed(self, requester_url, correlation_id, requester_nsa, provider_nsa, connection_id):

        return self._genericConfirm(nsiconnection.provisionConfirmed, requester_url, actions.PROVISION_CONFIRMED,
                                    correlation_id, requester_nsa, provider_nsa, connection_id)


    def releaseConfirmed(self, requester_url, correlation_id, requester_nsa, provider_nsa, connection_id):

        return self._genericConfirm(nsiconnection.releaseConfirmed, requester_url, actions.RELEASE_CONFIRMED,
                                    correlation_id, requester_nsa, provider_nsa, connection_id)


    def terminateConfirmed(self, requester_url, correlation_id, requester_nsa, provider_nsa, connection_id):

        return self._genericConfirm(nsiconnection.terminateConfirmed, requester_url, actions.TERMINATE_CONFIRMED,
                                    correlation_id, requester_nsa, provider_nsa, connection_id)

    # notifications

    def reserveTimeout(self, requester_url, requester_nsa, provider_nsa, correlation_id,
                       connection_id, notification_id, timestamp, timeout_value, originating_connection_id, originating_nsa):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        reserve_timeout = nsiconnection.ReserveTimeoutRequestType(connection_id, notification_id, xmlhelper.createXMLTime(timestamp), timeout_value, originating_connection_id, originating_nsa)

        body_element = reserve_timeout.xml(nsiconnection.reserveTimeout)

        payload = minisoap.createSoapPayload(body_element, header_element)

        d = httpclient.soapRequest(requester_url, actions.RESERVE_TIMEOUT, payload, ctx_factory=self.ctx_factory)
        return d


    def dataPlaneStateChange(self, requester_url, requester_nsa, provider_nsa, correlation_id,
                             connection_id, notification_id, timestamp, active, version, consistent):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        data_plane_status = nsiconnection.DataPlaneStatusType(active, version, consistent)
        dps = nsiconnection.DataPlaneStateChangeRequestType(connection_id, notification_id, xmlhelper.createXMLTime(timestamp), data_plane_status)

        body_element = dps.xml(nsiconnection.dataPlaneStateChange)

        payload = minisoap.createSoapPayload(body_element, header_element)

        d = httpclient.soapRequest(requester_url, actions.DATA_PLANE_STATE_CHANGE, payload, ctx_factory=self.ctx_factory)
        return d


    def errorEvent(self, requester_url, requester_nsa, provider_nsa, correlation_id,
                   connection_id, notification_id, timestamp, event, info, service_ex):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        if service_ex:
            nsa_id, connection_id, error_id, text, variables, child_ex = service_ex
            service_exception = nsiconnection.ServiceExceptionType(nsa_id, connection_id, error_id, text, None, None)
        else:
            service_exception = None

        org_connection_id = None
        org_nsa_id = None
        additional_info = None
        error_event = nsiconnection.ErrorEventType(connection_id, notification_id, xmlhelper.createXMLTime(timestamp), event,
                                                   org_connection_id, org_nsa_id, additional_info, service_exception)

        body_element = error_event.xml(nsiconnection.errorEvent)

        payload = minisoap.createSoapPayload(body_element, header_element)

        d = httpclient.soapRequest(requester_url, actions.ERROR_EVENT, payload, ctx_factory=self.ctx_factory)
        return d


    def querySummaryConfirmed(self, requester_url, requester_nsa, provider_nsa, correlation_id, reservations):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        qs_reservations = queryhelper.buildQuerySummaryResultType(reservations)
        qsct = nsiconnection.QuerySummaryConfirmedType(qs_reservations)

        payload = minisoap.createSoapPayload(qsct.xml(nsiconnection.querySummaryConfirmed), header_element)
        d = httpclient.soapRequest(requester_url, actions.QUERY_SUMMARY_CONFIRMED, payload, ctx_factory=self.ctx_factory)
        return d


    def queryRecursiveConfirmed(self, requester_url, requester_nsa, provider_nsa, correlation_id, reservations):

        header_element = helper.createRequesterHeader(requester_nsa, provider_nsa, correlation_id=correlation_id)

        qr_reservations = queryhelper.buildQueryRecursiveResultType(reservations)
        qrct = nsiconnection.QueryRecursiveConfirmedType(qr_reservations)

        payload = minisoap.createSoapPayload(qrct.xml(nsiconnection.queryRecursiveConfirmed), header_element)
        d = httpclient.soapRequest(requester_url, actions.QUERY_RECURSIVE_CONFIRMED, payload, ctx_factory=self.ctx_factory)
        return d


#    def queryFailed(self, requester_url, correlation_id, requester_nsa, provider_nsa, error_msg):
#
#        print "CLIENT QUERY FAILED"
#        qft = self.client.createType('{http://schemas.ogf.org/nsi/2011/10/connection/types}QueryFailedType')
#        net = self.client.createType('{http://schemas.ogf.org/nsi/2011/10/connection/types}ServiceExceptionType')
#
#        qft.requesterNSA = requester_nsa
#        qft.providerNSA  = provider_nsa
#
#        net.errorId = 'QUERY_FAILURE'
#        net.text = error_msg
#        qft.serviceException = net
#
#        d = self.client.invoke(requester_url, 'queryFailed', correlation_id, qft)
#        return d

