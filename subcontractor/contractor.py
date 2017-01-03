from cinp.client import CInP

class Contractor( object ):
  def __init__( self, host, port, proxy,  *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.cinp = CInP( host=host, port=port, proxy=proxy )

  def get_jobs( self, site, plugin_list, job_count ):
    data = { 'site': site, 'plugin_list': plugin_list, 'job_count': job_count }
    resp = self.cinp.call( '/api/v1/Foreman/jobs(getJobs)', data=data )

    return resp
