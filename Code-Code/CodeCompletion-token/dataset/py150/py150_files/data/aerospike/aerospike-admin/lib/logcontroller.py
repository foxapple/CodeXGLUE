# Copyright 2013-2014 Aerospike, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from lib.controller import ShellController
from lib.controllerlib import *
from lib import terminal
from lib.view import CliView


def strip_string(search_str):
    search_str = search_str.strip()
    if search_str[0] == "\"" or search_str[0] == "\'":
        return search_str[1:len(search_str) - 1]
    else:
        return search_str

def clear_option_from_mods(self, option):
        for mod in self.modifiers:
            if mod in self.mods and option in self.mods[mod]:
                    self.mods[mod].remove(option)


def flip_keys(orig_data):
    new_data = {}
    for key1, data1 in orig_data.iteritems():
        if isinstance(data1, Exception):
            continue
        for key2, data2 in data1.iteritems():
            if key2 not in new_data:
                new_data[key2] = {}
            new_data[key2][key1] = data2

    return new_data

@CommandHelp('Aerospike Admin')
class LogRootController(BaseController):

    def __init__(
            self,
            seed_nodes=[
                ('127.0.0.1',
                 3000)],
            use_telnet=False,
            user=None,
            password=None,
            log_path=" "):
        super(
            LogRootController,
            self).__init__(
            seed_nodes=seed_nodes,
            use_telnet=use_telnet,
            user=user,
            password=password,
            log_path=log_path)
        self.controller_map = {
            'info': InfoController,
            'show': ShowController,
            '!': ShellController,
            'shell': ShellController,
            'loggrep': LogGrepController,
            'loglatency': LogLatencyController,
            'add': AddController,
            'remove': RemoveController,
            'list': ListController,
            'select': SelectController,
            'features': FeaturesController,
            'pager':PagerController}

    @CommandHelp('Terminate session')
    def do_exit(self, line):
        # This function is a hack for autocomplete
        return "EXIT"

    @CommandHelp(
        'Returns documentation related to a command',
        'for example, to retrieve documentation for the "info"',
        'command use "help info".')
    def do_help(self, line):
        self.executeHelp(line)


@CommandHelp(
    'The "info" command provides summary tables for various aspects',
    'of Aerospike functionality.')
class InfoController(CommandController):

    def __init__(self):
        self.modifiers = set()

    @CommandHelp(
        'Displays network, namespace, and xdr summary',
        'information.')
    def _do_default(self, line):
        self.do_network(line)
        self.do_namespace(line)
        self.do_xdr(line)

    # @CommandHelp('Displays summary information for the Aerospike service.')
    # def do_service(self, line):
    #     service_infos = self.logger.infoSummary(stanza='service')
    #
    #     for timestamp in sorted(service_infos.keys()):
    #         self.view.infoString(timestamp, service_infos[timestamp])

    @CommandHelp(
        'Displays network information for Aerospike.')
    def do_network(self, line):
        network_infos = self.logger.infoSummary(stanza='network')
        service_infos = self.logger.infoSummary(stanza='service')
        network_stats = self.logger.infoStatistics(stanza='service')
        for timestamp in sorted(network_stats.keys()):
            if not network_stats[timestamp]:
                try:
                    if service_infos[timestamp]:
                        self.view.infoString(timestamp, service_infos[timestamp])
                except:
                    pass
                try:
                    if network_infos[timestamp]:
                        self.view.infoString(timestamp, network_infos[timestamp])
                except:
                    pass
                continue
            logsnapshot_controller = self.logger.get_log_snapshot(timestamp=timestamp)
            builds = logsnapshot_controller.get_asd_build()
            versions = logsnapshot_controller.get_asd_version()
            self.view.infoNetwork(network_stats[timestamp], versions, builds, logsnapshot_controller, title_suffix=" (%s)"%(timestamp), **self.mods)

    @CommandHelp('Displays summary information for each namespace.')
    def do_namespace(self, line):
        ns_infos = self.logger.infoSummary(stanza='namespace')
        ns_stats = self.logger.infoStatistics(stanza='namespace')
        for timestamp in sorted(ns_stats.keys()):
            if not ns_stats[timestamp]:
                try:
                    if ns_infos[timestamp]:
                        self.view.infoString(timestamp, ns_infos[timestamp])
                except:
                    pass
                continue
            self.view.infoNamespace(flip_keys(ns_stats[timestamp]), self.logger.get_log_snapshot(timestamp=timestamp), title_suffix=" (%s)"%(timestamp), **self.mods)

    def convert_key_to_tuple(self, stats):
        for key in stats.keys():
            key_tuple = tuple(key.split())
            stats[key_tuple] = stats[key]
            del stats[key]

    @CommandHelp('Displays summary information for each set.')
    def do_set(self, line):
        set_infos = self.logger.infoSummary(stanza='sets')
        set_stats = self.logger.infoStatistics(stanza='sets')
        for timestamp in sorted(set_stats.keys()):
            if not set_stats[timestamp]:
                try:
                    if set_infos[timestamp]:
                        self.view.infoString(timestamp, set_infos[timestamp])
                except:
                    pass
                continue
            self.convert_key_to_tuple(set_stats[timestamp])
            self.view.infoSet(flip_keys(set_stats[timestamp]), self.logger.get_log_snapshot(timestamp=timestamp), title_suffix=" (%s)"%(timestamp), **self.mods)

    @CommandHelp('Displays summary information for Cross Datacenter',
        'Replication (XDR).')
    def do_xdr(self, line):
        xdr_infos = self.logger.infoSummary(stanza='xdr')
        xdr_stats = self.logger.infoStatistics(stanza='xdr')
        for timestamp in sorted(xdr_stats.keys()):
            if not xdr_stats[timestamp]:
                try:
                    if xdr_infos[timestamp]:
                        self.view.infoString(timestamp, xdr_infos[timestamp])
                except:
                    pass
                continue
            xdr_enable = {}
            logsnapshot_controller = self.logger.get_log_snapshot(timestamp=timestamp)
            builds = logsnapshot_controller.get_xdr_build()
            for xdr_node in xdr_stats[timestamp].keys():
                xdr_enable[xdr_node] = True

            self.view.infoXDR(xdr_stats[timestamp], builds, xdr_enable, logsnapshot_controller, title_suffix=" (%s)"%(timestamp), **self.mods)

    @CommandHelp('Displays summary information for each datacenter.')
    def do_dc(self, line):
        dc_infos = self.logger.infoSummary(stanza='dc')
        dc_stats = self.logger.infoStatistics(stanza='dc')
        dc_config = self.logger.infoGetConfig(stanza='dc')
        for timestamp in sorted(dc_stats.keys()):
            if not dc_stats[timestamp]:
                try:
                    if dc_infos[timestamp]:
                        self.view.infoString(timestamp, dc_infos[timestamp])
                except:
                    pass
                continue
            for node in dc_stats[timestamp].keys():
                if dc_stats[timestamp][node] and not isinstance(dc_stats[timestamp][node],Exception) and dc_config[timestamp][node] and not isinstance(dc_config[timestamp][node],Exception):
                    for dc in dc_stats[timestamp][node].keys():
                        dc_stats[timestamp][node][dc].update(dc_config[timestamp][node][dc])
                elif (not dc_stats[timestamp][node] or isinstance(dc_stats[timestamp][node],Exception)) and dc_config[timestamp][node] and not isinstance(dc_config[timestamp][node],Exception):
                    dc_stats[timestamp][node] = dc_config[timestamp][node]
            self.view.infoDC(flip_keys(dc_stats[timestamp]), self.logger.get_log_snapshot(timestamp=timestamp), title_suffix=" (%s)"%(timestamp), **self.mods)

    @CommandHelp('Displays summary information for Secondary Indexes (SIndex).')
    def do_sindex(self, line):
        sindex_infos = self.logger.infoSummary(stanza='sindex')
        sindex_stats = self.logger.infoStatistics(stanza='sindex')
        for timestamp in sorted(sindex_stats.keys()):
            if not sindex_stats[timestamp]:
                try:
                    if sindex_infos[timestamp]:
                        self.view.infoString(timestamp, sindex_infos[timestamp])
                except:
                    pass
                continue
            self.view.infoSIndex(sindex_stats[timestamp], self.logger.get_log_snapshot(timestamp=timestamp), title_suffix=" (%s)"%(timestamp), **self.mods)

