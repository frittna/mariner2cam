Software Setup
==============

Once your :doc:`hardware setup <hardware-setup>` done, you will have to:

1. Install Mariner 2
2. Setup the `USB Gadget driver
   <https://www.kernel.org/doc/html/latest/driver-api/usb/gadget.html>`_ so that
   the printer can see uploaded files
3. Enable the serial port so the Raspberry Pi can send commands to the printer

This section will guide you through those steps.

Installing Mariner 2
--------------------

There are several ways to install Mariner 2 depending on your platform.

Debian / Ubuntu / Raspberry Pi OS (apt)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, enable the repository:

.. code-block:: shell-session

   $ curl -fsSL https://amd989.github.io/mariner/setup.sh | sudo bash

Then install mariner:

.. code-block:: shell-session

   $ sudo apt install mariner3d

Or set up the repository manually:

.. code-block:: shell-session

   $ curl -fsSL https://amd989.github.io/mariner/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/mariner3d.gpg
   $ echo "deb [signed-by=/usr/share/keyrings/mariner3d.gpg] https://amd989.github.io/mariner stable main" | sudo tee /etc/apt/sources.list.d/mariner3d.list
   $ sudo apt update
   $ sudo apt install mariner3d

Rocky Linux / RHEL / Fedora (dnf)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Quick install:

.. code-block:: shell-session

   $ curl -fsSL https://amd989.github.io/mariner/setup-rpm.sh | sudo bash
   $ sudo dnf install mariner3d

Or set up the repository manually:

.. code-block:: shell-session

   $ sudo rpm --import https://amd989.github.io/mariner/gpg.key
   $ sudo tee /etc/yum.repos.d/mariner3d.repo <<EOF
   [mariner3d]
   name=Mariner 2 - MSLA 3D Printer Controller
   baseurl=https://amd989.github.io/mariner/rpm/
   enabled=1
   gpgcheck=1
   gpgkey=https://amd989.github.io/mariner/gpg.key
   EOF
   $ sudo dnf install mariner3d

Docker
~~~~~~

Mariner 2 is available as a multi-architecture Docker image:

.. code-block:: shell-session

   $ docker run -d \
       --name mariner \
       --device /dev/ttyUSB0 \
       -v /mnt/usb_share:/mnt/usb_share \
       -p 5000:5000 \
       amd989/mariner3d

The image is also available from GitHub Container Registry:

.. code-block:: shell-session

   $ docker pull ghcr.io/amd989/mariner

.. note::
   When using Docker, you still need to configure the USB Gadget and serial
   port on the host system as described below. Pass the serial device and USB
   share volume into the container.

Automated Raspberry Pi setup
----------------------------

If you installed Mariner 2 from the apt or dnf repository on a Raspberry Pi,
the package ships a helper script that performs all of the boot-partition,
USB gadget, and serial port steps described in the rest of this page:

.. code-block:: shell-session

   $ sudo mariner3d-setup-pi

The script is idempotent — safe to re-run — and backs up each file it edits
to ``<file>.mariner.bak`` on the first run. It auto-detects your Pi model
(adding ``dr_mode=peripheral`` where needed) and the boot partition location
(``/boot`` vs ``/boot/firmware`` on Bookworm and newer).

Useful flags:

.. code-block:: shell-session

   $ sudo mariner3d-setup-pi --size 4096   # 4 GB container instead of 2 GB
   $ sudo mariner3d-setup-pi --dry-run     # show changes without applying
   $ sudo mariner3d-setup-pi --help

Once it finishes, reboot the Pi and skip ahead to :doc:`wrapping-up`. The
remaining sections on this page document the same steps manually, in case you
prefer to run them yourself or are not on a Raspberry Pi OS image.

.. note::
   The script installs a ``mariner-usb-gadget.service`` systemd unit that
   loads the ``g_mass_storage`` module at boot, replacing the legacy
   ``/etc/rc.local`` approach. If you previously followed the manual
   instructions, you can remove the ``modprobe g_mass_storage`` line from
   ``/etc/rc.local`` — the systemd unit handles it now.

USB Gadget Setup
----------------

In order to make the printer see the files uploaded to mariner, we need to
setup the `USB Gadget driver
<https://www.kernel.org/doc/html/latest/driver-api/usb/gadget.html>`_ as a Mass
Storage device. This section will guide you through that process.

Enable USB driver for gadget modules by adding this line to
``/boot/config.txt``:

If you are using a Pi Zero W or a Pi 4B add:

.. code-block:: text

   dtoverlay=dwc2

If you are using a Pi 3A+, there is a little variant as these supports device
mode or host mode, but not "true" OTG which is auto-sensing between host and
device (AKA gadget). So, for the Pi 3A+ you have to add:

.. code-block:: text

   dtoverlay=dwc2,dr_mode=peripheral

Enable the dwc2 kernel module, by adding this to your ``/boot/cmdline.txt``
just after ``rootwait``:

.. code-block:: text

   modules-load=dwc2

Setup a container file for storing uploaded files, the ``count=`` is in MB,
use multiples of 1024 to get the number of GBs you want:

.. code-block:: shell-session

   $ sudo dd bs=1M if=/dev/zero of=/piusb.bin count=2048
   $ sudo mkdosfs /piusb.bin -F 32 -I

Create the mount point for the container file:

.. code-block:: shell-session

   $ sudo mkdir -p /mnt/usb_share

Add the following line to your ``/etc/fstab`` so the container file gets
mounted on boot::

.. code-block:: text

   /piusb.bin /mnt/usb_share vfat users,gid=mariner,umask=002 0 2

Finally, make ``/etc/rc.local`` load the ``g_mass_storage`` module. If that file
doesn't exist yet, create it with the following contents:

.. code-block:: sh

   #!/bin/sh -e

   modprobe g_mass_storage file=/piusb.bin stall=0 ro=1

   exit 0

If the file exists, you should simply add the ``modprobe`` line to it.

.. code-block:: diff

    #!/bin/sh -e
   +modprobe g_mass_storage file=/piusb.bin stall=0 ro=1
    exit 0

Once you restart the pi (or potentially run ``sudo mount -a``), the printer
should start seeing the contents of ``/mnt/usb_share``.

Setting up the serial port
--------------------------

First, enable UART by adding this to ``/boot/config.txt``::

   enable_uart=1

In order for the Pi to communicate with the printer's mainboard over
serial, you also need to disable the Pi's console over the serial port:

.. code-block:: shell-session

   $ sudo systemctl stop serial-getty@ttyS0
   $ sudo systemctl disable serial-getty@ttyS0

Lastly, remove the console from ``cmdline.txt`` by removing this from it::

   console=serial0,115200
