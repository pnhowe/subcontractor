from datetime import datetime, timedelta
from asyncio import Semaphore

from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class DynamicPool():
  def __init__( self, lease_time ):  # lease_time in seconds
    super().__init__()

    self.address_map = {}  # key is address, value is mac
    self.expires_map = {}  # key is address, value is expires datetime
    self.boot_file_map = {}  # key is address, value is boot file

    self.lease_time = ipv4( lease_time ).list()
    self.lease_delta = timedelta( seconds=lease_time )
    self.address_map_lock = Semaphore()

  def update_paramaters( self, gateway, netmask, dns_server, domain_name, address_map ):
    self.netmask = ipv4( netmask ).list()
    self.gateway = ipv4( gateway ).list() if gateway is not None else None
    self.domain_name = strlist( domain_name ).list()
    self.dns_server = ipv4( dns_server ).list()

    self._update_address_list( address_map )

  def lookup( self, mac, assign ):
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
            self.address_map[ address ] = mac
            break

    finally:
      self.address_map_lock.release()

    if address is None:
      return None

    self.expires_map[ address ] = self.lease_delta + datetime.utcnow()

    host_name = 'dynamic_{0}'.format( address )
    return ( ipv4( address ).list(), self.netmask, self.gateway, self.dns_server, strlist( host_name ).list(), self.domain_name, self.boot_file_map[ address ], self.lease_time )

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
  def _update_address_list( self, address_list ):
    self.address_map_lock.acquire()
    try:
      add_list = set( address_list ) - set( self.address_map.keys() )
      remove_list = set( self.address_map.keys() ) - set( address_list )

      for address in add_list:
        self.address_map[ address ] = None
        self.expires_map[ address ] = None
        self.boot_file_map[ address ] = None

      for address in remove_list:
        try:
          del self.expires_map[ address ]
        except KeyError:
          pass

        try:
          del self.address_map[ address ]
        except KeyError:
          pass

        try:
          del self.boot_file_map[ address ]
        except KeyError:
          pass

      for address, boot_file in address_list.items():
        self.boot_file_map[ address ] = strlist( boot_file ).list()

    finally:
      self.address_map_lock.release()

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
          self.expires_map[ address ] = None
          self.address_map[ address ] = None

    finally:
      self.address_map_lock.release()

  def summary( self ):
    result = {}
    for address, mac in self.address_map.items():
      result[ address ] = mac

    return result

  def dump_cache( self ):
    return ( self.address_map, self.expires_map, self.boot_file_map )

  def load_cache( self, cache ):
    if self.address_map:
      raise Exception( 'allready loaded, can not restore cache' )

    ( self.address_map, self.expires_map, self.boot_file_map ) = cache
