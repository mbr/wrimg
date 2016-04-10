import os
from stat import S_IFBLK

from .size import ByteSize


class Device(object):
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
        return open(
            os.path.join(self.sys_fs_path, name), 'rb').read().rstrip(b'\n')

    def _lookup_sys_bool(self, name):
        return int(self._lookup_sys(name)) == 1

    @property
    def removable(self):
        return self._lookup_sys_bool('removable')

    @property
    def size(self):
        return ByteSize(int(self._lookup_sys('size')) * 512)

    @property
    def model(self):
        return self._lookup_sys('device/model').decode('utf8').strip()

    @property
    def read_only(self):
        return self._lookup_sys_bool('ro')

    def open(self, mode='r'):
        return open(self.path, mode)

    def __repr__(self):
        return '{0.__class__.__name__}({0.path})'.format(self)

    @classmethod
    def iter_block_devices(cls, base_path='/dev'):
        for name in os.listdir(base_path):
            if name.startswith('sd') and len(name) == 3:
                yield cls(os.path.join(base_path, name))
