wrimg
=====

``wrimg`` is an alternative for dd to write images to removable media. It has
the following advantages:

* Syncs buffers after each chunk is written, allowing ``C-c`` to work
* For the same reason ``wrimg`` can make accurate predictions about the remaining time
* Automatically adjusts buffer size when copying
* Contains extra safety-checks to keep you from accidentally erasing your
  hard drives!

It is slightly slower than ``dd``, with common SD-card/USB data rates usually a
second or two. Copying between two very fast devices (like SSD-to-SSD) is
better left to ``dd``.


Installation
------------

``wrimg`` can be installed from PyPI_::

  $ pip install wrimg

.. _PyPI: http://pypi.python.org/wrimg


Usage
-----

Usage is straightforward:

  $ wrimg someimg.iso -t /dev/sdX

The ``--target/-t`` can be omitted, causing wrimg to display a menu of suitable
targets. For other options, check the ``--help`` option.
