import logging
import threading
import pickle

from pydhcplib.dhcp_network import DhcpServer
from pydhcplib.dhcp_constants import DhcpOptions
from pydhcplib.dhcp_packet import DhcpPacket
from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist
from pydhcplib.type_hwmac import hwmac
from pydhcplib.interface import interface


class DHCPd( DhcpServer, threading.Thread  ):
  def __init__( self, listen_interface, listen_address, tftp_server ):
    super().__init__( listen_interface, listen_address, 68, 67 )
    iface = interface()
    if listen_interface not in iface.getInterfaceList():
      raise Exception( 'Interface "{0}" not available'.format( listen_interface ) )

    self.cont = True
    self.pool_map = {}
    self.pool_order = []
    self.tftp_server = ipv4( tftp_server ).list()
    self.dhcp_server_ip = ipv4( iface.getAddr( listen_interface ) ).list()

  def setOptions( self, request, reply, item ):
    address, netmask, gateway, dns_server, host_name, domain_name, console, config_uuid, lease_time = item

    parameter_request_list = request.GetOption( 'parameter_request_list' )
    user_class = strlist( request.GetOption( 'user_class' ) ).str()
    architecture = request.GetOption( 'client_system' )

    reply.SetOption( 'server_identifier', self.dhcp_server_ip )
    reply.SetOption( 'ip_address_lease_time', lease_time )
    reply.SetOption( 'yiaddr', address )
    reply.SetOption( 'subnet_mask', netmask )
    if gateway:
      reply.SetOption( 'router', gateway )

    if host_name:
      reply.SetOption( 'host_name', host_name )

    if domain_name:
      reply.SetOption( 'domain_name', domain_name )
      reply.SetOption( 'domain_search', [ domain_name ] )

    if dns_server:
      reply.SetOption( 'domain_name_server', dns_server )

    if config_uuid:
      reply.SetOption( 'config_file', config_uuid )

    if user_class == 'iPXE':
      reply.SetOption( 'ipxe.no-pxedhcp', [ 1 ] )  # disable iPXE's waiting on proxy DHCP

    if DhcpOptions[ 'bootfile_name' ] in parameter_request_list and console is not None:
      reply.SetOption( 'siaddr', self.tftp_server )
      try:
        architecture = int( architecture[0] << 8 ) + int( architecture[1] )
      except IndexError:
        architecture = 0
      # see https://www.iana.org/assignments/dhcpv6-parameters/dhcpv6-parameters.xhtml#processor-architecture
      if architecture == 7:  # x64 UEFI
        boot_file = strlist( '{0}.efi'.format( console ) ).list()
      # elif architecture == 6: # x86 UEFI
      #   boot_file = strlist( '{0}.efi'.format( console ) ).list()
      else:  # 0 = x86 BIOS
        boot_file = strlist( '{0}.kpxe'.format( console ) ).list()

      reply.SetOption( 'file', boot_file + [ 0 ] * ( 128 - len( boot_file  ) ) )

  def HandleDhcpDiscover( self, request ):
    logging.debug( 'DHCPd: Recieved Discover:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    logging.info( 'DHCPd: Recieved Discover from "{0}"'.format( mac ) )

    for name in self.pool_order:
      item = self.pool_map[ name ].lookup( mac, True )
      if item is not None:
        break

    if item is None:
      logging.warning( 'DHCPd: mac "{0}" does not have an entry, ignorning.'.format( mac ) )
      return

    reply = DhcpPacket()
    reply.CreateDhcpOfferPacketFrom( request )
    self.setOptions( request, reply, item )

    logging.info( 'DHCPd: Sending Offer to "{0}"'.format( mac ) )
    logging.debug( 'DHCPd: Sending Offer:\n{0}'.format( reply.str() ) )
    self.SendDhcpPacket( request, reply )

  def HandleDhcpRequest( self, request ):
    logging.debug( 'DHCPd: Received Request:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    logging.info( 'DHCPd: Recieved Request from "{0}"'.format( mac ) )

    for name in self.pool_order:
      item = self.pool_map[ name ].lookup( mac, True )
      if item is not None:
        break

    if item is None:
      logging.warning( 'DHCPd: mac "{0}" does not have an entry, ignorning.'.format( mac ) )
      return

    reply = DhcpPacket()
    reply.CreateDhcpAckPacketFrom( request )
    self.setOptions( request, reply, item )

    logging.info( 'DHCPd: Sending Ack to "{0}"'.format( mac ) )
    logging.debug( 'DHCPd: Sending Ack:\n{0}'.format( reply.str() ) )
    self.SendDhcpPacket( request, reply )

  def HandleDhcpDecline( self, request ):
    logging.debug( 'DHCPd: Revieved Decline:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    logging.info( 'DHCPd: Recieved Decline from "{0}"'.format( mac ) )

    for pool in self.pool_map.values():
      pool.decline( mac )

  def HandleDhcpRelease( self, request ):
    logging.debug( 'DHCPd: Recieved Release:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    logging.info( 'DHCPd: Recieved Release from "{0}"'.format( mac ) )

    for pool in self.pool_map.values():
      pool.release( mac )

  @property
  def pool_names( self ):
    return self.pool_map.keys()

  def add_pool( self, pool, name ):
    self.pool_map[ name ] = pool
    self.pool_order.append( name )

  def del_pool( self, name ):
    del self.pool_order[ self.pool_order.index( name ) ]
    del self.pool_map[ name ]

  def get_pool( self, name ):
    return self.pool_map[ name ]

  def cleanup( self ):
    for pool in self.pool_map.values():
      pool.cleanup()

  def save_cache( self, filepath ):
    cache = {}
    for name, pool in self.pool_map.items():
      cache[ name ] = pool.dump_cache()

    fp = open( filepath, 'wb' )
    pickle.dump( cache, fp )
    fp.close()

  def load_cache( self, filepath ):
    fp = open( filepath, 'rb' )
    cache = pickle.load( fp )
    fp.close()

    for name in cache:
      try:
        self.pool_map[ name ].load_cache( cache[ name ] )
      except KeyError:
        pass

  def run( self ):
    while self.cont:
      self.GetNextDhcpPacket( timeout=5 )

  def stop( self ):
    self.cont = False

  def summary( self ):
    result = {}
    for name, pool in self.pool_map.items():
      result[ name ] = pool.summary()

    return result
