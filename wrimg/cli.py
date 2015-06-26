from functools import partial
import sys

import click

from .devices import Device


# this will possibly have to be adjusted in the future with huge usb-sticks
G = 1024 ** 3
MAX_SIZE = 32 * G  # 32G


def candidate_for_writing(dev):
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

    if dev.size > MAX_SIZE:
        return False, 'device has a size larger than {} bytes'.format(MAX_SIZE)

    return True, None


def dev_info(dev):
    return '{0.path} ({0.size:.1fH}): {0.model}'.format(dev)


@click.command()
@click.argument('image-file')
@click.option('--target', '-t',
              type=click.Path(dir_okay=False, writable=True),
              help='The target to write to. If none is given, a menu is shown'
                   ' to select one.')
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.option('--i-know-what-im-doing', is_flag=True, default=False)
def wrimg(image_file, target, verbose, i_know_what_im_doing):
    if verbose:
        info = click.echo
    else:
        info = lambda *args, **kwargs: None

    error = partial(click.echo, err=True)

    if not target:
        candidates = []
        for dev in sorted(Device.iter_block_devices(), key=lambda d: d.path):
            ok, msg = candidate_for_writing(dev)
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

            idx = int(click.prompt(
                'Select a device',
                type=click.Choice(map(str, range(len(candidates))))
            ))

            target = candidates[idx]
    else:
        target = Device(target)

    # sanity-check target-device
    ok, msg = candidate_for_writing(target)

    if not ok:
        if not i_know_what_im_doing:
            error('{.path}: {}.\nAdd --i-know-what-im-doing to disable this '
                  'check.'
                  .format(target, msg))
            sys.exit(0)
        error('WARNING: {}: {}'.format(dev_info(target), msg))

    # confirm start, featuring the defensive assert!
    assert click.confirm('Write to {}?'.format(dev_info(target)),
                         err=True, abort=True)

    info('Writing {} to {.path}'.format(image_file, target))

    # transfer begins here
