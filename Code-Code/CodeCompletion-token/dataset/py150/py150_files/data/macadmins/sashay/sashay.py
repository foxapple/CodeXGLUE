#!/usr/bin/python
"""Parses Server.app's Caching Servers Debug Log, Sends Reports
   See README and LICENSE for more information. Originally created
   by Erik Gomez, pythonified by Allister Banks, 2015"""


import bz2
import collections
import datetime
import glob
import optparse
import os
import re
import subprocess
import sys
import tempfile
from CoreFoundation import CFPreferencesCopyAppValue


def sanities():
    """preflight checks to ensure compat., skipped if run in dev mode"""
    pref_path = '/Library/Server/Caching/Config/Config.plist'
    try:
        logidentitypref = CFPreferencesCopyAppValue('LogClientIdentity', pref_path)
        if not logidentitypref == 'true':
            print """This will be a very spare/boring report if you don't run this command:
                  sudo serveradmin settings caching:LogClientIdentity = 1"""
    except Exception as e:
        raise e
    if os.geteuid() != 0:
        exit("For the final message send(only), this(currently) needs to be run with 'sudo'.")


def server_appvers():
    """Checks for/gets server.app version, since we're forking between 4 and 5"""
    plist_path = '/Applications/Server.app/Contents/Info.plist'
    server_app_version = CFPreferencesCopyAppValue('CFBundleShortVersionString', plist_path)
    if not server_app_version:
        print "Can't find Server.app, are you running this on your Mac server instance?"
        sys.exit(2)
    elif server_app_version < 4.1:
        print "Not Version 4.1(+) of Server.app"
        sys.exit(3)
    elif server_app_version < '5.0':
        return 'Four'
    else:
        return 'Five'

# utility methods
def normalize_gbs(mb_or_gb, val_to_operate_on):
    """Used when calculating bandwidth. Takes an index to check, and if MB,
       returns the applicable index divided by 1024 to normalize on GBs"""
    if mb_or_gb == 'MB':
        return float(float(val_to_operate_on) / 1024.0)
    elif mb_or_gb != 'GB':
        return 0.0 # if it's less than 1MB just shove in a placeholder float
    else:
        return float(val_to_operate_on)


def alice(list_to_get_extremes):
    """One pill makes you taller... calculates bandwidth used delta"""
    return max(list_to_get_extremes) - min(list_to_get_extremes)


def gen_mb_or_gb(floaty):
    """Shows bandwidth in MBs if less than 1GB. Returns string"""
    if floaty > 1.0:
        return " ".join([str(round(floaty, 2)), 'GBs'])
    else:
        megabyted_float = floaty * 1024
        return " ".join([str(round(megabyted_float, 2)), 'MBs'])

#start taking vars from main()
def get_start(from_datetime):
    """Calc start of reporting period datetime, returns as string"""
    delta_object = datetime.timedelta(days=int(from_datetime))
    start_datetime = str(datetime.datetime.today() - delta_object)[:-3] # lops off UTC's millisecs
    return start_datetime


def join_bzipped_logs(dir_of_logs):
    """Creates tempfile, wildcard searches for all archive logs, then uses bz2 module
       to unpack and append them all to the tempfile. Returns file(list of strings) once populated"""
    #setup tempfile
    unbzipped_logs = tempfile.mkstemp(suffix='.log', prefix='sashayTemp-')[1]
    das_bzips = "".join([dir_of_logs, '/Debug-*'])
    bunch_of_bzips = glob.glob(das_bzips)
    opened_masterlog = open(unbzipped_logs, 'w')
    #concat each unbz'd log to tempfile
    for archived_log in bunch_of_bzips:
        try:
            process_bz = bz2.BZ2File(archived_log)
            opened_masterlog.write(process_bz.read())
        except Exception as e:
            raise e
        finally:
            process_bz.close()
    opened_masterlog.close()
    return unbzipped_logs


