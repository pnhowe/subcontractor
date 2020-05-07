from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class StaticPool():
  def __init__( self, lease_time ):
    super().__init__()
    self.mac_map = {}
    self.lease_time = ipv4( lease_time ).list()

  def lookup( self, mac, assign ):
    try:
      return self.mac_map[ mac ]
    except KeyError:
      return None

  def release( self, mac ):
    return

  def decline( self, mac ):
    return

  # set address to None to remove entry
  def update_entry( self, mac, address=None, netmask=None, gateway=None, dns_server=None, host_name=None, domain_name=None, console=None ):
    if address is None:
      try:
        del self.mac_map[ mac ]
      except KeyError:
        pass

      return

    self.mac_map[ mac ] = ( ipv4( address ).list(),
                            ipv4( netmask ).list(),
                            ipv4( gateway ).list(),
                            ipv4( dns_server ).list(),
                            strlist( host_name ).list(),
                            strlist( domain_name ).list(),
                            console,
                            self.lease_time )

  # update everything, if it's not in this list, it will get removed
  def update( self, entry_map ):
    for key, value in entry_map.items():
      gateway = value.get( 'gateway', 0 )
      if gateway is None:
        gateway = 0
      self.mac_map[ key ] = ( ipv4( value.get( 'ip_address', 0 ) ).list(),
                              ipv4( value.get( 'netmask', 0 ) ).list(),
                              ipv4( gateway ).list(),
                              ipv4( value.get( 'dns_server', 0 ) ).list(),
                              strlist( value.get( 'host_name', '' ) ).list(),
                              strlist( value.get( 'domain_name', '' ) ).list(),
                              value.get( 'console', None ),
                              self.lease_time )

    for item in set( self.mac_map.keys() ) - set( entry_map.keys() ):
      del self.mac_map[ item ]

  def cleanup( self ):
    pass

  def summary( self ):
    result = {}
    for mac, details in self.mac_map.items():
      result[ mac ] = ipv4( details[ 0 ] ).str()

    return result

  def dump_cache( self ):
    return self.mac_map

  def load_cache( self, cache ):
    if self.mac_map:
      raise Exception( 'allready loaded, can not restore cache' )

    self.mac_map = cache
