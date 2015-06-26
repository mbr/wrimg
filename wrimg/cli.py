from functools import partial

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


@click.command()
@click.argument('image-file')
@click.option('--target', '-t',
              type=click.Path(dir_okay=False, writable=True),
              help='The target to write to. If none is given, a menu is shown'
                   ' to select one.')
@click.option('--verbose', '-v', is_flag=True, default=False)
def wrimg(image_file, target, verbose):
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
            return 1

        # display menu
        for i, c in enumerate(candidates):
            click.echo(
                '[{1}] {0.path} ({0.size:.1fH}): {0.model}'
                .format(c, i))
        idx = int(click.prompt(
            'Select a device',
            type=click.Choice(map(str, range(len(candidates))))
        ))

        target = candidates[idx]

    info('target device: {}'.format(target))
