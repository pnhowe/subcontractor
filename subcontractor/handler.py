import logging
#import threadding

from importlib import import_module


class Handler( object ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.max_concurent_jobs = 0
    self.job_delay = 5
    self.job_queue = []
    self.plugin_map = {}
    self.plugin_limit = {}

  @property
  def empty_slots( self ):
    return self.max_concurent_jobs - len( self.job_queue )

  @property
  def plugin_list( self ):
    return self.plugin_map.keys()

  def registerPlugin( self, path ):
    module = import_module( path )

    self.plugin_map[ module.name ] = module.handler
    self.plugin_limit[ module.name ] = 0


  def setLimits( self, plugin=None, job_delay=None, max_concurent_jobs=None ):
    if max_concurent_jobs is not None and ( max_concurent_jobs < 0 or max_concurent_jobs > 100 ):
      raise TypeError( 'max_concurent_jobs is invalid' )
    if job_delay is not None and ( job_delay < 0 or job_delay > 60 ):
      raise TypeError( 'job_delay is invalid' )

    if plugin is not None:
      if max_concurent_jobs is None:
        raise TypeError( 'max_concurent_jobs is required when plugin is specified' )
      try:
        self.plugin_limit[ plugin ] = max_concurent_jobs
      except KeyError:
        raise Exception( 'plugin "{0}" not loaded'.format( plugin ) )

      return

    if job_delay is not None:
      logging.info( 'handler: setting job_delay to "{0}"'.format( job_delay ) )
      self.job_delay = job_delay

    if max_concurent_jobs is not None:
      logging.info( 'handler: setting max_concurent_jobs to "{0}"'.format( max_concurent_jobs ) )
      self.max_concurent_jobs = max_concurent_jobs

  def addJobs( self, job_list ): # must return immeditally, unless there are more jobs in jobs_list than fit in the remaining slots
    logging.info( 'handler: adding more jobs "{0}"....'.format( job_list ) )
