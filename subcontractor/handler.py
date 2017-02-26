import logging
#import threadding

from importlib import import_module


class Handler( object ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.max_concurent_jobs = 0
    self.job_delay = 5
    self.job_queue = []
    self.module_map = {}
    self.module_limit = {}

  @property
  def empty_slots( self ):
    return self.max_concurent_jobs - len( self.job_queue )

  @property
  def module_list( self ):
    return self.module_map.keys()

  def registerModule( self, path ):
    module = import_module( path )

    self.module_map[ module.MODULE_NAME ] = module.MODULE_FUNCTIONS
    self.module_limit[ module.MODULE_NAME ] = 0

  def setLimits( self, module=None, job_delay=None, max_concurent_jobs=None ):
    if max_concurent_jobs is not None and ( max_concurent_jobs < 0 or max_concurent_jobs > 100 ):
      raise TypeError( 'max_concurent_jobs is invalid' )

    if job_delay is not None and ( job_delay < 0 or job_delay > 60 ):
      raise TypeError( 'job_delay is invalid' )

    if module is not None:
      if max_concurent_jobs is None:
        raise TypeError( 'max_concurent_jobs is required when module is specified' )

      try:
        self.module_limit[ module ] = max_concurent_jobs
      except KeyError:
        raise Exception( 'module "{0}" not loaded'.format( module ) )

      return

    if job_delay is not None:
      logging.info( 'handler: setting job_delay to "{0}"'.format( job_delay ) )
      self.job_delay = job_delay

    if max_concurent_jobs is not None:
      logging.info( 'handler: setting max_concurent_jobs to "{0}"'.format( max_concurent_jobs ) )
      self.max_concurent_jobs = max_concurent_jobs

  def addJobs( self, job_list ): # must return immeditally, unless there are more jobs in jobs_list than fit in the remaining slots
    logging.info( 'handler: adding more jobs "{0}"....'.format( job_list ) )

  def wait( self ):
    pass
