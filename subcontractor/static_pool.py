from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist


class StaticPool():
  def __init__( self ):
    super().__init__()
    self.mac_map = {}

  def lookup( self, mac ):
    try:
      return self.mac_map[ mac ]
    except KeyError:
      return None

  def release( self, mac ):
    return

  # set address to None to remove entry
  def update_entry( self, mac, address=None, netmask=None, gateway=None, dns_server=None, boot_file=None ):
    if address is None:
      try:
        del self.mac_map[ mac ]
      except KeyError:
        pass

      return

    self.mac_map[ mac ] = ( ipv4( address ).list(), ipv4( netmask ).list(), ipv4( gateway ).list(), ipv4( dns_server ).list(), strlist( boot_file ).list() )

  # update everything, if it's not in this list, it will get removed
  def update( self, entry_map ):
    for key, value in entry_map.iteritems():
      self.mac_map[ key ] = ( ipv4( value.get( 'address', None ) ).list(),
                              ipv4( value.get( 'netmask', None ) ).list(),
                              ipv4( value.get( 'gateway', None ) ).list(),
                              ipv4( value.get( 'dns_server', None ) ).list(),
                              strlist( value.get( 'boot_file', None ) ).list() )

    for item in set( self.mac_map.keys() ) - set( entry_map.keys() ):
      del self.mac_map[ item ]
