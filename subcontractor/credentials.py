import json
import ssl
from urllib import request


VAULT_TIMEOUT = 20

_handler = None


def getCredentials( value ):
  if value is None:
    return None

  return _handler.get( value )


def setup( config ):
  global _handler

  vault_type = config.get( 'credentials', 'type', fallback=None )

  if not vault_type:  # could be None or ''
    _handler = NullVault()

  elif vault_type == 'hashicorp':
    _handler = HashiCorptVault( config.get( 'credentials', 'host' ),
                                config.get( 'credentials', 'token' ),
                                config.get( 'credentials', 'proxy', fallback=None ),
                                config.getboolean( 'credentials', 'verify_ssl', fallback=True ) )

  else:
    raise ValueError( 'Unknown Credentials type "{0}"'.format( vault_type ) )


class NullVault():
  def __init__( self ):
    pass

  def get( self, name ):
    return None


class HashiCorptVault():
  def __init__( self, host, token, proxy=None, verify_ssl=True ):
    super().__init__()

    if host[-1] == '/':
      raise ValueError( 'VAULT_HOST must not end with "/"' )

    self.host = host

    handler_list = []

    if proxy is not None:
      handler_list.append( request.ProxyHandler( { 'http': proxy, 'https': proxy } ) )
    else:
      handler_list.append( request.ProxyHandler( {} ) )

    if not verify_ssl:
      handler_list.append( request.HTTPSHandler( context=ssl._create_unverified_context() ) )

    self.opener = request.build_opener( *handler_list )

    self.opener.addheaders = [
        ( 'X-Vault-Token', token ),
    ]

  def get( self, url ):
    req = request.Request( '{0}{1}'.format( self.host, url ), method='GET' )
    resp = self.opener.open( req, timeout=VAULT_TIMEOUT )
    # TODO: catch 404, 403, etc
    return json.loads( resp.read().decode() )[ 'data' ][ 'data' ]
