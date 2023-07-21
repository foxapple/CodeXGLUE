import inspect
import logging
import logging.handlers
import os


#-------------------------------------------------------------------------------
# Level related stuff
#-------------------------------------------------------------------------------
#
# Provides a local method of overriding logging levels without having to import
# the real logging module. Prompts are set for each level, allowing for specific
# information to be prepended to output at a particular level.
#

NOTSET   = logging.NOTSET
VERBOSE  = 5
DEBUG    = logging.DEBUG
INFO     = logging.INFO
WARNING  = logging.WARNING
WARN     = WARNING
ERROR    = logging.ERROR
CRITICAL = logging.CRITICAL
FATAL    = CRITICAL

LEVEL_NAMES = {
    CRITICAL   : 'CRITICAL',
    ERROR      : 'ERROR',
    WARNING    : 'WARNING',
    INFO       : 'INFO',
    DEBUG      : 'DEBUG',
    VERBOSE    : 'VERBOSE',
    NOTSET     : 'NOTSET',
    'CRITICAL' : CRITICAL,
    'ERROR'    : ERROR,
    'WARN'     : WARNING,
    'WARNING'  : WARNING,
    'INFO'     : INFO,
    'DEBUG'    : DEBUG,
    'VERBOSE'  : VERBOSE,
    'NOTSET'   : NOTSET,
}

DEFAULT_PROMPTS = {
    VERBOSE  : "{level}: ".format(level=LEVEL_NAMES[VERBOSE]),
    DEBUG    : "{level}: ".format(level=LEVEL_NAMES[DEBUG]),
    INFO     : "{level}: ".format(level=LEVEL_NAMES[INFO]),
    WARNING  : "{level}: ".format(level=LEVEL_NAMES[WARNING]),
    ERROR    : "{level}: ".format(level=LEVEL_NAMES[ERROR]),
    CRITICAL : "{level}: ".format(level=LEVEL_NAMES[CRITICAL]),
}

ELEVATED_PATH = '/var/log/management/'
LOCAL_PATH    = '~/Library/Logs/Management/'

class Logger(logging.Logger):
    """
    This class replaces the regular logging methods (info, error, etc.) with
    methods that can both output information to the console as well as write to
    the logs.
    """
    def __init__(self, name, level=INFO, print_default=True, log_default=True):
        """
        Set up the logger. Generally this will be created from some command
        line arguments.
        
        :param name: the name of the logger
        :type  name: str
        :param level: the level at which to log output
        :type  level: int
        """
        
        # Call the super constructor to build the actual logger.
        super(Logger, self).__init__(name=name, level=level)
        
        # Set the default level names and prompts for this logger.
        self.level_names = LEVEL_NAMES.copy()
        self.prompts     = DEFAULT_PROMPTS.copy()
        
        # Set the default for printing and logging.
        self.print_default = print_default
        self.log_default   = log_default
    
    def add_level_name(self, level, level_name):
        """
        Allows for custom level names to be used. This is used in logging
        output.
        
        :param level: The numeric value of the level.
        :param level_name: The name for that level of logging.
        """
        self.level_names[level]      = level_name
        self.level_names[level_name] = level
        
        logging.addLevelName(level, level_name)

    def set_prompt(self, level, prompt):
        """
        Set a new default prompt. Useful for outputting custom information with
        custom logging levels.
        
        :param level: The level for the prompt to display at.
        :param prompt: The prompt to display.
        """
        self.prompts[level] = prompt
        
    def verbose(self, message, print_out=None, log=None):
        """
        Log 'message' as verbose output.
        
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= VERBOSE:
            print("{prompt}{message}".format(prompt=self.prompts[VERBOSE], message=message))
        if log:
            super(Logger, self).debug(message)
    
    def debug(self, message, print_out=None, log=None):
        """
        Log 'message' as debugging output.
        
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= DEBUG:
            print("{prompt}{message}".format(prompt=self.prompts[DEBUG], message=message))
        if log:
            super(Logger, self).debug(message)
    
    def info(self, message, print_out=None, log=None):
        """
        Log 'message' as general information.
        
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= INFO:
            print("{prompt}{message}".format(prompt=self.prompts[INFO], message=message))
        if log:
            super(Logger, self).info(message)
    
    def warning(self, message, print_out=None, log=None):
        """
        Log 'message' as a warning (not enough to halt execution, but enough to
        be notable).
        
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= WARNING:
            print("{prompt}{message}".format(prompt=self.prompts[WARNING], message=message))
        if log:
            super(Logger, self).warning(message)
        
    warn = warning
        
    def error(self, message, print_out=None, log=None):
        """
        Log 'message' as an error.
        
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= ERROR:
            print("{prompt}{message}".format(prompt=self.prompts[ERROR], message=message))
        if log:
            super(Logger, self).error(message)
    
    def critical(self, message, print_out=None, log=None):
        """
        Log 'message' as a critical failure. This should probably halt
        execution more often than not.
        
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= CRITICAL:
            print("{prompt}{message}".format(prompt=self.prompts[CRITICAL], message=message))
        if log:
            super(Logger, self).critical(message)
    
    fatal = critical
    
    def log(self, level, message, print_out=None, log=None):
        """
        Log 'message' with a custom logging level.
        
        :param level: The verbosity level to log at.
        :param message: Information to display.
        :param print_out: Whether to print to stdout.
        :param log: Whether to commit this to the logger.
        """
        # Set default values.
        if print_out is None:
            print_out = self.print_default
        if log is None:
            log = self.log_default
        
        # Do the logging depending on settings.
        if print_out and self.level <= level:
            prompt = self.prompts.get(level, 'Level {}: '.format(level))
            print("{prompt}{message}".format(prompt=prompt, message=message))
        if log:
            super(Logger, self).log(level, message)
        
