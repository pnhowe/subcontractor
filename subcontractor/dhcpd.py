import logging
import threading

from pydhcplib.dhcp_network import DhcpServer


class DHCPd( DhcpServer, threading.Thread  ):
  def __init__( self, listen_interface, listen_address, tftp_server ):
    super().__init__( listen_interface, listen_address, 68, 67 )
    self.cont = True

  def HandleDhcpDiscover( self, packet ):
    logging.info( 'DHCPd: Discover:\n{0}'.format( packet ) )

  def HandleDhcpRequest( self, packet ):
    logging.info( 'DHCPd: Request:\n{0}'.format( packet ) )

  def HandleDhcpDecline( self, packet ):
    logging.info( 'DHCPd: Decline:\n{0}'.format( packet ) )

  def HandleDhcpRelease( self, packet ):
    logging.info( 'DHCPd: Release:\n{0}'.format( packet ) )

  def HandleDhcpInform( self, packet ):
    logging.info( 'DHCPd: Inform:\n{0}'.format( packet ) )

  def run( self ):
    while self.cont:
      self.GetNextDhcpPacket( timeout=5 )

  def stop( self ):
    self.cont = False
