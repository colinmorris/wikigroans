import requests
import time
import json
import os

import utils
from utils import debug

SLEEPTIME = 1
API_PREFIX = 'https://en.wikipedia.org/w/api.php'


def query_mw(**kwargs):
    params = kwargs.copy()
    params.setdefault('format', 'json')
    querystring = '&'.join([ f'{key}={val}' for (key, val) in params.items() ])
    url = API_PREFIX + '?' + querystring
    debug(url)
    res = requests.get(url)
    j = res.json()
    time.sleep(SLEEPTIME)
    return j

def get_revisions(title):
    rvprops = ['size', 'timestamp', 'comment']
    params = dict(
            action='query',
            prop='revisions',
            rvprop='|'.join(rvprops),
            titles=utils.munge_title(title),
            rvlimit=500,
    )
    res = None
    revs = []
    while res is None or 'continue' in res:
        if res and 'continue' in res:
            params['rvcontinue'] = res['continue']['rvcontinue']
        res = query_mw(**params)
        pages = res['query']['pages']
        assert len(pages) == 1
        v = list(pages.values())[0]
        revs.extend(v['revisions'])

    return revs

def fetch_revisions_for_title(title, force=False):
    dest = utils.path_for_title(title)
    if not force and os.path.exists(dest):
        debug(f'SKIPPING fetch for extant title: {title}')
        return
    debug(title)
    revs = get_revisions(title)
    with open(dest, 'w') as f:
        json.dump(revs, f, indent=2)

def fetch_from_csv():
    for titles in utils.load_groan_tuples():
        for title in titles:
            fetch_revisions_for_title(title)

if __name__ == '__main__':
    fetch_from_csv()