def separate_range_build_list(dir_of_logs, unbzipped_logs, start_datetime, to_datetime, server_vers):
    # todo - this is a bit big and nasty, but good enough for now
    """Opens current debug.log and un-bz'd logs and builds new list of loglines
       that fall within our reporting period. Returns two lists of strings: one for bandwidth,
       other for eventual parsing of filetypes served, device os/model, and ips devices accessed from."""
    our_range_logline_str_list, bandwidth_lines_list, filetype_lines_list, service_restart_timestamps = [], [], [], []
    try:
        with open(os.path.join(dir_of_logs, 'Debug.log'), 'rU') as current, open(unbzipped_logs, 'rU') as unzipped:
            for f in current, unzipped:
                for line in f:
                    if line[:23] > start_datetime:
                        if line[:23] < to_datetime:
                            our_range_logline_str_list.append(line)
    except IOError as e:
        print 'Operation failed: %s' % e.strerror
        sys.exit(4)
    # currently just resetting start_time if service was restarted to most current occurance
    # and informing with datetime in report (with the proper format to add --through option)
    more_recent_svc_hup = False
    for logline_str in our_range_logline_str_list:
        if 'Registration succeeded.  Resuming server.' in logline_str:
            service_restart_timestamps.append(logline_str[:23])
            more_recent_svc_hup = True
            new_start_datetime = max(service_restart_timestamps)
    # todo - should probably be less repetition below
    excludes = ['egist', 'public', 'peers', 'Opened', 'EC', 'Bad']
    filetypes = ['ipa', 'epub', 'pkg', 'zip']
    if more_recent_svc_hup:
        for logline_str in our_range_logline_str_list:
            if logline_str[:23] > new_start_datetime:
                if server_vers == 'Five':
                    if 'Served all' in logline_str:
                        bandwidth_lines_list.append(logline_str.split())
                    elif not any(x in logline_str for x in excludes):
                        if any(x in logline_str for x in filetypes):
                            filetype_lines_list.append(logline_str.split())
                else:
                    if 'start:' in logline_str:
                        bandwidth_lines_list.append(logline_str.split())
                    elif not any(x in logline_str for x in excludes):
                        if any(x in logline_str for x in filetypes):
                            filetype_lines_list.append(logline_str.split())
    else:
        new_start_datetime = start_datetime
        for logline_str in our_range_logline_str_list:
            if logline_str[:23] > start_datetime:
                if server_vers == 'Five':
                    if 'Served all' in logline_str:
                        bandwidth_lines_list.append(logline_str.split())
                    elif not any(x in logline_str for x in excludes):
                        if any(x in logline_str for x in filetypes):
                            filetype_lines_list.append(logline_str.split())
                else:
                    if 'start:' in logline_str:
                        bandwidth_lines_list.append(logline_str.split())
                    elif not any(x in logline_str for x in excludes):
                        if any(x in logline_str for x in filetypes):
                            filetype_lines_list.append(logline_str.split())
    return bandwidth_lines_list, filetype_lines_list, more_recent_svc_hup, new_start_datetime


