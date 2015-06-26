import os
import re
from stat import S_IFBLK


class Device(object):
    BLOCK_DEVICE_RE = re.compile('^/dev/sd.$')

    def __init__(self, path):
        # strip all symbolic links and make path absolute (for /proc/mounts)
        self.path = os.path.abspath(os.path.realpath(path))
        self.st = os.lstat(self.path)

    @property
    def is_device(self):
        return bool(self.st.st_mode & S_IFBLK)

    @property
    def major(self):
        return os.major(self.st.st_rdev)

    @property
    def minor(self):
        return os.minor(self.st.st_rdev)

    @property
    def sys_fs_path(self):
        return os.path.join('/sys/dev/block', '{0.major}:{0.minor}'
                            .format(self))

    def _lookup_sys(self, name):
        return open(os.path.join(self.sys_fs_path, name), 'rb').read()

    def _lookup_sys_bool(self, name):
        return int(self._lookup_sys(name)) == 1

    @property
    def is_removable(self):
        return self._lookup_sys_bool('removable')

    @property
    def size(self):
        return int(self._lookup_sys('size'))

    @property
    def read_only(self):
        return self._lookup_sys_bool('ro')

    @classmethod
    def iter_block_devices(cls):
        for name in os.listdir('/dev'):
            if cls.BLOCK_DEVICE_RE.match(name):
                yield cls(name)
