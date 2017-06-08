from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class StaticPool():
  def __init__( self ):
    super().__init__()
    self.mac_map = {}

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
  def update_entry( self, mac, address=None, netmask=None, gateway=None, dns_server=None, host_name=None, domain_name=None, boot_file=None ):
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
                            strlist( boot_file ).list() )

  # update everything, if it's not in this list, it will get removed
  def update( self, entry_map ):
    for key, value in entry_map.items():
      self.mac_map[ key ] = ( ipv4( value.get( 'ip_address', 0 ) ).list(),
                              ipv4( value.get( 'netmask', 0 ) ).list(),
                              ipv4( value.get( 'gateway', 0 ) ).list(),
                              ipv4( value.get( 'dns_server', 0 ) ).list(),
                              strlist( value.get( 'host_name', '' ) ).list(),
                              strlist( value.get( 'domain_name', '' ) ).list(),
                              strlist( value.get( 'boot_file', '' ) ).list() )

    for item in set( self.mac_map.keys() ) - set( entry_map.keys() ):
      del self.mac_map[ item ]
