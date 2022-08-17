import sys
import os

def debug(msg):
    sys.stderr.write(msg + '\n')

def munge_title(title):
    return title.replace(' ', '_')

def unmunge_title(title):
    return title.replace('_', ' ')

REVISIONS_DIR = 'revisions'
def path_for_title(title):
    fname = munge_title(title) + '.json'
    dest = os.path.join(REVISIONS_DIR, fname)
    return dest

SIZE_DIR = 'time_series'
def ts_path_for_title(title):
    fname = munge_title(title) + '.csv'
    dest = os.path.join(SIZE_DIR, fname)
    return dest

def load_groan_tuples():
    with open('groans.csv') as f:
        tups = []
        for line in f:
            if line.startswith('#'):
                continue
            tups.append( line.strip().split(',') )
    return tups
