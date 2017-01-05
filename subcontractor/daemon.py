import os
import sys
import signal
import argparse
import logging
import configparser
import pwd
from logging.handlers import SysLogHandler

class Daemon( object ):
  default_config_file = 'config.conf'

  def __init__( self, name, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.name = name
    self.pid_file = None

  def config( self, config ): # override
    pass

  def stop( self ): # override
    pass

  def main( self ): # override
    pass

  def run( self ):
    parser = argparse.ArgumentParser( description=self.name )
    parser.add_argument( '-c', '--config', help='location of config file', default=self.default_config_file )
    parser.add_argument( '-p', '--pid-file', help='location of the pid file', default='/var/run/{0}.pid'.format( self.name ) )
    parser.add_argument( '-d', '--debug', help='set logging level to debug', action='store_true' )
    parser.add_argument( '-u', '--user', help='user to run as, if not specified the process continues to run as the user that started it, only applys to backgrang/foreground' )
    parser.add_argument( 'action', help='action to take. background: start and daemonize, foreground: start output to console', choices=( 'background', 'foreground', 'stop', 'status' ), default=None )

    args = parser.parse_args()

    if args.action is None:
      parser.print_help()
      sys.exit( 0 )

    self.pid_file = args.pid_file

    logging.basicConfig()
    logger = logging.getLogger()

    if args.action == 'background': # has to happen before we start loggin
      logger.handlers = []
      handler = SysLogHandler( address='/dev/log', facility=SysLogHandler.LOG_DAEMON )
      handler.setFormatter( logging.Formatter( fmt='{0} [%(process)d]: %(message)s'.format( self.name ) ) )
      logger.addHandler( handler )
      logger.setLevel( logging.INFO )

    if args.debug:
      logger.setLevel( logging.DEBUG )

    cur_pid = self._read_pid_file()
    if args.action == 'status':
      if cur_pid is None:
        print( 'Stopped' )
        sys.exit( 0 )

      try:
        os.kill( cur_pid, 0 )
      except OSError as e:
        if e.errno == 3:
          print( 'Process PID "{0}" missing'.format( cur_pid ) )
          sys.exit( 0 )
        else:
          print( 'Error checking pid "{0}", errno: {1}'.format( cur_pid, e.errno ) )
          sys.exit( 1 )

      print( 'Running PID "{0}"'.format( cur_pid ) )
      sys.exit( 0 )

    if args.action == 'stop':
      if cur_pid is None:
        print( 'Not running' )
        sys.exit( 0 )

      try:
        os.kill( cur_pid, signal.SIGTERM )
      except OSError as e:
        if e.errno == 3:
          print( 'Process PID "{0}" allready stopped, cleaning up pid file'.format( cur_pid ) )
          self._delete_pid_file()
          sys.exit( 0 )
        else:
          print( 'Error stopping pid "{0}", errno: {1}'.format( cur_pid, e.errno ) )
          sys.exit( 1 )

      print( 'Process PID "{0}" told to stop'.format( cur_pid ) )
      sys.exit( 0 )

    if args.action not in ( 'background', 'foreground' ):
      print( 'daemon: unknown action "{0}"'.format( args.action ) )
      sys.exit( 1 )

    if cur_pid is not None:
      print( 'Process allready running as PID "{0}"'.format( cur_pid ) )
      sys.exit( 1 )

    if args.action == 'background':
      self._daemonize()

    self._write_pid_file()

    signal.signal( signal.SIGINT, self._sigHandlerStop )
    signal.signal( signal.SIGQUIT, self._sigHandlerStop )
    signal.signal( signal.SIGTERM, self._sigHandlerStop )

    logging.debug( 'daemon: loading config from "{0}"...'.format( args.config ) )
    config = configparser.ConfigParser()
    try:
      if not config.read( args.config ):
        logging.error( 'daemon: error reading configfile: "{0}"'.format( args.config ) )
        sys.exit( 1 )
    except Exception as e:
      logging.exception( 'daemon: error parsing configfile: "{0}"'.format( e ) )
      sys.exit( 1 )

    if args.user is not None:
      self._change_user( args.user )

    self.config( config )

    logging.debug( 'daemon: starting main function...' )
    try:
      self.main()
      logging.debug( 'daemon: main completed' )
    except Exception as e:
      logging.exception( 'daemon: Exception "{0}" while executing main'.format( e ) )

    logging.debug( 'daemon: shutting down...' )
    self._delete_pid_file()
    logging.debug( 'daemon: done!' )
    logging.shutdown()

  def _sigHandlerStop( self, sig, frame ):
    logging.info( 'daemon: got stop signal' )
    self.stop()

  def _daemonize( self ):
    logging.debug( 'daemon: damonizing...' )
    logging.debug( 'daemon: first fork...' )
    try:
      pid = os.fork()
      if pid > 0: # we are the parent, let the child go
        sys.exit( 0 )
    except OSError as e:
      logging.exception( 'daemon: exception on first fork, errno: {0}'.format( e.errno ) )
      sys.exit( 1 )

    logging.debug( 'daemon: detaching process...' )

    os.chdir( '/' )
    os.setsid()
    os.umask( 0 )

    logging.debug( 'daemon: second fork...' )
    try:
      pid = os.fork()
      if pid > 0: # we are the parent, let the child go
        sys.exit( 0 )
    except OSError as e:
      logging.exception( 'daemon: exception on second fork, errno: {0}'.format( e.errno ) )
      sys.exit( 1 )

    logging.debug( 'daemon: detaching stdin/out/err...' )
    sys.stdout.flush()
    sys.stderr.flush()
    tmp = open( '/dev/null', 'r' )
    os.dup2( tmp.fileno(), sys.stdin.fileno() )
    tmp = open( '/dev/null', 'a+' )
    os.dup2( tmp.fileno(), sys.stdout.fileno() )
    tmp = open( '/dev/null', 'a+' )
    os.dup2( tmp.fileno(), sys.stderr.fileno() )
    logging.debug( 'daemon: fully daemonized' )

  def _change_user( self, user_name ):
    logging.debug( 'daemon: chaning to user "{0}"...'.format( user_name ) )
    try:
      user_pw = pwd.getpwnam( user_name )
    except KeyError:
      logging.error( 'daemon: user "{0}" not found'.format( user_name ) )
      sys.exit( 1 )

    env = os.environ.copy()
    env[ 'HOME' ] = user_pw.pw_dir
    env[ 'LOGNAME' ] = user_pw.pw_name
    env[ 'USER' ] = user_pw.pw_name

    os.setgid( user_pw.pw_gid )
    os.setuid( user_pw.pw_uid )
    logging.debug( 'daemon: user changed' )

  def _write_pid_file( self ):
    logging.debug( 'daemon: writing pid to "{0}"'.format( self.pid_file ) )
    try:
      open( self.pid_file, 'w' ).write( '{0}\n'.format( os.getpid() ) )
    except OSError as e:
      logging.error( 'daemon: unable to create pid file, errno: {0}'.format( e.errno ) )
      sys.exit( 1 )

  def _read_pid_file( self ):
    logging.debug( 'daemon: reading pid file "{0}"'.format( self.pid_file ) )
    try:
      return int( open( self.pid_file, 'r' ).read().strip() )
    except ValueError:
      logging.error( 'daemon: invalid pid file' )
      return None
    except FileNotFoundError:
      logging.info( 'daemon: pid file not found' )
      return None

  def _delete_pid_file( self ):
    logging.debug( 'daemon: removing pid file "{0}"'.format( self.pid_file ) )
    try:
      os.unlink( self.pid_file )
    except FileNotFoundError:
      pass