class FileLogger(Logger):
    """
    A rotating file logger. This will write to a file up until the file contains
    10MB of data. At that point the file will get ".1" appended to its name, and
    a new file will be created in its place. This will keep up to five backup
    files aside from the main file to which output is logged.
    
    The default destination is:
        ELEVATED_PATH/<name>.log
    But if the current user does not have write permissions within that
    directory, instead the destination will be:
        LOCAL_PATH/<name>.log
    
    The default logging severity level is INFO.
    """
    def __init__(self, name=None, level=INFO, path=None, print_default=True, log_default=True, log_size=10485760, backup_count=5):
        """
        Create the rotating file logger. By default, the name will be set based
        on the inspection stack; the level will be set to INFO; and the path
        will be set to the class defaults.
        
        :param name: The name of the logger (e.g. "myprogram").
        :param level: The logging level for output.
        :param path: The directory to put the log file inside.
        :param print_default: Whether to default to outputting logging
                              information to stdout.
        :Param log_default: Whether to default to commiting logging information
                            to the log file.
        """
        # Did they specify a path?
        if path:
            # Make sure that the path ends with a slash. (It should point to a
            # directory, not a file).
            if not path.endswith('/'):
                path += '/'
        else:
            # See if we have privileges to write to the root log file and set
            # the destination accordingly.
            if os.access(os.path.dirname(ELEVATED_PATH[:-1]), os.W_OK):
                path = ELEVATED_PATH
            else:
                path = os.path.expanduser(LOCAL_PATH)
        
        # There needs to be a name. If none is provided, pull it from the
        # inspection stack. (It might not be pretty.)
        if not name:
            name = inspect.stack()[1][3]
        
        # Form the destination. All destinations will end in '.log'.
        destination = os.path.join(path, name)
        if not destination.endswith('.log'):
            destination += '.log'
        
        # Ensure that the necessary directories exist for creating the log file.
        if not os.path.exists(os.path.dirname(destination)):
            try:
                os.makedirs(os.path.dirname(destination))
            except OSError:
                raise ValueError("Invalid path specified: could not create'{}'".format(str(os.path.dirname(destination))))
        
        # Call the super constructor.
        super(FileLogger, self).__init__(name=name, level=level, print_default=print_default, log_default=log_default)
        
        # Save the path (just in case).
        self.path = path
        
        # Set up the formatting and handling for this file logger.
        # This will be a rotating file logger, with up to five backup files each
        # weighing up to 10MB. Each line is prefaced with the timestamp, the
        # logging level, and the message. So
        #   logger.info("This is some test output!")
        # would produce a line as:
        #   2015-02-05 17:29:48,289 INFO: This is some test output!
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        handler   = logging.handlers.RotatingFileHandler(destination, maxBytes=log_size, backupCount=backup_count)
        handler.setFormatter(formatter)
        
        self.addHandler(handler)

class StreamLogger(Logger):
    """
    A simple console-output logger. This will not write to a file, but instead
    will output everything to the console.
    
    The default logging severity level is DEBUG.
    """
    def __init__(self, name=None, level=DEBUG, print_default=False, log_default=True):
        """
        Build the stream logger as specified. The default logging level is set
        at DEBUG.
        
        :param level: the level at which to cut off logging
        :type  level: int
        """
        
        # Since this type of logger is only used for console output, the name
        # defaults to whatever method called the logger.
        if not name:
            name = inspect.stack()[1][3]
        
        # Call the super constructor.
        super(StreamLogger, self).__init__(name=name, level=level, print_default=print_default, log_default=log_default)
        
        # Set up the formatting and handling for this logger. Each line is
        # prefaced with the timestamp, the logging level, and the message. So
        #   logger.info("This is some test output!")
        # would produce a line as:
        #   2015-02-05 17:29:48,289 INFO: This is some test output!
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        handler   = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        self.addHandler(handler)

def get_logger(name=None, log=False, level=INFO, path=None):
    """
    Returns the appropriate logger depending on the passed-in arguments.
    
    This is particularly useful in conjunction with command-line arguments when
    you won't know for sure what kind of logger the program will need.
    
    :param name: The name of the file to log into.
    :param log: Whether to actually commit information to a file.
    :param level: The verbosity level. Only events logged at or above this level
                  will be displayed.
    :param path: The folder to put the log file into.
    """
    # Are we writing the output to disk? Pick the type of logger based on that.
    if log:
        return FileLogger(name=name, level=level, path=path)
    else:
        return StreamLogger(name=name, level=level)

def file_logger(name=None, level=INFO, path=None):
    """
    Provides backwards compatibility with previous versions of Management Tools
    (i.e. version < 1.6.0).
    
    :param name: The name of the file to log into.
    :param level: The verbosity level. Only events logged at or above this level
                  will be displayed.
    :param path: The folder to put the log file into.
    """
    return FileLogger(name=name, level=level, path=path)

def stream_logger(level=DEBUG):
    """
    Provides backwards compatibility with previous versions of Management Tools
    (i.e. version < 1.6.0).
    
    :param level: The verbosity level. Only events logged at or above this level
                  will be displayed.
    """
    return StreamLogger(name=None, level=level)
