import atexit
from functools import partial
import os
from stat import S_IFREG
import subprocess
import sys
import time

import click

from .devices import Device
from .size import ByteSize

# this will possibly have to be adjusted in the future with huge usb-sticks
G = 1024**3


def candidate_for_writing(dev, max_size):
    if not dev.is_device:
        return False, 'not a device'

    if not dev.major == 8:
        return False, 'major device number is not 8 (SCSI)'

    if dev.read_only:
        return False, 'device is read-only'

    if not dev.removable:
        return False, 'device is not a removable device'

    if dev.size == 0:
        return False, 'device has 0 size'

    if max_size is not None and dev.size > max_size:
        return False, 'device has a size larger than {} bytes'.format(max_size)

    return True, None


def dev_info(dev):
    return '{0.path} ({0.size:.1fH}): {0.model}'.format(dev)


class Reader(object):
    # FIXME: replace with reader that encompasses complete pipe and can
    #        count bytes in as well as bytes out, for more accurate
    #        progressbars
    BUFFER_SIZE_MIN = 1024  # 1 KB
    BUFFER_SIZE_MAX = 16 * 1024 * 1024  # 16 M
    BUFFER_SIZE_DEFAULT = 512 * 1024  # 512 KB

    def __init__(self, src, buffer_size, limit=None):
        self.src = src
        self.bytes_read = 0
        self.buffer_size = buffer_size or self.BUFFER_SIZE_DEFAULT
        assert self.BUFFER_SIZE_MIN <= self.buffer_size <= self.BUFFER_SIZE_MAX
        self.limit = limit

    def increase_buffer(self):
        self.buffer_size = min(self.buffer_size * 2, self.BUFFER_SIZE_MAX)

    def decrease_buffer(self):
        self.buffer_size = max(self.buffer_size // 2, self.BUFFER_SIZE_MIN)

    def __iter__(self):
        return self

    def __next__(self):
        if self.limit is not None:
            read_size = min(self.buffer_size, self.limit - self.bytes_read)
        else:
            read_size = self.buffer_size

        if read_size <= 0:
            raise StopIteration

        buf = self.src.read(read_size)

        if not buf:
            raise StopIteration

        self.bytes_read += len(buf)

        return buf

    next = __next__


@click.command()
@click.argument('image-file',
                type=click.Path(readable=True,
                                dir_okay=False,
                                exists=True))
@click.option('--chunk-size',
              '-C',
              type=ByteSize,
              default=None,
              help='Read-buffer size (default: auto-adjust)')
@click.option('-d',
              '--decompress',
              default='auto',
              type=click.Choice(['auto', 'none', 'xz']),
              help='On-the-fly decompression (default: auto-detect)')
@click.option('-e/-E',
              '--eject/--no-eject',
              default=True,
              help='Eject medium after writing (default: True).')
@click.option('--limit',
              '-l',
              type=ByteSize,
              help='Write no more than this many bytes to device.')
@click.option(
    '--max-size',
    default=None,
    help='Maximum size in bytes before rejecting to write to device.')
@click.option('--target',
              '-t',
              type=click.Path(dir_okay=False,
                              writable=True),
              help='The target to write to. If none is given, a menu is shown'
              ' to select one.')
@click.option('--verbose',
              '-v',
              is_flag=True,
              default=False,
              help='Output more detailed information.')
@click.option('--i-know-what-im-doing',
              is_flag=True,
              default=False,
              help='Disable all safety checks.')
@click.option('-p',
              '--pause',
              is_flag=True,
              default=False,
              help='Pause before exiting')
@click.version_option()
def wrimg(image_file, target, verbose, i_know_what_im_doing, limit, chunk_size,
          decompress, max_size, eject, pause):
    if pause:
        atexit.register(lambda: input('Press enter to close'))

    if verbose:
        info = click.echo
    else:
        info = lambda *args, **kwargs: None

    error = partial(click.echo, err=True)

    if not target:
        candidates = []
        for dev in sorted(Device.iter_block_devices(), key=lambda d: d.path):
            ok, msg = candidate_for_writing(dev, max_size)
            if not ok:
                info('skipping {}: {}'.format(dev.path, msg))
                continue
            candidates.append(dev)

        if not candidates:
            error('No device given on command-line and no suitable candidate '
                  'found')
            sys.exit(1)
        elif len(candidates) == 1:
            target = candidates[0]
        else:
            # display menu
            for i, c in enumerate(candidates):
                click.echo('[{}] {}'.format(i, dev_info(c)))

            idx = int(click.prompt('Select a device',
                                   type=click.Choice(map(str, range(len(
                                       candidates))))))

            target = candidates[idx]
    else:
        target = Device(target)

    # sanity-check target-device
    ok, msg = candidate_for_writing(target, max_size)

    if not ok:
        if not i_know_what_im_doing:
            error('{.path}: {}.\nAdd --i-know-what-im-doing to disable this '
                  'check.'.format(target, msg))
            sys.exit(0)
        error('WARNING: {}: {}'.format(dev_info(target), msg))

    # determine compression type
    verb = 'Write'

    if decompress == 'auto':
        if image_file.endswith('.xz'):
            decompress = 'xz'
        elif image_file.endswith('.iso') or image_file.endswith('.img'):
            decompress = None
        else:
            error('Could not determine compression type from file-ending')
            sys.exit(1)
    elif decompress == 'none':
        decompress = None

    if decompress:
        info('Decompression enabled, using {}'.format(decompress))
        verb = 'Decompress ({}) and write'.format(decompress)

    # confirm start, featuring the defensive assert!
    assert click.confirm('{} to {}?'.format(verb, dev_info(target)),
                         err=True,
                         abort=True)

    # determine number of bytes to write
    img_st = os.stat(image_file)

    # start with the target device size
    total = target.size

    if not decompress and img_st.st_mode & S_IFREG:
        # regular file, limit by its size
        total = min(total, img_st.st_size)

    # apply limit
    if limit is not None:
        total = min(total, limit)

    info('Copying {:.0f} bytes from {} to {.path}'.format(total, image_file,
                                                          target))

    with open(image_file, 'rb') as src, target.open('wb') as dst:
        # compression hooks in here
        if decompress:
            if decompress == 'xz':
                decompress = subprocess.Popen(
                    ['xz', '--decompress', '--stdout'],
                    stdout=subprocess.PIPE,
                    stdin=src, )
            else:
                raise NotImplementedError('Unknown compressoin type {}'
                                          .format(decompress))

            src = decompress.stdout

        reader = Reader(src, chunk_size, limit)

        if not decompress:
            pbar = click.progressbar(length=total,
                                     label='writing',
                                     info_sep='| ')
        else:

            def show_bytes_written(item):
                return 'total: {:.1f H}'.format(ByteSize(reader.bytes_read))

            pbar = click.progressbar(reader,
                                     label='writing',
                                     info_sep='| ',
                                     item_show_func=show_bytes_written)

        with pbar as bar:
            chunk_source = pbar if decompress else reader

            for chunk in chunk_source:
                # measure time
                start = time.time()

                dst.write(chunk)
                dst.flush()
                os.fsync(dst.fileno())

                end = time.time()

                speed = ByteSize(len(chunk) / (end - start))

                # adjust chunk size if needed
                if chunk_size is None:
                    if end - start > 2:
                        # took longer then two seconds, halve bufsize
                        reader.decrease_buffer()
                    elif end - start < 0.5:
                        reader.increase_buffer()

                bar.label = '{:.1f H}/s'.format(speed)

                if not decompress:
                    bar.update(len(chunk))

    # we're done writing, call eject
    info('Ejecting {}'.format(target.path))
    subprocess.check_call(['eject', target.path])
