from twisted.internet import defer


class DUDRequester:

    def __init__(self):
        self.reserve_defer           = defer.Deferred()
        self.reserve_commit_defer    = defer.Deferred()
        self.reserve_abort_defer     = defer.Deferred()
        self.provision_defer         = defer.Deferred()
        self.release_defer           = defer.Deferred()
        self.terminate_defer         = defer.Deferred()
        self.query_summary_defer     = defer.Deferred()
        self.query_recursive_defer   = defer.Deferred()
        self.reserve_timeout_defer   = defer.Deferred()
        self.data_plane_change_defer = defer.Deferred()
        self.error_event_defer       = defer.Deferred()

    def reserveConfirmed(self, *args):
        self.reserve_defer.callback(args)

    def reserveFailed(self, *args):
        self.reserve_defer.errback(args)

    def reserveCommitConfirmed(self, *args):
        self.reserve_commit_defer.callback(args)

    def reserveCommitFailed(self, *args):
        self.reserve_commit_defer.callback(args)

    def reserveAbortConfirmed(self, *args):
        self.reserve_abort_defer.callback(args)

    def reserveAbortFailed(self, *args):
        self.reserve_abort_defer.errback(args)

    def provisionConfirmed(self, *args):
        self.provision_defer.callback(args)

    def releaseConfirmed(self, *args):
        self.release_defer.callback(args)

    def terminateConfirmed(self, *args):
        self.terminate_defer.callback(args)

    def querySummaryConfirmed(self, *args):
        self.query_summary_defer.callback(args)

    def queryRecursiveConfirmed(self, *args):
        self.query_recursive_defer.callback(args)

    def reserveTimeout(self, *args):
        self.reserve_timeout_defer.callback(args)

    def dataPlaneStateChange(self, *args):
        self.data_plane_change_defer.callback(args)

    def errorEvent(self, *args):
        self.error_event_defer.callback(args)

