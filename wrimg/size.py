import re

UNITS_1000 = ['kilobyte', 'megabyte', 'gigabyte', 'terabyte', 'petabyte',
              'exabyte', 'zetabyte', 'yottabyte']
UNITS_1024 = ['kibibyte', 'mebibyte', 'gibibyte', 'tebibyte', 'pebibyte',
              'exbibyte', 'zebibyte', 'yobibyte']
U_1000 = ['k', 'm', 'g', 't', 'p', 'e', 'z', 'y']
U_1024 = ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']

FMT_RE = re.compile(r'(.*?)( )?(hh|HH|h|H)$')


class ByteSize(float):
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
