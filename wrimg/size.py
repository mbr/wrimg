# FIXME: replace with datasize package (from PyPI)

import re
import sys

if sys.version_info.major < 3:
    long_int = long
    text_types = (str, unicode)
else:
    long_int = int
    text_types = str

UNITS_1000 = ['kilobyte', 'megabyte', 'gigabyte', 'terabyte', 'petabyte',
              'exabyte', 'zetabyte', 'yottabyte']
UNITS_1024 = ['kibibyte', 'mebibyte', 'gibibyte', 'tebibyte', 'pebibyte',
              'exbibyte', 'zebibyte', 'yobibyte']
U_1000 = ['k', 'm', 'g', 't', 'p', 'e', 'z', 'y']
U_1024 = ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']

_PARSE = [
    (UNITS_1000, 1000),
    (UNITS_1024, 1024),
    (U_1000, 1000),
    (U_1024, 1024),
]

FMT_RE = re.compile(r'(.*?)( )?(hh|HH|h|H)$')
VAL_RE = re.compile(r'(\d+(?:\.\d+))(?: )?(.*)')


class ByteSize(long_int):
    @staticmethod
    def __new__(cls, val):
        if isinstance(val, text_types):
            val = str(val)

            for units, base in _PARSE:
                for idx, suffix in enumerate(units):
                    if val.endswith(suffix):
                        val = val[:-len(suffix)]
                        num = long(val) * base**(idx + 1)
                        return long.__new__(cls, num)
            return long_int(val)
        else:
            # if no string, just pass through
            return long_int.__new__(cls, val)

    def __format__(self, fmt):
        base = None

        m = FMT_RE.match(fmt)
        space = ''

        if m:
            fmt, space, bf = m.groups()
            if bf == 'hh':
                base = 1000
                units = UNITS_1000
            elif bf == 'HH':
                base = 1024
                units = UNITS_1024
            elif bf == 'h':
                base = 1000
                units = U_1000
            elif bf == 'H':
                base = 1024
                units = U_1024

        val = self
        suffix = ''

        if base:
            for idx, name in enumerate(units):
                if abs(val) < base:
                    break

                val /= float(base)
                suffix = units[idx]

        return float(val).__format__(fmt) + (space or '') + suffix
