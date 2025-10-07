import logging
import hashlib
import copy
import asyncio
from importlib import import_module


def _hideify_internal( salt, value_map ):
  if isinstance( value_map, list ):
    iter = enumerate( value_map )
  elif isinstance( value_map, dict ):
    iter = value_map.items()
  else:
    return value_map

  for name, value in iter:
    if isinstance( value, ( dict, list ) ):
      value_map[ name ] = _hideify_internal( salt, copy.copy( value_map[ name ] ) )

    elif isinstance( value, str ) and isinstance( name, str ) and any( [ i in name for i in ( 'password', 'token', 'secret' ) ] ):  # this should match contractor/Records/lib.py - prepConfig
      try:
        value_map[ name ] = salt + ':' + hashlib.sha256( ( salt + ':' + value ).encode() ).hexdigest()
      except KeyError:
        pass

  return value_map


def _hideify( paramaters ):
  salt = 'salt'  # TODO: get a random something, or does it matter if/how often this changes?

  return _hideify_internal( salt, copy.copy( paramaters ) )


class JobWorker():
  def __init__( self, contractor, cookie, job_id, function, paramaters, semaphore ):
    super().__init__()
    self.contractor = contractor
    self.cookie = cookie
    self.job_id = job_id
    self.function = function
    self.paramaters = paramaters
    self.semaphore = semaphore

  async def run( self ):
    logging.debug( 'handler: acquring lock for "{0}"...'.format( self.job_id ) )
    async with self.semaphore:
      logging.debug( 'handler: starting job "{0}" with "{1}"'.format( self.function, _hideify( self.paramaters ) ) )
      try:
        data = self.function( self.paramaters )
      except Exception as e:
        logging.exception( 'handler: Exception with function "{0}" paramaters "{1}"'.format( self.function, _hideify( self.paramaters ) ) )
        self.contractor.jobError( self.job_id, 'Unhandled Exception "{0}"({1})'.format( e, type( e ).__name__ ), self.cookie )
        return

    logging.debug( 'handler: lock for "{0}" released'.format( self.job_id ) )

    if not isinstance( data, dict ):
      logging.error( 'handler: result from function was not a dict, got "{0}"({1})'.format( str( data )[ 0:50 ], type( data ).__name__ ) )
      self.contractor.jobError( self.job_id, 'result was not a dict, got "{0}"({1})'.format( data, type( data ).__name__ ), self.cookie )

    logging.debug( 'handler: results of "{0}" with "{1}" is "{2}"'.format( self.function, _hideify( self.paramaters ), data ) )
    response = 'Error'
    while response == 'Error':
      response = self.contractor.jobResults( self.job_id, data, self.cookie )  # this is after releasing the semaphore so we are not holding things up if sending the results requires retries
      logging.info( 'handler: job "{0}" complete, contractor said "{1}"'.format( self.job_id, response ) )
      if response == 'Accepted':
        break

      if response != 'Error':
        raise Exception( 'Unknown jobResults response "{0}"'.format( response ) )

      logging.debug( 'handler: Contractor said it had an error, sleeping before trying again...' )
      asyncio.sleep( 60 )


class Handler():
  def __init__( self, contractor ):
    super().__init__()
    self.contractor = contractor
    self.max_concurent_jobs = 0  # there is not a semaphore to inforce this, this is used to limit the number of jobs being requested
    self.job_delay = 5
    self.module_map = {}
    self.semaphore_map = {}
    self.task_list = []

  @property
  def empty_slots( self ):
    return self.max_concurent_jobs - len( self.task_list )

  @property
  def module_list( self ):
    return list( self.module_map.keys() )

  def registerModule( self, path, limit ):
    module = import_module( path )

    logging.info( 'handler: registering module "{0}" with limit "{1}"...'.format( module.MODULE_NAME, limit ) )
    self.module_map[ module.MODULE_NAME ] = module.MODULE_FUNCTIONS
    self.semaphore_map[ module.MODULE_NAME ] = asyncio.Semaphore( limit )

  def setLimits( self, job_delay=None, max_concurent_jobs=None ):
    if max_concurent_jobs is not None and ( max_concurent_jobs < 0 or max_concurent_jobs > 100 ):
      raise TypeError( 'max_concurent_jobs is invalid' )

    if job_delay is not None and ( job_delay < 0 or job_delay > 60 ):
      raise TypeError( 'job_delay is invalid' )

    if job_delay is not None:
      logging.info( 'handler: setting job_delay to "{0}"'.format( job_delay ) )
      self.job_delay = job_delay

    if max_concurent_jobs is not None:
      logging.info( 'handler: setting max_concurent_jobs to "{0}"'.format( max_concurent_jobs ) )
      self.max_concurent_jobs = max_concurent_jobs

  def addJobs( self, job_list ):
    logging.debug( 'handler: adding more jobs "{0}"....'.format( _hideify( job_list ) ) )

    for job in job_list:
      try:
        semaphore = self.semaphore_map[ job[ 'module' ] ]
      except KeyError:
        logging.error( 'handler: Unable to find semaphore for module "{0}"'.format( job[ 'module' ] ) )
        continue

      try:
        function = self.module_map[ job[ 'module' ] ][ job[ 'function' ] ]
      except KeyError:
        logging.error( 'handler: Unable to find function "{0}" in module "{1}", job dropped.'.format( job[ 'function' ], job[ 'module' ] ) )
        continue

      worker = JobWorker( self.contractor, job[ 'cookie' ], job[ 'job_id' ], function, job[ 'paramaters' ], semaphore )
      self.task_list.append( asyncio.create_task( worker.run() ) )

  def checkTasks( self ):
    logging.debug( 'handler: curenly have {0} tasks'.format( len( self.task_list ) ) )
    for i in range( len( self.task_list ) - 1, -1, -1 ):
      if self.task_list[ i ].done:
        logging.debug( 'handler: task "{0}" is done.'.format( i ) )
        del self.task_list[ i ]

  def wait( self ):
    while self.task_list:
      asyncio.sleep( 2 )
      self.checkTasks()

  def logStatus( self ):
    for module_name in self.module_map:
      logging.info( 'handler: module "{0}": {1} slots aviable'.format( module_name, self.semaphore_map[ module_name ]._value ) )
