import dateutil.parser
import dateutil.tz
import json
import datetime
import bisect
import time

import utils

class Revision:
    def __init__(self, timestamp, size, comment):
        self.timestamp = timestamp
        self.size = size
        self.comment = comment

    def __repr__(self):
        return f'Rev @ {self.timestamp} of size {self.size}'

    @classmethod
    def from_json(cls, d):
        dt = dateutil.parser.isoparse(d['timestamp'])
        # Sometimes the 'comment' field is replaced by 'commenthidden' (with
        # an empty value), I guess when revs have been suppressed.
        comment = d.get('comment', '')
        return cls(dt, d['size'], comment)

class History:

    def __init__(self, title, revs):
        self.title = title
        self.revs = revs
        # Should probably already be sorted, but just to be safe.
        self.revs.sort(key=lambda r: r.timestamp)
        self._timestamps = [r.timestamp for r in self.revs]

    @classmethod
    def load_title(cls, title):
        path = utils.path_for_title(title)
        with open(path) as f:
            rev_dicts = json.load(f)
        revs = [Revision.from_json(d) for d in rev_dicts]
        return cls(title, revs)


    def revs_in_range(self, start, end):
        # index of the first rev after start
        a = bisect.bisect_left(self._timestamps, start)
        #assert a > 0
        b = bisect.bisect_left(self._timestamps, end, lo=a)
        return self.revs[max(0, a-1):b]

    def avg_size_in_range(self, start, end):
        # TODO: deal with case where revs don't overlap with start or end
        # i.e. first and last month
        #import pdb; pdb.set_trace()
        revs = self.revs_in_range(start, end)
        actual_start = max(start, revs[0].timestamp)
        total_width = (end - actual_start).total_seconds()
        normed = 0
        for i, rev in enumerate(revs):
            a = max(start, rev.timestamp)
            if i+1 < len(revs):
                b = revs[i+1].timestamp
            else:
                b = end
            width = (b-a).total_seconds() / total_width
            normed += width * rev.size
        return normed

    def size_per_month(self):
        """
        Return a dict mapping datetime (representing the first of each month) to avg size for that month.

        For each month in history range...
            Locate range of revisions that include this month
            sum up size * time fraction for each revision
            time fraction is the distance between...
                the later of (start of month, start of rev)
                the earlier of (end of month, start of next rev)
            divided by the total duration of the month
        """
        a = self.revs[0].timestamp
        b = self.revs[-1].timestamp
        year = a.year
        month = a.month
        sizes = {}
        while datetime.datetime(year=year, month=month, day=1, tzinfo=dateutil.tz.tzutc()) < b:
            start = datetime.datetime(year, month, 1, tzinfo=dateutil.tz.tzutc())
            if month == 12:
                y2 = year+1
                m2 = 1
            else:
                y2 = year
                m2 = month+1
            end = datetime.datetime(y2, m2, 1, tzinfo=dateutil.tz.tzutc())
            size = self.avg_size_in_range(start, end)
            sizes[start] = size
            year = y2
            month = m2
        return sizes

def dump_sizes(title, sizes):
    dest = utils.ts_path_for_title(title)
    with open(dest, 'w') as f:
        for date, size in sizes.items():
            datestr = f'{date.year}-{date.month}'
            line = f'{datestr},{round(size)}\n'
            f.write(line)

if __name__ == '__main__':
    t0 = time.time()
    groans = utils.load_groan_tuples()
    for groan in groans:
        for title in groan:
            h = History.load_title(title)
            sizes = h.size_per_month()
            dump_sizes(title, sizes)
    t1 = time.time()
    print(f"Finished in {t1-t0:.1f} seconds")
