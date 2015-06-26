import os
import pytest


from wrimg.devices import Device


@pytest.fixture
def blkpath():
    return '/dev/sdg'


@pytest.fixture
def regpath():
    return 'setup.py'


@pytest.fixture
def regdev(regpath):
    return Device(regpath)


@pytest.fixture
def blkdev(blkpath):
    return Device(blkpath)


def test_fixtures_exist(blkpath, regpath):
    assert os.path.exists(blkpath)
    assert os.path.exists(regpath)


def test_is_device_reg(regdev):
    assert regdev.is_device is False


def test_is_device_blk(blkdev):
    assert blkdev.is_device is True


def test_removable(blkdev):
    assert blkdev.is_removable is True