def parse_bandwidth(bandwidth_lines_list, server_vers):
    """On Server4, uses indexed fields in log lines to build list of bandwidth
       transferred, normalizes in GBs, then parses deltas for data served from
       cache or streamed from apple/peers. On 5, builds up totals. Returns strings"""
    if server_vers == 'Five':
        #2015-09-22 10:23:03.737 #o13uUhWMyXek Served all 3.2 MB of 3.2 MB; 0 bytes from cache, 3.2 MB stored from Internet, 0 bytes from peers
        daily_total_from_cache, daily_total_from_apple, peer_amount = 0.0, 0.0, 0.0
        for each in bandwidth_lines_list:
            if each[14] != '0':
                if each[15] != 'GB':
                    this_loops_fromapple = float(each[14]) / 1024
                elif each[15] == 'GB':
                    this_loops_fromapple = float(each[14])
                daily_total_from_apple += this_loops_fromapple
            elif each[19] != '0':
                if each[20] != 'GB':
                    peer_amount += float(each[19]) / 1024
            elif each[10] != '0':
                if each[11] != 'GB':
                    daily_total_from_cache += float(each[10]) / 1024
                elif each[11] == 'GB':
                    daily_total_from_cache += float(each[10])
        if peer_amount == 0.0:
            peer_amount = 'no peer servers detected'
        else:
            peer_amount = 'along with %s from peers' % gen_mb_or_gb(peer_amount)
    else:
        logged_bytes_from_cache, logged_bytes_from_apple, logged_bytes_from_peers = [], [], []
        for each in bandwidth_lines_list:
            strip_parens = (each[15])[1:] # silly log line cleanup
            logged_bytes_from_cache.append(normalize_gbs(each[6], each[5]))
            logged_bytes_from_apple.append(normalize_gbs(each[16], strip_parens))
            if not each[19] == '0':
                logged_bytes_from_peers.append(normalize_gbs(each[20], each[19]))
        daily_total_from_cache = alice(logged_bytes_from_cache)
        daily_total_from_apple = alice(logged_bytes_from_apple)
        # check for peers, set default
        peer_amount = 'no peer servers detected'
        if len(logged_bytes_from_peers) > 1:
            if max(logged_bytes_from_peers) > 0.1:
                daily_total_from_peers = alice(logged_bytes_from_peers)
                daily_total_from_apple = daily_total_from_apple - daily_total_from_peers
                peer_amount = 'along with %s from peers' % gen_mb_or_gb(daily_total_from_peers)
    return daily_total_from_cache, daily_total_from_apple, peer_amount


def get_device_stats(filetype_lines_list, server_vers):
    """Parses out device stats, returns list motherlode"""
# Example data as of July 2, 2015
# ['2015-06-30', '12:31:04.095', '#eLTtl5KfMlrA', 'Request', 'from', '172.20.202.245:61917', '[itunesstored/1.0', 'iOS/8.3', 'model/iPhone7,1', 'build/12F70', '(6;', 'dt:107)]', 'for', 'http://a1254.phobos.apple.com/us/r1000/038/Purple7/v4/23/23/5e/23235e5d-1a12-f381-c001-60acfe6a56ff/zrh1611131113630130772.D2.pd.ipa']
# ['2015-06-30', '12:32:19.554', '#6d3LgXpVcHAU', 'Request', 'from', '172.18.20.102:52880', '[Software%20Update', '(unknown', 'version)', 'CFNetwork/720.3.13', 'Darwin/14.3.0', '(x86_64)]', 'for', 'http://swcdn.apple.com/content/downloads/58/34/031-25780/u1bqpe4ggzdp86utj2esnxfj4xq5izwwri/FirmwareUpdate.pkg']
# ['2015-06-30', '14:09:00.230', '#sNn+egdFxN7m', 'Request', 'from', '172.18.81.204:60025', '[Software%20Update', '(unknown', 'version)', 'CFNetwork/596.6.3', 'Darwin/12.5.0', '(x86_64)', '(MacBookAir6%2C2)]', 'for', 'http://swcdn.apple.com/content/downloads/15/59/031-21808/qylh17vrdgnipjibo2avj3nbw8y2pzeito/Safari6.2.7MountainLion.pkg']
    iplog, oslog, modellog, ipas, epubs, pkgs, zips = [], [], [], [], [], [], []
    for filelog in filetype_lines_list:
        if server_vers == 'Five':
            filelog = filelog[2:]
        if filelog[5].startswith('172') or filelog[5].startswith('192') or filelog[5].startswith('10.'):
            strip_port = (filelog[5])[:-6]
            iplog.append(strip_port)
            if not filelog[10].startswith('Darwin'):
                if filelog[7] == '(unknown':
                    modellog.append('Unknown Mac')
                else:
                    oslog.append(filelog[7])#Whereas iOS just logs without a fuss
            else:
                osver_dict = {'12':'Mac OS 10.8.x', '13':'Mac OS 10.9.x', '14':'Mac OS 10.10.x', '15':'Mac OS 10.11.x'}
                os_ver = (filelog[10])[7:9] #User agent-based Mac OS detection
                oslog.append(osver_dict.get(os_ver))
            if len(filelog) == 15:# For some reason you only seem to get Mac models when logline has 15 sections
                if filelog[12].startswith('dt:'):
                    modellog.append((filelog[8])[6:])
                else:
                    modellog.append(filelog[12])
            else:
                modellog.append((filelog[8])[6:])#...whereas iOS just logs without a fuss(noticing a pattern?)
            if (filelog[-1]).endswith('ipa'):
                ipas.append(filelog[-1])
            elif (filelog[-1]).endswith('epub'):
                epubs.append(filelog[-1])
            elif (filelog[-1]).endswith('pkg'):
                pkgs.append(filelog[-1])
            elif (filelog[-1]).endswith('zip'):
                zips.append(filelog[-1])
    return iplog, oslog, modellog, ipas, epubs, pkgs, zips


