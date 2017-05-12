from datetime import datetime, timedelta

from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class DynamicPool():
  def __init__( self, gateway, netmask, dns_server, domain_name, boot_file, lease_time ):  # lease_time in seconds
    super().__init__()
    self.netmask = ipv4( netmask ).list()
    self.gateway = ipv4( gateway ).list()
    self.domain_name = strlist( domain_name ).list()
    self.boot_file = strlist( boot_file ).list()
    self.dns_server = ipv4( dns_server ).list()
    self.address_map = {}  # key is address, value is mac
    self.mac_map = {}      # key is mac, value is address
    self.expires_map = {}  # key is address, value is expires datetime
    self.lease_delta = timedelta( seconds=self.lease_time )

  def lookup( self, mac, assign=False ):
    address = None
    try:
      address = self.mac_map[ mac ]
    except KeyError:
      pass

    if address is None and assign is True:
      # create semaphore to lock the address_map
      for key, value in self.address_map.iteritems():
        if value is None:
          address = key
          break

      if address is not None:
        self.mac_map[ mac ] = address
      # release semaphore

    if address is None:
      return None

    # create semaphore
    self.expires_map[ address ] = self.lease_delta + datetime.utcnow()
    # release semaphore

    host_name = 'dynamic_{0}'.format( address )
    return ( address, self.netmask, self.gateway, self.dns_server, host_name, self.domain_name, self.boot_file )

  def release( self, mac ):
    # get semaphore
    try:
      address = self.mac_map[ mac ]
    except KeyError:
      # release semaphore
      return

    self.address_map[ address ] = None
    self.expires_map[ address ] = None
    # release semaphore
    return

  # Update the addresslist to the specified list, anythingnot in the new list will be removed
  # any new entries will be added
  def update_address_list( self, address_list ):
    address_list = [ ipv4( i ) for i in address_list ]
    add_list = set( address_list ) - set( self.pool_map.keys() )
    remove_list = set( self.pool_map.keys() ) - set( address_list )

    # create semaphore
    for address in add_list:
      self.address_map[ address ] = None
      self.expires_map[ address ] = None

    for address in remove_list:
      try:
        del self.mac_map[ self.address_map[ address ] ]
      except KeyError:
        pass

      try:
        del self.expires_map[ address ]
      except KeyError:
        pass

      try:
        del self.address_map[ address ]
      except KeyError:
        pass

    # release semaphore

  def cleanup( self ):
    # get semaphore
    address_list = set( self.address_map.keys() )

    # make sure there are no mac nor expires for addresses that do not exist
    for item in set( self.expires_map.keys() ) - address_list:
      del self.expires_map[ item ]

    for item in set( self.mac_map.values() ) - address_list:
      for key, value in self.mac_map.iteritems():
        if value == item:
          del self.mac_map[ key ]

    # look for expires values that are in the past
    now = datetime.utcnow()
    for item in self.expires_map.keys():
      if self.expires_map[ item ] < now:
        mac = self.address_list[ item ]
        del self.mac_map[ mac ]
        self.expires_map[ item ] = None
        self.address_mav[ item ] = None

    # release semaphore
