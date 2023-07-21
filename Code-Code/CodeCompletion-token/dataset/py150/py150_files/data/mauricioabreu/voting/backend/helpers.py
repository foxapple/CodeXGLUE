from ConfigParser import SafeConfigParser


def parse_config(filename):
    with open(filename) as f:
        parser = SafeConfigParser()
        parser.readfp(f)

    return parser