@CommandHelp(
    '"show" is used to display Aerospike Statistics and',
    'configuration.')
class ShowController(CommandController):

    def __init__(self):
        self.controller_map = {
            'config': ShowConfigController,
            'statistics': ShowStatisticsController,
            'distribution': ShowDistributionController}
        self.modifiers = set()

    def _do_default(self, line):
        self.executeHelp(line)

@CommandHelp(
    '"show config" is used to display Aerospike configuration settings')
class ShowConfigController(CommandController):

    def __init__(self):
        self.modifiers = set(['like', 'diff'])

    @CommandHelp('Displays service, network, and namespace configuration')
    def _do_default(self, line):
        self.do_service(line)
        self.do_network(line)
        self.do_namespace(line)

    @CommandHelp('Displays service configuration')
    def do_service(self, line):
        service_configs = self.logger.infoGetConfig(stanza='service')

        for timestamp in sorted(service_configs.keys()):
            self.view.showConfig(
                "Service Configuration (%s)" %
                (timestamp),
                service_configs[timestamp], self.logger.get_log_snapshot(timestamp=timestamp),
                **self.mods)

    @CommandHelp('Displays network configuration')
    def do_network(self, line):
        service_configs = self.logger.infoGetConfig(stanza='network')

        for timestamp in sorted(service_configs.keys()):
            self.view.showConfig(
                "Network Configuration (%s)" %
                (timestamp),
                service_configs[timestamp],self.logger.get_log_snapshot(timestamp=timestamp),
                **self.mods)

    @CommandHelp('Displays namespace configuration')
    def do_namespace(self, line):
        ns_configs = self.logger.infoGetConfig(stanza='namespace')

        for timestamp in sorted(ns_configs.keys()):
            for ns, configs in ns_configs[timestamp].iteritems():
                self.view.showConfig(
                    "%s Namespace Configuration (%s)" %
                    (ns, timestamp), configs, self.logger.get_log_snapshot(timestamp=timestamp), **self.mods)

    @CommandHelp('Displays XDR configuration')
    def do_xdr(self, line):
        xdr_configs = self.logger.infoGetConfig(stanza='xdr')

        for timestamp in sorted(xdr_configs.keys()):
            self.view.showConfig(
                "XDR Configuration (%s)" %
                (timestamp),
                xdr_configs[timestamp],self.logger.get_log_snapshot(timestamp=timestamp),
                **self.mods)

    @CommandHelp('Displays datacenter configuration')
    def do_dc(self, line):
        dc_configs = self.logger.infoGetConfig(stanza='dc')

        for timestamp in sorted(dc_configs.keys()):
            for dc, configs in dc_configs[timestamp].iteritems():
                self.view.showConfig(
                    "%s DC Configuration (%s)" %
                    (dc, timestamp), configs,self.logger.get_log_snapshot(timestamp=timestamp),**self.mods)

@CommandHelp(
    '"distribution" is used to show the distribution of object sizes',
    'and time to live for node and a namespace.')
class ShowDistributionController(CommandController):

    def __init__(self):
        self.modifiers = set(['like'])

    @CommandHelp('Shows the distributions of Time to Live and Object Size'
                 , '  Options(only for Object Size distribution):'
                 , '    -b   - Displays byte wise distribution of Object Sizes if it is collected in collectinfo.')
    def _do_default(self, line):
        self.do_time_to_live(line)
        self.do_object_size(line)

    def _do_distribution(self, histogram_name, title, unit):
        histogram = self.logger.infoGetHistogram(histogram_name)
        for timestamp in sorted(histogram.keys()):
            #print "************************** %s for %s **************************" % (title, timestamp)
            self.view.showDistribution(title,
                histogram[timestamp],
                unit,
                histogram_name,self.logger.get_log_snapshot(timestamp=timestamp),
                title_suffix=" (%s)"%(timestamp), **self.mods)

    @CommandHelp('Shows the distribution of TTLs for namespaces')
    def do_time_to_live(self, line):
        return self._do_distribution('ttl', 'TTL Distribution', 'Seconds')

    @CommandHelp('Shows the distribution of Object sizes for namespaces'
                 , '  Options:'
                 , '    -b   - Displays byte wise distribution of Object Sizes if it is collected in collectinfo.')
    def do_object_size(self, line):
        if '-b' in line:
            histogram = self.logger.infoGetHistogram("objsz-b")
            for timestamp in histogram:
                self.view.showObjectDistribution('Object Size Distribution',histogram[timestamp], 'Bytes', 'objsz', 10, False,
                           self.logger.get_log_snapshot(timestamp=timestamp), title_suffix=" (%s)"%(timestamp), loganalyser_mode=True
                           , **self.mods)
        else:
            return self._do_distribution('objsz','Object Size Distribution','Record Blocks')

    @CommandHelp('Shows the distribution of Eviction TTLs for namespaces')
    def do_eviction(self, line):
        return self._do_distribution('evict','Eviction Distribution','Seconds')

