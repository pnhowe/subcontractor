from datetime import datetime, timedelta, UTC
from asyncio import Semaphore

from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class DynamicPool():
  def __init__( self, lease_time, mtu, vlan, console ):  # lease_time in seconds
    super().__init__()

    self.address_map = {}  # key is address, value is mac
    self.expires_map = {}  # key is address, value is expires datetime
    self.mtu = mtu
    self.vlan = vlan
    self.console = console

    self.lease_time = ipv4( lease_time ).list()
    self.lease_delta = timedelta( seconds=lease_time )
    self.address_map_lock = Semaphore()

  async def update_paramaters( self, gateway, netmask, dns_server, domain_name, address_list ):
    self.netmask = ipv4( netmask ).list()
    self.gateway = ipv4( gateway ).list() if gateway is not None else None
    self.domain_name = strlist( domain_name ).list()
    self.dns_server = ipv4( dns_server ).list()

    await self._update_address_list( address_list )

  async def lookup( self, mac, assign ):
    address = None
    async with self.address_map_lock:
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

    if address is None:
      return None

    self.expires_map[ address ] = self.lease_delta + datetime.now( UTC )

    host_name = 'dynamic_{0}'.format( address )
    return ( ipv4( address ).list(), self.netmask, self.gateway, self.mtu, self.vlan, self.dns_server, strlist( host_name ).list(), self.domain_name, None, self.console, self.lease_time )

  async def release( self, mac ):
    address = None
    async with self.address_map_lock:
      for key, value in self.address_map.items():
        if value == mac:
          address = key
          break

    if address is None:
      return

    async with self.address_map_lock:
      self.address_map[ address ] = None
      self.expires_map[ address ] = None

    return

  async def decline( self, mac ):
    await self.release( mac )

  # Update the addresslist to the specified list, anything not in the new list will be removed
  # any new entries will be added
  async def _update_address_list( self, address_list ):
    async with self.address_map_lock:
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

  async def cleanup( self ):
    async with self.address_map_lock:
      address_list = set( self.address_map.keys() )

      # make sure there are no mac nor expires for addresses that do not exist
      for item in set( self.expires_map.keys() ) - address_list:
        del self.expires_map[ item ]

      # look for expires values that are in the past
      now = datetime.now( UTC )
      for address in self.expires_map.keys():
        if self.expires_map[ address ] is not None and self.expires_map[ address ] < now:
          self.expires_map[ address ] = None
          self.address_map[ address ] = None

  def summary( self ):
    result = {}
    for address, mac in self.address_map.items():
      result[ address ] = mac

    return result

  def dump_cache( self ):
    return ( self.address_map, self.expires_map )

  def load_cache( self, cache ):
    if self.address_map:
      raise Exception( 'allready loaded, can not restore cache' )

    ( self.address_map, self.expires_map ) = cache
