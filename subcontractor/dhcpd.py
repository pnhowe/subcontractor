import logging
import threading

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
    self.pool_location_map = {}
    self.pool_list = []
    self.tftp_server = ipv4( tftp_server ).list()
    self.dhcp_server_ip = ipv4( iface.getAddr( listen_interface ) ).list()

  def setOptions( self, request, reply, item ):
    address, netmask, gateway, dns_server, host_name, domain_name, boot_file, lease_time = item

    parameter_request_list = request.GetOption( 'parameter_request_list' )
    user_class = strlist( request.GetOption( 'user_class' ) ).str()

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

    if user_class == 'iPXE':
      reply.SetOption( 'ipxe.no-pxedhcp', [ 1 ] )  # disable iPXE's waiting on proxy DHCP

    if DhcpOptions[ 'bootfile_name' ] in parameter_request_list and len( boot_file ) > 0:
      reply.SetOption( 'siaddr', self.tftp_server )
      reply.SetOption( 'file', boot_file + [ 0 ] * ( 128 - len( boot_file  ) ) )

  def HandleDhcpDiscover( self, request ):
    logging.info( 'DHCPd: Recieved Discover:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    for pool in self.pool_list:
      item = pool.lookup( mac, True )
      if item is not None:
        break

    if item is None:
      logging.info( 'DHCPd: mac "{0}" does not have an entry, ignorning.'.format( mac ) )
      return

    reply = DhcpPacket()
    reply.CreateDhcpOfferPacketFrom( request )
    self.setOptions( request, reply, item )

    logging.info( 'DHCPd: Sending Offer:\n{0}'.format( reply.str() ) )
    self.SendDhcpPacket( request, reply )

  def HandleDhcpRequest( self, request ):
    logging.info( 'DHCPd: Received Request:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    for pool in self.pool_list:
      item = pool.lookup( mac, False )
      if item is not None:
        break

    if item is None:
      logging.info( 'DHCPd: mac "{0}" does not have an entry, ignorning.'.format( mac ) )
      return

    reply = DhcpPacket()
    reply.CreateDhcpAckPacketFrom( request )
    self.setOptions( request, reply, item )

    logging.info( 'DHCPd: Sending Ack:\n{0}'.format( reply.str() ) )
    self.SendDhcpPacket( request, reply )

  def HandleDhcpDecline( self, request ):
    logging.info( 'DHCPd: Revieved Decline:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    for pool in self.pool_list:
      pool.decline( mac )

  def HandleDhcpRelease( self, request ):
    logging.info( 'DHCPd: Recieved Release:\n{0}'.format( request.str() ) )
    mac = hwmac( request.GetHardwareAddress() ).str()
    for pool in self.pool_list:
      pool.release( mac )

  def add_pool( self, pool, name ):
    try:
      self.pool_list[ self.pool_location_map[ name ] ] = pool
    except KeyError:
      self.pool_location_map[ name ] = len( self.pool_list )
      self.pool_list.append( pool )

  def clean_pool( self, keep_name_list ):
      # TODO: do me!
      pass

  def cleanup( self ):
    for i in range( 0, len( self.pool_list ) ):
      self.pool_list[ i ].cleanup()

  def run( self ):
    while self.cont:
      self.GetNextDhcpPacket( timeout=5 )

  def stop( self ):
    self.cont = False
