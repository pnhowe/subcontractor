import logging

from cinp.client import CInP, NotFound, InvalidSession

CONTRACTOR_API_VERSION = '1.0'
SUBCONTRACTOR_USERNAME = 'subcontractor'
SUBCONTRACTOR_PASSWORD = 'subcontractor'


class Contractor():
  def relogin( func ):
    async def wrapper( self, *args, **kwargs ):
      try:
        return await func( self, *args, **kwargs )
      except InvalidSession:
        logging.debug( 'contractor: got invalid session, re-logging in and re-trying' )
        await self.logout()
        await self.login()
        return await func( self, *args, **kwargs )

    return wrapper

  def __init__( self, site, host, root_path, proxy, stop_event ):
    super().__init__()
    self.module_list = []
    self.site = '{0}Site/Site:{1}:'.format( root_path, site )
    self.host = host
    self.root_path = root_path
    self.proxy = proxy
    self.stop_event = stop_event

    self.cinp = None
    self.token = None

  async def __aenter__( self ):
    self.cinp = await CInP( host=self.host, root_path=self.root_path, proxy=self.proxy, retry_event=self.stop_event ).__aenter__()

    root, _ = await self.cinp.describe( '/api/v1/', retry_count=30 )  # be very tollerant for the initial describe, let things settle
    if root[ 'api-version' ] != CONTRACTOR_API_VERSION:
      raise Exception( 'Expected API version "{0}" found "{1}"'.format( CONTRACTOR_API_VERSION, root[ 'api-version' ] ) )

    await self.login()
    return self

  async def __aexit__( self, exc_type, exc, tb ):
    if not self.cinp:
      return

    await self.logout()
    await self.cinp.__aexit__( exc_type, exc, tb )
    self.cinp = None

  async def login( self ):
    self.token = await self.cinp.call( '/api/v1/Auth/User(login)', { 'username': SUBCONTRACTOR_USERNAME, 'password': SUBCONTRACTOR_PASSWORD }, retry_count=10 )
    self.cinp.setAuth( SUBCONTRACTOR_USERNAME, self.token )

  async def logout( self ):
    try:
      await self.cinp.call( '/api/v1/Auth/User(logout)', { 'token': self.token }, retry_count=10  )
    except InvalidSession:
      pass
    self.cinp.setAuth()
    self.token = None

  def setModuleList( self, module_list ):
    self.module_list = module_list

  async def getSite( self ):
    try:
      return await self.cinp.get( self.site )
    except NotFound:
      return None

  @relogin
  async def getJobs( self, max_jobs ):
    logging.debug( 'contractor: asking for "{0}" more jobs'.format( max_jobs ) )
    return await self.cinp.call( '/api/v1/SubContractor/Dispatch(getJobs)', { 'site': self.site, 'module_list': self.module_list, 'max_jobs': max_jobs } )

  @relogin
  async def jobResults( self, job_id, data, cookie ):
    logging.debug( 'contractor: sending results for job "{0}"'.format( job_id ) )
    return await self.cinp.call( '/api/v1/SubContractor/Dispatch(jobResults)', { 'job_id': job_id, 'cookie': cookie, 'data': data }, retry_count=20 )

  @relogin
  async def jobError( self, job_id, msg, cookie ):
    logging.debug( 'contractor: sending error for job "{0}"'.format( job_id ) )
    await self.cinp.call( '/api/v1/SubContractor/Dispatch(jobError)', { 'job_id': job_id, 'cookie': cookie, 'msg': msg }, retry_count=20 )

  @relogin
  async def getDHCPdDynamidPools( self ):
    logging.debug( 'contractor: getting dynamic pools' )
    return await self.cinp.call( '/api/v1/SubContractor/DHCPd(getDynamicPools)', { 'site': self.site }, retry_count=20 )

  @relogin
  async def getDHCPdStaticPools( self ):
    logging.debug( 'contractor: getting static assignments by mac' )
    return await self.cinp.call( '/api/v1/SubContractor/DHCPd(getStaticPools)', { 'site': self.site }, retry_count=20 )
