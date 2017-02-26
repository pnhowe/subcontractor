from cinp.client import CInP

class Contractor( object ):
  def __init__( self, host, root_path, port, proxy,  *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.cinp = CInP( host=host, root_path=root_path, port=port, proxy=proxy )

  def getJobs( self, site, plugin_list, job_count ):
    args = { 'site': site, 'plugin_list': plugin_list, 'job_count': job_count }
    resp = self.cinp.call( '/api/v1/SubContractor/Dispatch(getJobs)', args=args )

    return resp
