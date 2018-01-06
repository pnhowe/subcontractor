from datetime import datetime, timedelta
from asyncio import Semaphore

from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class DynamicPool():
  def __init__( self, gateway, netmask, dns_server, domain_name, lease_time, address_map ):  # lease_time in seconds
    super().__init__()
    self.netmask = ipv4( netmask ).list()
    self.gateway = ipv4( gateway ).list()
    self.domain_name = strlist( domain_name ).list()
    self.boot_file = strlist( '' ).list()
    self.dns_server = ipv4( dns_server ).list()
    self.address_map = {}  # key is address, value is mac
    self.expires_map = {}  # key is address, value is expires datetime
    self.lease_time = ipv4( lease_time ).list()
    self.lease_delta = timedelta( seconds=lease_time )
    self.address_map_lock = Semaphore()

    self._update_address_list( address_map.keys() )  # TODO: don't discard the bootfile

  def lookup( self, mac, assign ):
    print( '~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print( mac, assign )
    print( self.address_map )
    print( self.expires_map )
    print( '~~~~~~~~~~~~~~~~~~~~~~~~~~')

    address = None
    self.address_map_lock.acquire()
    try:
      for key, value in self.address_map.items():
        if value == mac:
          address = key
          break

      if address is None and assign is True:
        for key, value in self.address_map.items():
          if value is None:
            address = key
            break

        if address is not None:
          self.address_map[ address ] = mac

    finally:
      self.address_map_lock.release()

    if address is None:
      return None

    self.expires_map[ address ] = self.lease_delta + datetime.utcnow()

    print( '~~~~~~~~~~~~~~~~~~~~~~~~~~######')
    print( mac, assign, address )
    print( self.address_map )
    print( self.expires_map )
    print( '~~~~~~~~~~~~~~~~~~~~~~~~~~######')

    host_name = 'dynamic_{0}'.format( address )
    return ( ipv4( address ).list(), self.netmask, self.gateway, self.dns_server, strlist( host_name ).list(), self.domain_name, self.boot_file, self.lease_time )

  def release( self, mac ):
    address = None
    self.address_map_lock.acquire()
    try:
      for key, value in self.address_map.items():
        if value == mac:
          address = key
          break
    finally:
      self.address_map_lock.release()

    if address is None:
      return

    self.address_map_lock.acquire()
    try:
      self.address_map[ address ] = None
      self.expires_map[ address ] = None
    finally:
      self.address_map_lock.release()

    return

  def decline( self, mac ):
    self.release( mac )

  # Update the addresslist to the specified list, anything not in the new list will be removed
  # any new entries will be added
  def _update_address_list( self, address_list ):  # only call during constructor, otherwise need some locking
    add_list = set( address_list ) - set( self.address_map.keys() )
    remove_list = set( self.address_map.keys() ) - set( address_list )

    for address in add_list:
      self.address_map[ address ] = None
      self.expires_map[ address ] = None

    for address in remove_list:
      try:
        del self.expires_map[ address ]
      except KeyError:
        pass

      try:
        del self.address_map[ address ]
      except KeyError:
        pass

  def cleanup( self ):
    self.address_map_lock.acquire()
    try:
      address_list = set( self.address_map.keys() )

      # make sure there are no mac nor expires for addresses that do not exist
      for item in set( self.expires_map.keys() ) - address_list:
        del self.expires_map[ item ]

      # look for expires values that are in the past
      now = datetime.utcnow()
      for address in self.expires_map.keys():
        if self.expires_map[ address ] is not None and self.expires_map[ address ] < now:
          print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ {0}'.format( address ))
          print( self.expires_map[ address ], now )
          self.expires_map[ address ] = None
          self.address_map[ address ] = None

    finally:
      self.address_map_lock.release()
