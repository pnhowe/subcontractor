import logging

from cinp.client import CInP, NotFound


class Contractor():
  def __init__( self, site, host, root_path, proxy ):
    super().__init__()
    self.module_list = []
    self.site = '{0}Site/Site:{1}:'.format( root_path, site )
    self.cinp = CInP( host=host, root_path=root_path, proxy=proxy )

  def setModuleList( self, module_list ):
    self.module_list = module_list

  def getSite( self ):
    try:
      return self.cinp.get( self.site )
    except NotFound:
      return None

  def getJobs( self, job_count ):
    logging.debug( 'contractor: asking for "{0}" more jobs'.format( job_count ) )
    return self.cinp.call( '/api/v1/SubContractor/Dispatch(getJobs)', { 'site': self.site, 'module_list': self.module_list, 'job_count': job_count } )

  def jobResults( self, job_id, data, cookie ):
    logging.debug( 'contractor: sending results for job "{0}"'.format( job_id ) )
    return self.cinp.call( '/api/v1/SubContractor/Dispatch(jobResults)', { 'job_id': job_id, 'cookie': cookie, 'data': data } )

  def jobError( self, job_id, msg, cookie ):
    logging.debug( 'contractor: sending error for job "{0}"'.format( job_id ) )
    self.cinp.call( '/api/v1/SubContractor/Dispatch(jobError)', { 'job_id': job_id, 'cookie': cookie, 'msg': msg } )

  def getDHCPdDynamidPools( self ):
    logging.debug( 'contractor: getting dynamic pools' )
    return self.cinp.call( '/api/v1/SubContractor/DHCPd(getDynamicPools)', { 'site': self.site } )

  def getDHCPdStaticPools( self ):
    logging.debug( 'contractor: getting static assignments by mac' )
    return self.cinp.call( '/api/v1/SubContractor/DHCPd(getStaticPools)', { 'site': self.site } )
