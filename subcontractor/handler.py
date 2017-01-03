import logging
#import threadding

class Handler( object ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.max_concurent_jobs = 0
    self.job_delay = 5
    self.job_queue = []

  @property
  def empty_slots( self ):
    return self.max_concurent_jobs - len( self.job_queue )

  def setLimits( self, job_delay=None, max_concurent_jobs=None ):
    if job_delay is not None and job_delay > 0 and job_delay < 60:
      logging.info( 'handler: setting job_delay to "{0}"'.format( job_delay ) )
      self.job_delay = job_delay

    if max_concurent_jobs is not None and max_concurent_jobs > 0 and max_concurent_jobs < 100:
      logging.info( 'handler: setting max_concurent_jobs to "{0}"'.format( max_concurent_jobs ) )
      self.max_concurent_jobs = max_concurent_jobs

  def addJobs( self, job_list ): # must return immeditally, unless there are more jobs in jobs_list than fit in the remaining slots
    logging.info( 'handler: adding more jobs "{0}"....'.format( job_list ) )