def parse_prods(prodlist, name):
    """Returns a string with prod reporting format, or empty string if no products found"""
    if len(prodlist) > 0:
        sum_of_prods = len(prodlist)
        individ_prods = len(set(prodlist))
        return '%d different %s were requested %d times, \n' % (individ_prods, name, sum_of_prods)
    else:
        return ''


def report_rounder(key_total):
    """takes the total number of 'keyed' items and returns an int to round displayed results to"""
    if key_total > 10:
        if key_total < 15:
            return 10
        elif key_total < 20:
            return 15
        elif key_total < 25:
            return 20
        elif key_total >= 25:
            return 25
    else:
        return key_total


def main():
    p = optparse.OptionParser()
    p.set_usage("""Usage: %prog [options]""")
    p.add_option('--from', '-f', dest='from_datetime', default=1,
                 help="""(Integer) Number of days in the past to include in report.
                         Default is 24hrs from current timestamp""")
    p.add_option('--through', '-t', dest='to_datetime', default=str(datetime.datetime.today())[:-3],
                 help="""End of date range to report, in format '2015-06-30 12:00:00.000'""")
    p.add_option('--net', '-n', dest='network_ips', default=True,
                 help="""Report on total/unique ips and subnets.""")
    p.add_option('--modelvers', '-m', dest='modelvers', default=True,
                 help="""Report on iOS device versions and Macs (if logged).""")
    p.add_option('--osrevs', '-r', dest='os_revisions', default=True,
                 help="""Report on iOS and Macs OS versions.""")
    p.add_option('--ipa', '-i', dest='ipas', default=True,
                 help="""Report on total/unique ipas.""")
    p.add_option('--epub', '-e', dest='epubs', default=True,
                 help="""Report on total/unique epubs.""")
    p.add_option('--pkg', '-p', dest='pkgs', default=True,
                 help="""Report on total/unique pkgs.""")
    p.add_option('--zip', '-z', dest='zips', default=True,
                 help="""Report on total/unique zips (assuming for iOS firmware).""")
    p.add_option('--subject', '-s', dest='subject_prefix', default='Daily',
                 help="""Adds prefix to message, e.g. for denoting arbitrary date ranges, 'daily/weekly/monthly'.""")
    p.add_option('--dev', '-d', dest='devmode', default=False,
                 help="""Skips sanity checks for dev work, remember to override dir_of_logs""")
    p.add_option('--logs', '-l', dest='logdir', default='/Library/Server/Caching/Logs',
                 help="""Dir of caching server debug logs, default = /Library/Server/Caching/Logs""")

    options, arguments = p.parse_args()
    # get to work
    if not options.devmode:
        sanities()
        server_vers = server_appvers()
    else:# setting server version to Five in devmode to intentionally test forked code path
        server_vers = 'Five'
    dir_of_logs = options.logdir
    start_datetime = get_start(options.from_datetime)
    unbzipped_logs = join_bzipped_logs(dir_of_logs)
    (bandwidth_lines_list, filetype_lines_list, more_recent_svc_hup, new_start_datetime) = separate_range_build_list(dir_of_logs, unbzipped_logs, start_datetime, options.to_datetime, server_vers)
    if options.devmode:
        print '-' * 14, 'DEBUG', '-' * 14, '\nAll Args:', sys.argv[1:]
        print 'New(?) start_datetime:', new_start_datetime, '\n'
    (daily_total_from_cache, daily_total_from_apple, peer_amount) = parse_bandwidth(bandwidth_lines_list, server_vers)
    (iplog, oslog, modellog, ipas, epubs, pkgs, zips) = get_device_stats(filetype_lines_list, server_vers)

    #build message
    message = ["Download requests served from cache:", gen_mb_or_gb(daily_total_from_cache), '\n',
               "Amount streamed from Apple (" + str(peer_amount) + "):", gen_mb_or_gb(daily_total_from_apple), '\n',
               "(Potential) Net bandwidth saved:",
               gen_mb_or_gb(daily_total_from_cache - daily_total_from_apple), '\n', ""]
    if more_recent_svc_hup:
        disclaimer1 = ['\n', "  * NOTE: Stats are only displayed from the last caching service restart,", new_start_datetime, '\n']
        message += disclaimer1
    if options.modelvers:
        sum_of_models = len(modellog)
        individs = len(set(modellog))
        key_total1 = report_rounder(individs)
        counter = collections.Counter(modellog)
        model_tally = ['\n', 'The', str(key_total1), 'most frequently seen types of devices (of', str(individs), 'unique devices in total, followed by their count) were:', '\n\t', str(counter.most_common(key_total1)),
                       '\n', 'The server was accessed by those devices', str(sum_of_models), 'times,']
        if 'Unknown Mac' in modellog:
            model_tally.append('(Unique devices above do not include some unspecified Macs)')
        message += model_tally
    if options.network_ips:
        subnet_list = []
        for addy in iplog:
            just_sub = re.search('(\d{1,3}\.){2}\d{1,3}', addy)
            subnet_list.append(just_sub.group())
        individ_subs = len(set(subnet_list))
        key_total2 = report_rounder(individ_subs)
        counter = collections.Counter(subnet_list)
        ip_tally = ['\n', "IP ranges that devices most frequently accessed this server from were:", '\n\t', str(counter.most_common(key_total2)), '\n']
        message += ip_tally
    if options.os_revisions:
        individ_osen = len(set(oslog))
        key_total3 = report_rounder(individ_osen)
        counter = collections.Counter(oslog)
        os_tally = ['\n', 'Of the', str(individ_osen), 'different OS versions seen across all devices, the', str(key_total3), 'most frequent were:', '\n\t', str(counter.most_common(key_total3)), '\n\n']
        message += os_tally
    final_filetypes = []
    if options.ipas:
        final_filetypes.append(parse_prods(ipas, 'iPhone Applications'))
    if options.epubs:
        final_filetypes.append(parse_prods(epubs, 'iBooks'))
    if options.pkgs:
        final_filetypes.append(parse_prods(pkgs, 'Mac Applications and/or Updates'))
    if options.zips:
        final_filetypes.append(parse_prods(zips, 'iOS Updates (and other zip archives)'))
    message += final_filetypes

    if options.subject_prefix:
        message.insert(0, options.subject_prefix)

    print ' '.join(message)                                                        #debug
    final_msg_list = ['/Applications/Server.app/Contents/ServerRoot/usr/sbin/server postAlert CustomAlert Common subject "', options.subject_prefix, 'Caching Server Data:', new_start_datetime[:-4], 'through', options.to_datetime[:-4] + '"', 'message', '"' + ' '.join(message) + '"', '<<<""']
    final_message = ' '.join(final_msg_list)
    if not options.devmode:
        subprocess.call(final_message, shell=True)

if __name__ == '__main__':
    main()
