#import socket
#import httplib


class CInP( object ):
  def __init__( self, host, port, proxy=None, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.host = host
    self.port = port
    self.proxy = proxy
    print( 'cinp client "{0}" "{1}" "{2}"'.formmat( self.host, self.port, self.proxy ) )
