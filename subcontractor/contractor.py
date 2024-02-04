import logging

from cinp.client import CInP, NotFound, InvalidSession

CONTRACTOR_API_VERSION = '0.9'
SUBCONTRACTOR_USERNAME = 'subcontractor'
SUBCONTRACTOR_PASSWORD = 'subcontractor'


class Contractor():
  def relogin( func ):
    def wrapper( self, *args, **kwargs ):
      try:
        return func( self, *args, **kwargs )
      except InvalidSession:
        logging.debug( 'contractor: got invalid session, re-logging in and re-trying' )
        self.logout()
        self.login()
        return func( self, *args, **kwargs )
    return wrapper

  def __init__( self, site, host, root_path, proxy, stop_event ):
    super().__init__()
    self.module_list = []
    self.site = '{0}Site/Site:{1}:'.format( root_path, site )
    self.cinp = CInP( host=host, root_path=root_path, proxy=proxy, retry_event=stop_event )

    root, _ = self.cinp.describe( '/api/v1/', retry_count=30 )  # very tollerant for the initial describe, let things settle
    if root[ 'api-version' ] != CONTRACTOR_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( CONTRACTOR_API_VERSION, root[ 'api-version' ] ) )

    self.login()

  def login( self ):
    self.token = self.cinp.call( '/api/v1/Auth/User(login)', { 'username': SUBCONTRACTOR_USERNAME, 'password': SUBCONTRACTOR_PASSWORD }, retry_count=10 )
    self.cinp.setAuth( SUBCONTRACTOR_USERNAME, self.token )

  def logout( self ):
    try:
      self.cinp.call( '/api/v1/Auth/User(logout)', { 'token': self.token }, retry_count=10  )
    except InvalidSession:
      pass
    self.cinp.setAuth()
    self.token = None

  def setModuleList( self, module_list ):
    self.module_list = module_list

  def getSite( self ):
    try:
      return self.cinp.get( self.site )
    except NotFound:
      return None

  @relogin
  def getJobs( self, max_jobs ):
    logging.debug( 'contractor: asking for "{0}" more jobs'.format( max_jobs ) )
    return self.cinp.call( '/api/v1/SubContractor/Dispatch(getJobs)', { 'site': self.site, 'module_list': self.module_list, 'max_jobs': max_jobs } )

  @relogin
  def jobResults( self, job_id, data, cookie ):
    logging.debug( 'contractor: sending results for job "{0}"'.format( job_id ) )
    return self.cinp.call( '/api/v1/SubContractor/Dispatch(jobResults)', { 'job_id': job_id, 'cookie': cookie, 'data': data }, retry_count=20 )

  @relogin
  def jobError( self, job_id, msg, cookie ):
    logging.debug( 'contractor: sending error for job "{0}"'.format( job_id ) )
    self.cinp.call( '/api/v1/SubContractor/Dispatch(jobError)', { 'job_id': job_id, 'cookie': cookie, 'msg': msg }, retry_count=20 )

  @relogin
  def getDHCPdDynamidPools( self ):
    logging.debug( 'contractor: getting dynamic pools' )
    return self.cinp.call( '/api/v1/SubContractor/DHCPd(getDynamicPools)', { 'site': self.site }, retry_count=20 )

  @relogin
  def getDHCPdStaticPools( self ):
    logging.debug( 'contractor: getting static assignments by mac' )
    return self.cinp.call( '/api/v1/SubContractor/DHCPd(getStaticPools)', { 'site': self.site }, retry_count=20 )
