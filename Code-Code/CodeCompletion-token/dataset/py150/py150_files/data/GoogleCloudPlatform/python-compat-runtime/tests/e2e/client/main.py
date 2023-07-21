import argparse
import sys

import requests


def main(url):
    requests.get(url + 'refresh')
    response = requests.get(url + 'test')

    print(response.text)

    if response.status_code != 200:
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()

    main(args.url)
