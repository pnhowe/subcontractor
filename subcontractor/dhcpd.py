import logging
import threading

from pydhcplib.dhcp_network import DhcpServer
from pydhcplib.dhcp_constants import DhcpOptions
from pydhcplib.packet import DhcpPacket
from pydhcplib.type_ipv4 import ipv4
from pydhcplib.type_strlist import strlist
from pydhcplib.type_hw_addr import hwmac


class DHCPd( DhcpServer, threading.Thread  ):
  def __init__( self, listen_interface, listen_address, tftp_server ):
    super().__init__( listen_interface, listen_address, 68, 67 )
    self.cont = True
    self.pool_list = []
    self.tftp_server = ipv4( tftp_server ).list()

  def HandleDhcpDiscover( self, request ):
    logging.info( 'DHCPd: Recieved Discover:\n{0}'.format( request ) )
    mac = hwmac( str( request.GetHardwareAddress() ) )
    for pool in self.pool_list:
      item = pool.lookup( mac, True )
      if item is not None:
        break

    if item is None:
      logging.info( 'DHCPd: mac "{0}" does not have an entry, ignorning.'.format( mac ) )
      return

    address, netmask, gateway, dns_server, boot_file, host_name, domain_name = item

    requested_option_list = request.GetOption( 'paramater_request_list' )
    user_class = strlist( request.GetOption( 'user_class' ) ).str()
    reply = DhcpPacket()
    reply.CreateDhcpOfferPacketFrom( request )
    # reply.SetOption( 'server_identifier', self.dhcp_server_ip )  # the dhcp server's ip
    reply.SetOption( 'yiaddr', address )
    reply.SetOption( 'subnet_mask', netmask )
    reply.SetOption( 'router', gateway )
    reply.SetOption( 'host_name', host_name )
    reply.SetOption( 'domain_name', domain_name )
    reply.SetOption( 'domain_name_server', dns_server )

    if user_class == 'iPXE':
      reply.setOption( '176', [ 1 ] )  # disable iPXE's waiting on proxy DHCP

    if DhcpOptions[ 'bootfile_name' ] in requested_option_list:
      reply.SetOption( 'siaddr', self.tftp_server )
      reply.SetOption( 'file', boot_file )

    logging.info( 'DHCPd: Sending Offer:\n{0}'.format( reply ) )
    self.SendDhcpPacket( request, reply )

  def HandleDhcpRequest( self, packet ):
    logging.info( 'DHCPd: Request:\n{0}'.format( packet ) )

  def HandleDhcpDecline( self, packet ):
    logging.info( 'DHCPd: Decline:\n{0}'.format( packet ) )

  def HandleDhcpRelease( self, packet ):
    logging.info( 'DHCPd: Release:\n{0}'.format( packet ) )
    mac = hwmac( str( packet.GetHardwareAddress() ) )
    for pool in self.pool_list:
      pool.release( mac )

  def HandleDhcpInform( self, packet ):
    logging.info( 'DHCPd: Inform:\n{0}'.format( packet ) )

  def add_pool( self, pool ):
    self.pool_list.append( pool )

  def run( self ):
    while self.cont:
      self.GetNextDhcpPacket( timeout=5 )

  def stop( self ):
    self.cont = False