@CommandHelp('Displays latency information for Aerospike server log.')
class LogLatencyController(CommandController):

    def __init__(self):
        self.modifiers = set()
        self.grepFile = GrepFile(False, self.modifiers)

    @CommandHelp(
        'Displays latency information for Aerospike server log.',
        '  Options:',
        '    -h <string>  - Histogram Name, MANDATORY - NO DEFAULT',
        '    -t <string>  - Analysis slice interval, default: 10,  e.g. 3600 or 1:00:00',
        '    -f <string>  - Log time from which to analyze e.g. head or "Sep 22 2011 22:40:14" or -3600 or -1:00:00,',
        '                   default: head',
        '    -d <string>  - Maximum duration for which to analyze, e.g. 3600 or 1:00:00',
        '    -b <string>  - Number of buckets to display, default: 3',
        '    -n <string>  - Comma separated node numbers. You can get these numbers by list command. Ex. : -n \'1,2,5\'',
        '                   If not set then runs on all server logs in selected list.',
        '    -e <string>  - Show 0-th then every e-th bucket, default: 3',
        '    -o           - Showing original time range for slices. Default is showing time with seconds value rounded to next nearest multiple of 10.')
    def _do_default(self, line):
        self.grepFile.do_latency(line)

@CommandHelp('Displays statistics for Aerospike components.')
class ShowStatisticsController(CommandController):

    def __init__(self):
        self.modifiers = set(['like','for'])

    def need_to_show_total(self, line):
        show_total = False
        try:
            if "-t" in line:
                show_total = True
                clear_option_from_mods("-t")
        except:
            pass
        return show_total

    @CommandHelp('Displays bin, set, service, and namespace statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end. It contains node wise sum for statistics.')
    def _do_default(self, line):
        self.do_bins(line)
        self.do_sets(line)
        self.do_service(line)
        self.do_namespace(line)

    @CommandHelp('Displays service statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_service(self, line):
        show_total = self.need_to_show_total(line)
        service_stats = self.logger.infoStatistics(stanza="service")
        for timestamp in sorted(service_stats.keys()):
            self.view.showConfig(
                "Service Statistics (%s)" %
                (timestamp),
                service_stats[timestamp],self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total,
                **self.mods)

    @CommandHelp('Displays namespace statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_namespace(self, line):
        show_total = self.need_to_show_total(line)
        ns_stats = self.logger.infoStatistics(stanza="namespace")

        for timestamp in sorted(ns_stats.keys()):
            namespace_list = util.filter_list(ns_stats[timestamp].keys(), self.mods['for'])
            for ns in sorted(namespace_list):
                stats = ns_stats[timestamp][ns]
                self.view.showStats(
                    "%s Namespace Statistics (%s)" %
                    (ns, timestamp), stats, self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total, **self.mods)

    @CommandHelp('Displays set statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_sets(self, line):
        show_total = self.need_to_show_total(line)
        set_stats = self.logger.infoStatistics(stanza="sets")
        for timestamp in sorted(set_stats.keys()):
            if not set_stats[timestamp]:
                continue
            namespace_list = [ns_set.split()[0] for ns_set in set_stats[timestamp].keys()]
            namespace_list = util.filter_list(namespace_list, self.mods['for'])
            for ns_set, stats in set_stats[timestamp].iteritems():
                if ns_set.split()[0] not in namespace_list:
                    continue
                self.view.showStats(
                    "%s Set Statistics (%s)" %
                    (ns_set, timestamp), stats, self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total, **self.mods)

    @CommandHelp('Displays bin statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_bins(self, line):
        show_total = self.need_to_show_total(line)
        new_bin_stats = self.logger.infoStatistics(stanza="bins")
        for timestamp in sorted(new_bin_stats.keys()):
            if not new_bin_stats[timestamp] or isinstance(new_bin_stats[timestamp], Exception) :
                continue
            namespace_list = util.filter_list(new_bin_stats[timestamp].keys(), self.mods['for'])
            for ns, stats in new_bin_stats[timestamp].iteritems():
                if ns not in namespace_list:
                    continue
                self.view.showStats(
                    "%s Bin Statistics (%s)" %
                    (ns, timestamp), stats, self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total, **self.mods)

    @CommandHelp('Displays XDR statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_xdr(self, line):
        show_total = self.need_to_show_total(line)
        xdr_stats = self.logger.infoStatistics(stanza="xdr")
        for timestamp in sorted(xdr_stats.keys()):
            self.view.showConfig(
                "XDR Statistics (%s)" %
                (timestamp),
                xdr_stats[timestamp], self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total,
                **self.mods)

    @CommandHelp('Displays datacenter statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_dc(self, line):
        show_total = self.need_to_show_total(line)
        dc_stats = self.logger.infoStatistics(stanza="dc")
        for timestamp in sorted(dc_stats.keys()):
            for dc, stats in dc_stats[timestamp].iteritems():
                self.view.showStats(
                    "%s DC Statistics (%s)" %
                    (dc, timestamp), stats, self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total, **self.mods)

    @CommandHelp('Displays sindex statistics'
                 , '  Options:'
                 , '    -t - Set to show total column at the end.')
    def do_sindex(self, line):
        show_total = self.need_to_show_total(line)
        sindex_stats = self.logger.infoStatistics(stanza="sindex")
        for timestamp in sorted(sindex_stats.keys()):
            if not sindex_stats[timestamp] or isinstance(sindex_stats[timestamp], Exception):
                continue
            namespace_list = [ns_set_sindex.split()[0] for ns_set_sindex in sindex_stats[timestamp].keys()]
            namespace_list = util.filter_list(namespace_list, self.mods['for'])
            for sindex, stats in sindex_stats[timestamp].iteritems():
                if sindex.split()[0] not in namespace_list:
                    continue
                self.view.showStats(
                    "%s Sindex Statistics (%s)" %
                    (sindex, timestamp), stats, self.logger.get_log_snapshot(timestamp=timestamp), show_total=show_total, **self.mods)

@CommandHelp('Displays features used in Aerospike cluster.')
class FeaturesController(CommandController):

    def __init__(self):
        self.modifiers = set(['like'])

    def _do_default(self, line):
        service_stats = self.logger.infoStatistics(stanza="service")
        ns_stats = self.logger.infoStatistics(stanza="namespace")
        for timestamp in sorted(service_stats.keys()):
            features = {}
            for node, stats in service_stats[timestamp].iteritems():
                features[node] = {}
                features[node]["KVS"] = "NO"
                try:
                    if int(
                            stats["stat_read_reqs"]) > 0 or int(
                            stats["stat_write_reqs"]) > 0:
                        features[node]["KVS"] = "YES"
                except:
                    pass

                features[node]["UDF"] = "NO"
                try:
                    if int(
                            stats["udf_read_reqs"]) > 0 or int(
                            stats["udf_write_reqs"]) > 0:
                        features[node]["UDF"] = "YES"
                except:
                    pass

                features[node]["BATCH"] = "NO"
                try:
                    if int(stats["batch_initiate"]) > 0:
                        features[node]["BATCH"] = "YES"
                except:
                    pass

                features[node]["SCAN"] = "NO"
                try:
                    if int(stats["tscan_initiate"]) > 0:
                        features[node]["SCAN"] = "YES"
                except:
                    pass

                features[node]["SINDEX"] = "NO"
                try:
                    if int(stats["sindex-used-bytes-memory"]) > 0:
                        features[node]["SINDEX"] = "YES"
                except:
                    pass

                features[node]["QUERY"] = "NO"
                try:
                    if int(
                            stats["query_reqs"]) > 0 or int(
                            stats["query_success"]) > 0:
                        features[node]["QUERY"] = "YES"
                except:
                    pass

                features[node]["AGGREGATION"] = "NO"
                try:
                    if int(
                            stats["query_agg"]) > 0 or int(
                            stats["query_agg_success"]) > 0:
                        features[node]["AGGREGATION"] = "YES"
                except:
                    pass

                try:
                    if (timestamp in ns_stats):
                        namespace_stats = ns_stats[timestamp]
                        for ns in namespace_stats:
                            features[node]["LDT(%s)"%(ns)] = "NO"
                            try:
                                if int(namespace_stats[ns][node].get("ldt-writes","0")) > 0 or int(namespace_stats[ns][node].get("ldt_writes","0")) > 0 or int(
                                        namespace_stats[ns][node].get("ldt-reads","0")) > 0 or int(namespace_stats[ns][node].get("ldt_reads","0")) > 0 or int(
                                        namespace_stats[ns][node].get("ldt-deletes","0")) > 0 or int(namespace_stats[ns][node].get("ldt_deletes","0")) > 0:
                                        features[node]["LDT(%s)" % (ns)] = "YES"
                            except:
                                pass
                except:
                    pass

                features[node]["XDR ENABLED"] = "NO"
                try:
                    if int(stats["stat_read_reqs_xdr"]) > 0:
                        features[node]["XDR ENABLED"] = "YES"
                except:
                    pass

                features[node]["XDR DESTINATION"] = "NO"
                try:
                    if int(stats["stat_write_reqs_xdr"]) > 0:
                        features[node]["XDR DESTINATION"] = "YES"
                except:
                    pass

            self.view.showConfig(
                "(%s) Features" %
                (timestamp),
                features,
                self.logger.get_log_snapshot(timestamp=timestamp),
                **self.mods)

@CommandHelp('Displays and analyse lines matched with input strings.')
class LogGrepController(CommandController):

    def __init__(self):
        self.controller_map = {
            'server': LogGrepServerController,
            'cluster': LogGrepClusterController}
        self.modifiers = set()

    def _do_default(self, line):
        self.executeHelp(line)

@CommandHelp('Displays all lines from server logs matched with input pattern, count those lines and analyse them.')
class LogGrepServerController(CommandController):

    def __init__(self):
        self.modifiers = set()
        self.grepFile = GrepFile(False, self.modifiers)

    def _do_default(self, line):
        self.grepFile.do_show(line)

    @CommandHelp(
        'Displays all lines from server logs matched with input strings.',
        '  Options:',
        '    -s <string>  - Space seprated Strings to search in log files, MANDATORY - NO DEFAULT',
        '                   Format -s \'string1\' \'string2\'... \'stringn\'',
        '    -a           - Set \'AND\'ing of search strings (provided with -s): Finding lines with all serach strings in it.',
        '                   Default is \'OR\'ing: Finding lines with atleast one search string in it.',
        '    -v <string>  - The non-matching string.',
        '    -n <string>  - Comma separated node numbers. You can get these numbers by list command. Ex. : -n \'1,2,5\'.',
        '                   If not set then runs on all server logs in selected list.',
        '    -f <string>  - Log time from which to analyze.',
        '                   May use the following formats:  \'Sep 22 2011 22:40:14\', -3600, or \'-1:00:00\'.',
        '                   Default: head',
        '    -d <string>  - Maximum time period to analyze.',
        '                   May use the following formats: 3600 or 1:00:00.',
        '    -u           - Set to find only for unique lines.',
        '    -i           - Perform case insensitive matching. By default it is case sensitive.')
    def do_show(self, line):
        self.grepFile.do_show(line)

    @CommandHelp(
        'Displays count of lines from server logs matched with input strings.',
        '  Options:',
        '    -s <string>  - Space seprated Strings to search in log files, MANDATORY - NO DEFAULT',
        '                   Format -s \'string1\' \'string2\'... \'stringn\'',
        '    -a           - Set \'AND\'ing of search strings (provided with -s): Finding lines with all serach strings in it.',
        '                   Default is \'OR\'ing: Finding lines with atleast one search string in it.',
        '    -n <string>  - Comma separated node numbers. You can get these numbers by list command. Ex. : -n \'1,2,5\'.',
        '                   If not set then runs on all server logs in selected list.',
        '    -f <string>  - Log time from which to analyze.',
        '                   May use the following formats:  \'Sep 22 2011 22:40:14\', -3600, or \'-1:00:00\'.',
        '                   Default: head',
        '    -d <string>  - Maximum time period to analyze.',
        '                   May use the following formats: 3600 or 1:00:00.',
        '    -v <string>  - The non-matching string.',
        '    -u           - Set to find only for unique lines.',
        '    -i           - Perform case insensitive matching. By default it is case sensitive.')
    def do_count(self, line):
        self.grepFile.do_count(line)

    @CommandHelp(
        'Displays set of values and difference between consecutive values for input string in server logs.',
        'Currently it is working for following KEY and VALUE patterns:',
        '        1) KEY<space>VALUE',
        '        2) KEY<space>(VALUE)',
        '        3) KEY<space>(Comma separated VALUE list)',
        '        4) KEY<space>(VALUE',
        '        5) VALUE1<space>(VALUE2)<space>KEY',
        '  Options:',
        '    -s <string>  - The String to search in log files, MANDATORY - NO DEFAULT',
        '    -v <string>  - The non-matching string.',
        '    -n <string>  - Comma separated node numbers. You can get these numbers by list command. Ex. : -n \'1,2,5\'.',
        '                   If not set then runs on all server logs in selected list.',
        '    -f <string>  - Log time from which to analyze.',
        '                   May use the following formats:  \'Sep 22 2011 22:40:14\', -3600, or \'-1:00:00\'.',
        '                   Default: head',
        '    -d <string>  - Maximum time period to analyze.',
        '                   May use the following formats: 3600 or 1:00:00.',
        '    -k <string>  - Show 0-th then every k-th result. default: 1.',
        '    -l <string>  - Show results with at least one diff value greater than or equal to limit.',
        '    -t <string>  - Analysis slice interval in seconds or time format. default: 10 seconds.',
        '    -i           - Perform case insensitive matching. By default it is case sensitive.')
    def do_diff(self, line):
        self.grepFile.do_diff(line)

class GrepFile(CommandController):

    def __init__(self, grep_cluster, modifiers):
        self.grep_cluster = grep_cluster
        self.modifiers = modifiers

    def do_show(self, line):
        if not line:
            raise ShellException("Could not understand grep request, " +
                                 "see 'help grep'")

        mods = self.parseModifiers(line)
        line = mods['line']

        tline = line[:]
        search_strs = []
        ignore_str = ""
        start_tm = "head"
        duration = ""
        sources = []
        unique = False
        is_and = False
        is_casesensitive = True
        reading_search_strings = False
        search_string_read = False
        while tline:
            search_string_read = False
            word = tline.pop(0)
            if word == '-s':
                try:
                    search_strs.append(strip_string(tline.pop(0)))
                    reading_search_strings = True
                    search_string_read = True
                except:
                    search_strs = []
            elif word == '-a':
                is_and = True
            elif word == '-v':
                ignore_str = tline.pop(0)
                ignore_str = strip_string(ignore_str)
            elif word == '-u':
                unique = True
            elif word == '-i':
                is_casesensitive = False
            elif word == '-f' and not self.grep_cluster:
                start_tm = tline.pop(0)
                start_tm = strip_string(start_tm)
            elif word == '-d' and not self.grep_cluster:
                duration = tline.pop(0)
                duration = strip_string(duration)
            elif word == '-n':
                try:
                    sources = [
                        int(i) for i in strip_string(
                            tline.pop(0)).split(",")]
                except:
                    sources = []
            elif reading_search_strings:
                try:
                    search_strs.append(strip_string(word))
                except:
                    pass
                search_string_read = True
            else:
                raise ShellException(
                    "Do not understand '%s' in '%s'" % (word, " ".join(line)))
            if not search_string_read:
                reading_search_strings = False

        if search_strs:
            files = self.logger.get_files_by_index(
                self.grep_cluster,
                sources)
            for timestamp in sorted(files.keys()):
                grepRes = self.logger.grep(
                    files[timestamp],
                    search_strs,
                    ignore_str,
                    unique,
                    self.grep_cluster,
                    start_tm,
                    duration,
                    is_and, is_casesensitive)
                merged_res = ""
                for key in sorted(grepRes.keys()):
                    merged_res += grepRes[key]
                    merged_res += "\n"
                self.view.infoString(timestamp, merged_res)

    def do_count(self, line):
        if not line:
            raise ShellException("Could not understand grep request, " +
                                 "see 'help grep'")

        mods = self.parseModifiers(line)
        line = mods['line']

        tline = line[:]
        search_strs = []
        ignore_str = ""
        unique = False
        is_and = False
        is_casesensitive=True
        start_tm = ""
        duration = ""
        sources = []
        reading_search_strings = False
        search_string_read = False
        while tline:
            search_string_read = False
            word = tline.pop(0)
            if word == '-s':
                try:
                    search_strs.append(strip_string(tline.pop(0)))
                    reading_search_strings = True
                    search_string_read = True
                except:
                    search_strs = []
            elif word == '-a':
                is_and = True
            elif word == '-u':
                unique = True
            elif word == '-i':
                is_casesensitive = False
            elif word == '-v':
                ignore_str = tline.pop(0)
                ignore_str = strip_string(ignore_str)
            elif word == '-f' and not self.grep_cluster:
                start_tm = tline.pop(0)
                start_tm = strip_string(start_tm)
            elif word == '-d' and not self.grep_cluster:
                duration = tline.pop(0)
                duration = strip_string(duration)
            elif word == '-n':
                try:
                    sources = [
                        int(i) for i in strip_string(
                            tline.pop(0)).split(",")]
                except:
                    sources = []
            elif reading_search_strings:
                try:
                    search_strs.append(strip_string(word))
                except:
                    pass
                search_string_read = True
            else:
                raise ShellException(
                    "Do not understand '%s' in '%s'" % (word, " ".join(line)))
            if not search_string_read:
                reading_search_strings = False

        if search_strs:
            files = self.logger.get_files_by_index(
                self.grep_cluster,
                sources)
            for timestamp in sorted(files.keys()):
                res = self.logger.grepCount(
                    files[timestamp],
                    search_strs, ignore_str,
                    unique, self.grep_cluster,
                    start_tm, duration,
                    is_and, is_casesensitive)
                merged_res = ""
                for key in sorted(res.keys()):
                    str = " "
                    if not self.grep_cluster:
                        str = key + " : "
                    merged_res += str + "Count of %s is : %s" % (search_strs, res[key])
                    merged_res += "\n"
                self.view.infoString(timestamp, merged_res)

    def do_diff(self, line):
        if not line:
            raise ShellException("Could not understand grep request, " +
                                 "see 'help grep'")

        mods = self.parseModifiers(line)
        line = mods['line']

        tline = line[:]
        search_str = ""
        start_tm = "head"
        duration = ""
        slice_tm = "10"
        show_count = 1
        limit = ""
        sources = []
        is_casesensitive = True
        while tline:
            word = tline.pop(0)
            if word == '-s':
                search_str = tline.pop(0)
                search_str = strip_string(search_str)
            elif word == '-f':
                start_tm = tline.pop(0)
                start_tm = strip_string(start_tm)
            elif word == '-d':
                duration = tline.pop(0)
                duration = strip_string(duration)
            elif word == '-t':
                slice_tm = tline.pop(0)
                slice_tm = strip_string(slice_tm)
            elif word == '-k':
                show_count = tline.pop(0)
                show_count = int(strip_string(show_count))
            elif word == '-i':
                is_casesensitive = False
            elif word == '-n':
                try:
                    sources = [
                        int(i) for i in strip_string(
                            tline.pop(0)).split(",")]
                except:
                    sources = []
            elif word == '-l' and tline:
                limit = tline.pop(0)
                limit = int(strip_string(limit))
            else:
                raise ShellException(
                    "Do not understand '%s' in '%s'" % (word, " ".join(line)))
        grepRes = {}
        if search_str:
            files = self.logger.get_files_by_index(
                self.grep_cluster,
                sources)
            for timestamp in sorted(files.keys()):
                grep_res = self.logger.grepDiff(
                    files[timestamp],
                    search_str,
                    self.grep_cluster,
                    start_tm,
                    duration,
                    slice_tm,
                    show_count,
                    limit, is_casesensitive)
                self.view.showGrepDiff(timestamp, grep_res)

    def do_latency(self, line):
        if not line:
            raise ShellException(
                "Could not understand latency request, " +
                "see 'help loglatency'")

        mods = self.parseModifiers(line)
        line = mods['line']

        tline = line[:]
        hist = ""
        start_tm = "head"
        duration = None
        slice_tm = "10"
        bucket_count = 3
        show_count = 3
        sources = []
        no_time_rounding = False
        while tline:
            word = tline.pop(0)
            if word == '-h':
                hist = tline.pop(0)
                hist = strip_string(hist)
            elif word == '-f':
                start_tm = tline.pop(0)
                start_tm = strip_string(start_tm)
            elif word == '-d':
                duration = tline.pop(0)
                duration = strip_string(duration)
            elif word == '-t':
                slice_tm = tline.pop(0)
                slice_tm = strip_string(slice_tm)
            elif word == '-e':
                show_count = tline.pop(0)
                show_count = int(strip_string(show_count))
            elif word == '-b':
                bucket_count = tline.pop(0)
                bucket_count = int(strip_string(bucket_count))
            elif word == '-n':
                try:
                    sources = [
                        int(i) for i in strip_string(
                            tline.pop(0)).split(",")]
                except:
                    sources = []
            elif word == '-o':
                no_time_rounding = True
            else:
                raise ShellException(
                    "Do not understand '%s' in '%s'" % (word, " ".join(line)))

        if hist:
            files = self.logger.get_files_by_index(
                self.grep_cluster,
                sources)

            for timestamp in sorted(files.keys()):
                latency_res = self.logger.loglatency(
                    files[timestamp],
                    hist,
                    slice_tm,
                    start_tm,
                    duration,
                    bucket_count,
                    show_count,
                    no_time_rounding)
                self.view.showLogLatency(timestamp, latency_res)

@CommandHelp('Displays all lines from cluster logs (collectinfos) matched with input pattern, and count those lines.')
class LogGrepClusterController(CommandController):

    def __init__(self):
        self.modifiers = set()
        self.grepFile = GrepFile(True, self.modifiers)

    def _do_default(self, line):
        self.grepFile.do_show(line)

    @CommandHelp(
        'Displays all lines from cluster logs (collectinfos) matched with input strings.',
        '  Options:',
        '    -s <string>  - Space seprated Strings to search in collectinfos, MANDATORY - NO DEFAULT',
        '                   Format -s \'string1\' \'string2\'... \'stringn\'',
        '    -a           - Set \'AND\'ing of search strings (provided with -s): Finding lines with all serach strings in it.',
        '                   Default is \'OR\'ing: Finding lines with atleast one search string in it.',
        '    -v <string>  - The non-matching string.',
        '    -n <string>  - Comma separated cluster snapshot numbers. You can get these numbers by list command. Ex. : -n \'1,2,5\'.',
        '                   If not set then runs on all cluster snapshots in selected list.',
        '    -u           - Set to find only for unique lines.',
        '    -i           - Perform case insensitive matching. By default it is case sensitive.')
    def do_show(self, line):
        self.grepFile.do_show(line)

    @CommandHelp(
        'Displays count of lines from cluster logs (collectinfos) matched with input strings.',
        '  Options:',
        '    -s <string>  - Space seprated Strings to search in collectinfos, MANDATORY - NO DEFAULT',
        '                   Format -s \'string1\' \'string2\'... \'stringn\'',
        '    -a           - Set \'AND\'ing of search strings (provided with -s): Finding lines with all serach strings in it.',
        '                   Default is \'OR\'ing: Finding lines with atleast one search string in it.',
        '    -n <string>  - Comma separated cluster snapshot numbers. You can get these numbers by list command. Ex. : -n \'1,2,5\'.',
        '                   If not set then runs on all cluster snapshots in selected list.',
        '    -v <string>  - The non-matching string.',
        '    -u           - Set to find only for unique lines.',
        '    -i           - Perform case insensitive matching. By default it is case sensitive.')
    def do_count(self, line):
        self.grepFile.do_count(line)

@CommandHelp('Checks for common inconsistencies and print if there is any')
class HealthController(CommandController):

    def __init__(self):
        self.controller_map = {
            'cluster': HealthClusterController,
            'servers': HealthServersController}
        self.modifiers = set()

    def _do_default(self, line):
        self.executeHelp(line)

@CommandHelp('Displays list of cluster collectinfos and server logs.')
class ListController(CommandController):

    def __init__(self):
        self.controller_map = {}
        self.modifiers = set()

    def _do_default(self, line):
        self.do_all(line)

    @CommandHelp('Displays list of all added cluster collectinfos and server logs')
    def do_all(self, line):
        print "*************************** CLUSTER ***************************"
        index = 1
        all_cluster_files = self.logger.get_list(cluster_snapshot=True, all_list=True)
        for timestamp in sorted(all_cluster_files.keys()):
            print str(index) + "  : " + timestamp + "\t" + all_cluster_files[timestamp]
            index += 1
        print "*************************** SERVER ***************************"
        index = 1
        all_server_files = self.logger.get_list(cluster_snapshot=False, all_list=True)
        for node in sorted(all_server_files.keys()):
            print str(index) + "  : " + node + "\t" + all_server_files[node]
            index += 1

    @CommandHelp('Displays list of cluster collectinfos and server logs selected for analysis')
    def do_selected(self, line):
        print "*************************** CLUSTER ***************************"
        index = 1
        selected_cluster_files = self.logger.get_list(cluster_snapshot=True, all_list=False)
        for timestamp in sorted(selected_cluster_files.keys()):
            print str(index) + "  : " + timestamp + "\t" + selected_cluster_files[timestamp]
            index += 1
        print "*************************** SERVER ***************************"
        index = 1
        selected_server_files = self.logger.get_list(cluster_snapshot=False, all_list=False)
        for node in sorted(selected_server_files.keys()):
            print str(index) + "  : " + node + "\t" + selected_server_files[node]
            index += 1

@CommandHelp('Select cluster snapshots (collectinfos) and server logs from all list to selected list.')
class SelectController(CommandController):

    def __init__(self):
        self.controller_map = {}
        self.modifiers = set()

    @CommandHelp(
        'Select list of cluster snapshots (collectinfos) in specific time range.',
        '  Options:',
        '    -y     - Expected year of snapshot. Formats: \'2015\', \'2011-2015\' or \'2011,2013,2015\'',
        '    -m     - Expected month of snapshot. Formats: \'10\', \'5-10\' or \'1,6,12\'',
        '    -d     - Expected date of snapshot. Formats: \'27\', \'20-25\' or \'11,13,29\'',
        '    -hh    - Expected hour value of snapshot. Formats: \'15\', \'1-8\' or \'11,22\'',
        '    -mm    - Expected minute value of snapshot. Formats: \'55\', \'30-55\' or \'1,4,45\'',
        '    -ss    - Expected second value of snapshot. Formats: \'43\', \'3-23\' or \'6,8,58\'')
    def do_time(self, line):
        tline = line[:]
        year = ""
        month = ""
        date = ""
        hr = ""
        minutes = ""
        sec = ""

        while tline:
            word = tline.pop(0)
            if word == '-y':
                year = tline.pop(0)
                year = strip_string(year)
            elif word == '-m':
                month = tline.pop(0)
                month = strip_string(month)
            elif word == '-d':
                date = tline.pop(0)
                date = strip_string(date)
            elif word == '-hh':
                hr = tline.pop(0)
                hr = strip_string(hr)
            elif word == '-mm':
                minutes = tline.pop(0)
                minutes = strip_string(minutes)
            elif word == '-ss':
                sec = tline.pop(0)
                sec = strip_string(sec)
            else:
                raise ShellException(
                    "Do not understand '%s' in '%s'" % (word, " ".join(line)))
        self.logger.select_cluster_snapshots(
            year,
            month,
            date,
            hr,
            minutes,
            sec)

    @CommandHelp(
        'Select list of cluster snapshots. We can give \'all\' as a input to add all snapshots from all list',
        'or we can give selective cluster snapshot numbers',
        'We can get cluster snapshot number from \'list\' command.',
        'Example : select cluster all   OR   select cluster 1 2 3')
    def do_cluster(self, line):
        self.logger.select_logs(line, cluster_snapshot=True)

    @CommandHelp(
        'Select list of server logs. We can give \'all\' as a input to add all server logs from all list',
        'or we can give selective server log numbers',
        'We can get server log number from \'list\' command.',
        'Example : select server all   OR   select server 1 2 3')
    def do_server(self, line):
        self.logger.select_logs(line, cluster_snapshot=False)

class HealthClusterController(CommandController):

    def __init__(self):
        self.modifiers = set()
        self.grepFile = GrepFile(True, self.modifiers)

    @CommandHelp('Displays All Cluster Level Assetions !!')
    def _do_default(self, line):
        service_stats = self.logger.infoStatistics(stanza="service")
        namespace_stats = self.logger.infoStatistics(stanza="namespace")
        asserts = {}

        NOT_OK = 0
        WARNING = 0
        CRITICAL = 0

        for timestamp in sorted(service_stats.keys()):
            asserts[timestamp] = {}
            tot_objects = 0
            tot_refs = 0
            for node, stats in service_stats[timestamp].iteritems():
                tot_objects += int(stats["objects"])
                tot_refs += int(stats["record_refs"])
            if tot_objects != tot_refs:
                asserts[timestamp]["Object Count"] = ": objects=" + \
                    str(tot_objects) + " != refs=" + str(tot_refs)
                WARNING += 1

        for timestamp in sorted(service_stats.keys()):
            print terminal.fg_blue() + "************************** Assertions for %s **************************" % (timestamp) + terminal.fg_clear()
            for node, string in asserts[timestamp].iteritems():
                print terminal.bold() + node + terminal.unbold() + terminal.fg_red() + string + terminal.fg_clear()

class HealthServersController(CommandController):

    def __init__(self):
        self.modifiers = set()
        self.grepFile = GrepFile(False, self.modifiers)

    @CommandHelp('Displays all possible results from logs')
    def _do_default(self, line):
        print "Todo"

@CommandHelp(
    'Allow users to add cluster collectinfos and server logs.',
    'After adding new log file by using this command, it will also update the selected file list.')
class AddController(CommandController):

    def __init__(self):
        self.controller_map = {
            'cluster': AddClusterController, 'server': AddServerController
        }
        self.modifiers = set()

    def _do_default(self, line):
        self.executeHelp(line)

@CommandHelp("Adds cluster logs (collectinfos).",
             "Format : add cluster \'cluster log path1\' \'cluster log path2\' \'cluster log directory path\' ...",
             "Ex. add cluster \'/temp/test/\' \'/abcd/collectinfo1.log\' \'/abcd/collecinfo2\'")
class AddClusterController(CommandController):

    def __init__(self):
        self.modifiers = set()

    def _do_default(self, line):
        for path in line:
            path = strip_string(path)
            snapshots_added, error = self.logger.add_cluster_snapshots(path)
            if snapshots_added==1:
                print "%d collectinfo added for cluster analysis."%(snapshots_added)
            elif snapshots_added>1:
                print "%d collectinfos added for cluster analysis."%(snapshots_added)

            if error:
                print "\n" + terminal.fg_red() + error + terminal.fg_clear()

@CommandHelp(
    "Adds server logs.",
    "It requires to provide display name which we want to set in list for logs.",
    "For log file of server (version >=3.7.1), "
    "asadm fetches node id from log and set it as a display name.",
    "Format : add server \'server_display_name1\' \'server log path1\' \'server_display_name2\' \'server log path2\' \'server_display_name_prefix\' \'server log directory path\' ...",
    "Ex. add server log1 \'/var/log/abcd.log\' nodes \'/var/log/xyz\'")
class AddServerController(CommandController):

    def __init__(self):
        self.modifiers = set()

    def _do_default(self, line):
        length = len(line)
        if length < 2:
            return

        for index in range(0, length, 2):
            if index == length - 1:
                break
            path = strip_string(line[index + 1])
            prefix = strip_string(line[index])
            server_logs_added, error = self.logger.add_server_logs(prefix, path)
            if server_logs_added==1:
                print "%d server log added for server analysis."%(server_logs_added)
            elif server_logs_added>1:
                print "%d server logs added for server analysis."%(server_logs_added)

            if error:
                print "\n" + terminal.fg_red() + error + terminal.fg_clear()

@CommandHelp(
    'Allow users to remove cluster and server logs.')
class RemoveController(CommandController):

    def __init__(self):
        self.controller_map = {
            'cluster': RemoveClusterController, 'server': RemoveServerController
        }
        self.modifiers = set()

    def _do_default(self, line):
        self.executeHelp(line)

@CommandHelp("Remove cluster logs (collectinfos).")
class RemoveClusterController(CommandController):

    def __init__(self):
        self.modifiers = set()

    @CommandHelp('Remove cluster logs.',
        '  Options:',
        '    -s <string>  - Comma separated selected cluster log file numbers. You can get these numbers by \'list selected\' command.',
        '                   This will remove files from selected file list',
        '                   Format : -s \'1,2,5\'',
        '    -a <string>  - Comma separated cluster log file numbers. You can get these numbers by \'list\' command.',
        '                   This will remove files from all and selected lists',
        '                   Format : -a \'1,2,5\'')
    def _do_default(self, line):
        if not line:
            raise ShellException(
                "Could not understand remove request, " +
                "see 'help remove'")
        mods = self.parseModifiers(line)
        line = mods['line']

        tline = line[:]
        selected_remove_list = []
        all_remove_list = []
        while tline:
            word = tline.pop(0)
            if word == '-a':
                try:
                    values = strip_string(tline.pop(0))
                    for i in values.split(","):
                        index = int(i)-1
                        all_remove_list.append(index)
                except:
                    pass
            elif word == '-s':
                try:
                    values = strip_string(tline.pop(0))
                    for i in values.split(","):
                        index = int(i)-1
                        selected_remove_list.append(index)
                except:
                    pass
            else:
                raise ShellException("Do not understand '%s' in '%s'" % (word, " ".join(line)))

        all_rm_list = self.logger.get_name_by_index(indices=all_remove_list, cluster_snapshot=True, from_all_list=True)
        selected_rm_list = self.logger.get_name_by_index(indices=selected_remove_list, cluster_snapshot=True, from_all_list=False)
        if all_rm_list:
            self.logger.remove_logs(all_rm_list)
        if selected_rm_list:
            self.logger.remove_logs(selected_rm_list, from_all_list=False)

@CommandHelp("Remove server logs.")
class RemoveServerController(CommandController):

    def __init__(self):
        self.modifiers = set()

    @CommandHelp('Remove server logs.',
        '  Options:',
        '    -s <string>  - Comma separated selected server log file numbers. You can get these numbers by \'list selected\' command.',
        '                   This will remove files from selected file list',
        '                   Format : -s \'1,2,5\'',
        '    -a <string>  - Comma separated server log file numbers. You can get these numbers by \'list\' command.',
        '                   This will remove files from all and selected lists',
        '                   Format : -a \'1,2,5\'')
    def _do_default(self, line):
        if not line:
            raise ShellException(
                "Could not understand remove request, " +
                "see 'help remove'")
        mods = self.parseModifiers(line)
        line = mods['line']

        tline = line[:]
        selected_remove_list = []
        all_remove_list = []
        while tline:
            word = tline.pop(0)
            if word == '-a':
                try:
                    values = strip_string(tline.pop(0))
                    for i in values.split(","):
                        index = int(i)-1
                        all_remove_list.append(index)
                except:
                    pass
            elif word == '-s':
                try:
                    values = strip_string(tline.pop(0))
                    for i in values.split(","):
                        index = int(i)-1
                        selected_remove_list.append(index)
                except:
                    pass
            else:
                raise ShellException("Do not understand '%s' in '%s'" % (word, " ".join(line)))
        all_rm_list = self.logger.get_name_by_index(indices=all_remove_list, cluster_snapshot=False, from_all_list=True)
        selected_rm_list = self.logger.get_name_by_index(indices=selected_remove_list, cluster_snapshot=False, from_all_list=False)
        if all_rm_list:
            self.logger.remove_logs(all_rm_list, cluster_snapshot=False, from_all_list=True)
        if selected_rm_list:
            self.logger.remove_logs(selected_rm_list, cluster_snapshot=False, from_all_list=False)

@CommandHelp("Set pager for output")
class PagerController(CommandController):
    def __init__(self):
        self.modifiers = set()

    def _do_default(self, line):
        self.executeHelp(line)

    @CommandHelp("Displays output with vertical and horizontal paging for each output table same as linux 'less' command.",
                 "We can use arrow keys to scroll output and 'q' to end page for table.",
                 "All linux less commands can work in this pager option.")
    def do_less(self, line):
        CliView.pager = CliView.LESS

    @CommandHelp("Removes pager and prints output normally")
    def do_remove(self, line):
        CliView.pager = CliView.NO_PAGER

    @CommandHelp("Displays current selected pager option.")
    def do_show(self, line):
        CliView.print_pager()
