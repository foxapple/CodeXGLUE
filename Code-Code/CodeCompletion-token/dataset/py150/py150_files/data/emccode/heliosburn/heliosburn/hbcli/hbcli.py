import os
import sys
import json
from controllers import config
from controllers import recording 
from controllers import qos
from controllers import session
from controllers import serveroverload
from controllers import user
from controllers import proxy
from controllers import testplan
from controllers import testplan_rule


def readrc():
    """Attemps to acquire a config from $HOME/.hbclirc
    Failures to parse a valid JSON will cause sys.exit(1)
    """
    path = os.environ['HOME'] + "/.hbclirc"
    if os.path.isfile(path) is False:
        print("Config file %s is not present, please create one with `config` first." % (path))
        sys.exit(1)
    f = open(path, 'r')
    config = f.read()
    f.close()
    try:
        config = json.loads(config)
        assert "user" in config
        assert "pass" in config
        assert "url" in config
        return config
    except (ValueError, AssertionError) as e:
        print("Unable to parse %s, is your config saved? Error: %s" % (path, e))
        sys.exit(1)


def main():
    help = """
    usage: %s <command> [-h] [command-specific-arguments] [-h]

    Commands:
        config         - adjust hbcli configuration
        proxy          - interact with proxy 
        qos            - interact with qos profiles
        user           - interact with users
        recording      - interact with recordings 
        session        - interact with sessions
        serveroverload - interact with serveroverload profiles
        testplan       - interact with testplans
        testplanrule   - interact with rules within a testplan

    """ % sys.argv[0]
    if len(sys.argv) < 2:
        print(help)
        sys.exit(0)


    f_map = {
        "config": config.main,
        "proxy": proxy.main,
        "qos": qos.main,
        "recording": recording.main,
        "session": session.main,
        "serveroverload": serveroverload.main,
        "testplan": testplan.main,
        "testplanrule": testplan_rule.main,
        "user": user.main,
    }

    if sys.argv[1] != "config":
        rc = readrc()
    else:
        rc = None

    if sys.argv[1] in f_map:
        f_map[sys.argv[1]](rc, sys.argv)
    else:
        print(help)
        sys.exit(0)
    return 0

if __name__ == "__main__":
    main()
