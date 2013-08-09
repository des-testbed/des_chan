#!/usr/bin/python
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

This module holds utility functions that may be needed by different parts of the
framework (and for the algorithms build with the framework).

The module uses PgSQL - A PyDB-SIG 2.0 compliant module to access the PostgreSQL
database. The latter is included in the Debian package python-pgsql.

Authors:    Matthias Philipp <mphilipp@inf.fu-berlin.de>,
            Felix Juraschek <fjuraschek@gmail.com>

Copyright 2008-2013, Freie Universitaet Berlin (FUB). All rights reserved.

These sources were developed at the Freie Universitaet Berlin, 
Computer Systems and Telematics / Distributed, embedded Systems (DES) group 
(http://cst.mi.fu-berlin.de, http://www.des-testbed.net)
-------------------------------------------------------------------------------
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see http://www.gnu.org/licenses/ .
--------------------------------------------------------------------------------
For further information and questions please use the web site
       http://www.des-testbed.net
       
"""

import sys
import time
import socket
import subprocess

import netifaces
from pythonwifi import iwlibs

from des_chan.error import *

def resolve_node_name(ip_address):
    """Resolves the name of the node to which the given IP address belongs.

    """
    if ip_address == "localhost" or ip_address == "127.0.0.1":
        return socket.gethostname()
    try:
        host_name = socket.gethostbyaddr(ip_address)[0]
    except socket.herror:
        raise CHANError("Unable to resolve node name (host name for IP %s unknown)" % ip_address)
    node_name = host_name.split("-ch")
    if node_name: 
        return node_name[0]
    else:
        raise CHANError("Unable to resolve node name (%s does not comply with DES naming conventions)" % host_name)


def get_node_ip(node_name, channel):
    """Returns the IP address of the wireless interface that belongs to the
    given node and is tuned to the given channel.

    """
    host_name = "%s-ch%s" % (node_name, channel)
    try:
        ip = socket.gethostbyname(host_name)
    except socket.gaierror:
        raise CHANError("Unable to get node IP (%s can not be resolved)" % host_name)
    else:
        return ip


def is_available(host):
    """Ping the supplied host and return if the host replied.

    """
    retval = subprocess.call("ping -c5 %s" % host, shell=True)
    return retval == 0


def is_interface_up(if_name):
    """Return if the supplied network interface is set up already.

    """
    # is the interface name valid?
    if if_name not in netifaces.interfaces():
        raise CHANError("Unable to check if interface is up (invalid interface name %s)" % if_name)
    # see if the interface name is listed in ifconfig
    return subprocess.call("ifconfig | grep -q %s" % if_name, shell=True) == 0


def get_if_name(channel):
    """Returns the name of the interface that is tuned to the given channel.

    """
    for if_name in iwlibs.getWNICnames():
        try:
            tuned_channel = iwlibs.Wireless(if_name).getChannel()
        except IOError:
            continue
        if tuned_channel == channel and is_interface_up(if_name):
            return if_name
    raise CHANError("No interface tuned to channel %s and set up" % channel)


def get_free_if_name(if_names=None):
    """Check (and return) a so far unused network interface

    """
    # if no interfaces are specified, use all wireless interfaces
    if not if_names:
        if_names = iwlibs.getWNICnames()
    for if_name in if_names:
        print if_name
        if not is_interface_up(if_name):
            return if_name
    raise CHANError("No free interfaces left")


def channel(iface):
    """Returns the default channel per network interface.

    """
    return {
        'wlan0': 14,
        'wlan1': 36,
        'wlan2': 40
        }.get(iface, 14)

def cell_id(iface):
    """Returns the default cell id per network interface.

    """
    return {
        'wlan0': '16:EB:FF:18:C8:6F',
        'wlan1': '46:44:4B:28:57:41',
        'wlan2': '8A:BF:D2:99:8B:45'
        }.get(iface, 'aa:aa:aa:aa:aa:aa')

def set_up_interface(if_name):
    """Sets  up an interface with ifconfig / iwconfig commands. This way, we are
    independent of the settings in /etc/network/interfaces, which may change over time.

    """
    chan = channel(if_name)
    essid = cell_id(if_name)

    # put iface down (just in case)
    subprocess.call("ifconfig " + if_name + " down", shell=True)
    subprocess.call("ifdown " + if_name, shell=True)

    subprocess.call("iwconfig " + if_name + " mode ad-hoc", shell=True)
    subprocess.call("iwconfig " + if_name + " essid des-mesh" + str(chan), shell=True)
    subprocess.call("iwconfig " + if_name + " channel " + str(chan), shell=True)
    subprocess.call("iwconfig " + if_name + " ap " + essid, shell=True)
    subprocess.call("iwconfig " + if_name + " txpower auto", shell=True)
    subprocess.call("iwconfig " + if_name + " rate 6M", shell=True)
    subprocess.call("ifconfig " + if_name + " $(calc_ip " + if_name[-1] + ") netmask 255.255.0.0", shell=True)
    # double check it the interface is up now
    #if retval != 0 or not is_interface_up(if_name):
    #    raise CHANError("Unable to set up interface %s" % if_name)


def shut_down_interface(if_name):
    """Shuts down the given interface.

    """
    subprocess.call("ifdown %s" % if_name, shell=True)
    subprocess.call("ifconfig %s down" % if_name, shell=True)
    if is_interface_up(if_name):
        raise CHANError("Unable to shut down interface %s" % if_name)


def shut_down_interfaces(if_names=None):
    """Wrapper to shut down more than one interface.

    """
    # if no interfaces are specified, use all wireless interfaces
    if not if_names:
        if_names = iwlibs.getWNICnames()
    for if_name in if_names:
        shut_down_interface(if_name)


def get_channel(if_name):
    """Returns the channel the given interface is currently operating on. 

    """
    if if_name not in iwlibs.getWNICnames():
        raise CHANError("Unable to set channel (invalid wireless interface: %s)" % if_name)
    interface = iwlibs.Wireless(if_name)
    return interface.getChannel()

def set_channel(if_name, channel, set_ip=True):
    """Set the channel for the interface. This is a bit more complicated since we also have
    to set the ESSID, Cell ID,  and the IP according to /etc/hosts.

    """
    if if_name not in iwlibs.getWNICnames():
        raise CHANError("Unable to set channel (invalid wireless interface: %s)" % if_name)
    interface = iwlibs.Wireless(if_name)
    try:
        print if_name, channel
        interface.setChannel(channel)
    except ValueError, IOError:
        raise CHANError("Unable to set channel (invalid channel: %s)" % channel)
    print "channel: %s" % interface.getChannel()
    # essid
    essid = "des-mesh-ch%d" % channel
    interface.setEssid(essid)
    print "essid: %s" % interface.getEssid()
    if interface.getEssid() != essid:
        raise CHANError("Unable to set channel (ESSID %s cannot be set)" % essid)
    # ip address
    if set_ip:
        host_name = "%s-ch%d" % (resolve_node_name("localhost"), channel)
        print host_name
        ip = socket.gethostbyname(host_name)
        print "ip: %s" % ip
        retval = subprocess.call("ifconfig %s %s netmask 255.255.255.128" %
                                 (if_name, ip), shell=True)
        if retval != 0:
            raise CHANError("Unable to set channel (IP %s cannot be assigned)"
                             % ip)
    ap_addr = "02:00:00:00:00:%02X" % channel
    interface.setAPaddr(ap_addr)
    actual_ap_addr = interface.getAPaddr()
    print "ap: %s" % actual_ap_addr
    # double check
    # if not (actual_ap_addr == ap_addr or actual_ap_addr == "00:00:00:00:00:00"):
    #    raise CHANError("Unable to set channel (AP address should be %s, but is %s)" % (ap_addr, actual_ap_addr))


def red(str):
    """Colors the given string red.

    """
    return "\033[31m%s\033[0m" % str


def green(str):
    """Colors the given string green.

    """
    return "\033[32m%s\033[0m" % str


def blue(str):
    """Colors the given string blue.

    """
    return "\033[34m%s\033[0m" % str


def bold(str):
    """Colors the given string bold.

    """
    return "\033[1m%s\033[0m" % str


def run(cmd):
    """Runs the given shell command and returns its output.

    """
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]


def busy_wait(seconds):
    """Waits the specified number of seconds and prints nice dots to indicate
    activity.

    """
    for i in range(seconds):
        print ".",
        sys.stdout.flush()
        time.sleep(1)
    print

