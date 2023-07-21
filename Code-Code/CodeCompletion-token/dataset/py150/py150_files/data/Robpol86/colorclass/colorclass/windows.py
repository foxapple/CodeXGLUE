"""Windows console screen buffer handlers."""

import atexit
import ctypes
import re
import sys

from colorclass.codes import ANSICodeMapping, BASE_CODES
from colorclass.core import RE_SPLIT

IS_WINDOWS = sys.platform == 'win32'
RE_NUMBER_SEARCH = re.compile(r'\033\[([\d;]+)m')
STD_ERROR_HANDLE = -12
STD_OUTPUT_HANDLE = -11
WINDOWS_CODES = {
    '/all': -33, '/fg': -39, '/bg': -49,

    'black': 0, 'red': 4, 'green': 2, 'yellow': 6, 'blue': 1, 'magenta': 5, 'cyan': 3, 'white': 7,

    'bgblack': -8, 'bgred': 64, 'bggreen': 32, 'bgyellow': 96, 'bgblue': 16, 'bgmagenta': 80, 'bgcyan': 48,
    'bgwhite': 112,

    'hiblack': 8, 'hired': 12, 'higreen': 10, 'hiyellow': 14, 'hiblue': 9, 'himagenta': 13, 'hicyan': 11, 'hiwhite': 15,

    'hibgblack': 128, 'hibgred': 192, 'hibggreen': 160, 'hibgyellow': 224, 'hibgblue': 144, 'hibgmagenta': 208,
    'hibgcyan': 176, 'hibgwhite': 240,

    '/black': -39, '/red': -39, '/green': -39, '/yellow': -39, '/blue': -39, '/magenta': -39, '/cyan': -39,
    '/white': -39, '/hiblack': -39, '/hired': -39, '/higreen': -39, '/hiyellow': -39, '/hiblue': -39, '/himagenta': -39,
    '/hicyan': -39, '/hiwhite': -39,

    '/bgblack': -49, '/bgred': -49, '/bggreen': -49, '/bgyellow': -49, '/bgblue': -49, '/bgmagenta': -49,
    '/bgcyan': -49, '/bgwhite': -49, '/hibgblack': -49, '/hibgred': -49, '/hibggreen': -49, '/hibgyellow': -49,
    '/hibgblue': -49, '/hibgmagenta': -49, '/hibgcyan': -49, '/hibgwhite': -49,
}


class COORD(ctypes.Structure):
    """COORD structure. http://msdn.microsoft.com/en-us/library/windows/desktop/ms682119."""

    _fields_ = [
        ('X', ctypes.c_short),
        ('Y', ctypes.c_short),
    ]


class SmallRECT(ctypes.Structure):
    """SMALL_RECT structure. http://msdn.microsoft.com/en-us/library/windows/desktop/ms686311."""

    _fields_ = [
        ('Left', ctypes.c_short),
        ('Top', ctypes.c_short),
        ('Right', ctypes.c_short),
        ('Bottom', ctypes.c_short),
    ]


class ConsoleScreenBufferInfo(ctypes.Structure):
    """CONSOLE_SCREEN_BUFFER_INFO structure. http://msdn.microsoft.com/en-us/library/windows/desktop/ms682093."""

    _fields_ = [
        ('dwSize', COORD),
        ('dwCursorPosition', COORD),
        ('wAttributes', ctypes.c_ushort),
        ('srWindow', SmallRECT),
        ('dwMaximumWindowSize', COORD)
    ]


def init_kernel32():
    """Load a unique instance of WinDLL into memory, set arg/return types, and get stdout/err handles.

    :raise AttributeError: When called on a non-Windows platform.

    1. Since we are setting DLL function argument types and return types, we need to maintain our own instance of
       kernel32 to prevent overriding (or being overwritten by) user's own changes to ctypes.windll.kernel32.
    2. While we're doing all this we might as well get the handles to STDOUT and STDERR streams.

    :return: Loaded kernel32 instance, stderr handle (int), and stdout handle (int).
    :rtype: tuple
    """
    kernel32 = ctypes.LibraryLoader(ctypes.WinDLL).kernel32  # Load our own instance. Unique memory address.

    # Setup GetStdHandle.
    kernel32.GetStdHandle.argtypes = [ctypes.c_ulong]
    kernel32.GetStdHandle.restype = ctypes.c_void_p

    # Setup GetConsoleScreenBufferInfo.
    kernel32.GetConsoleScreenBufferInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ConsoleScreenBufferInfo),
    ]
    kernel32.GetConsoleScreenBufferInfo.restype = ctypes.c_long

    # Get handles.
    stderr = kernel32.GetStdHandle(STD_ERROR_HANDLE)
    stdout = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    return kernel32, stderr, stdout


def get_console_info(kernel32, handle):
    """Get information about this current console window.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683231
    https://code.google.com/p/colorama/issues/detail?id=47
    https://bitbucket.org/pytest-dev/py/src/4617fe46/py/_io/terminalwriter.py

    :param ctypes.windll.kernel32 kernel32: Loaded kernel32 instance.
    :param int handle: stderr or stdout handle.

    :return: Foreground and background colors (integers).
    :rtype: tuple
    """
    # Query Win32 API.
    csbi = ConsoleScreenBufferInfo()  # Populated by GetConsoleScreenBufferInfo.
    try:
        if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi)):
            raise IOError('Unable to get console screen buffer info from win32 API.')
    except ctypes.ArgumentError:
        raise IOError('Unable to get console screen buffer info from win32 API.')

    # Parse data.
    # buffer_width = int(csbi.dwSize.X - 1)
    # buffer_height = int(csbi.dwSize.Y)
    # terminal_width = int(csbi.srWindow.Right - csbi.srWindow.Left)
    # terminal_height = int(csbi.srWindow.Bottom - csbi.srWindow.Top)
    fg_color = csbi.wAttributes % 16
    bg_color = csbi.wAttributes & 240

    return fg_color, bg_color


class WindowsStream(object):
    """Replacement stream which overrides sys.stdout or sys.stderr. When writing or printing, ANSI codes are converted.

    ANSI (Linux/Unix) color codes are converted into win32 system calls, changing the next character's color before
    printing it. Resources referenced:
        https://github.com/tartley/colorama
        http://www.cplusplus.com/articles/2ywTURfi/
        http://thomasfischer.biz/python-and-windows-terminal-colors/
        http://stackoverflow.com/questions/17125440/c-win32-console-color
        http://www.tysos.org/svn/trunk/mono/corlib/System/WindowsConsoleDriver.cs
        http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
        http://msdn.microsoft.com/en-us/library/windows/desktop/ms682088#_win32_character_attributes

    :cvar list ALL_BG_CODES: List of bg Windows codes. Used to determine if requested color is foreground or background.
    :cvar dict COMPILED_CODES: Translation dict. Keys are ANSI codes (values of BASE_CODES), values are Windows codes.
    :ivar int default_fg: Foreground Windows color code at the time of instantiation.
    :ivar int default_bg: Background Windows color code at the time of instantiation.
    """

    ALL_BG_CODES = [v for k, v in WINDOWS_CODES.items() if k.startswith('bg') or k.startswith('hibg')]
    COMPILED_CODES = dict((v, WINDOWS_CODES[k]) for k, v in BASE_CODES.items() if k in WINDOWS_CODES)

    def __init__(self, kernel32, stream_handle, original_stream):
        """Constructor.

        :param ctypes.windll.kernel32 kernel32: Loaded kernel32 instance.
        :param int stream_handle: stderr or stdout handle.
        :param original_stream: sys.stderr or sys.stdout before being overridden by this class' instance.
        """
        self._kernel32 = kernel32
        self._stream_handle = stream_handle
        self._original_stream = original_stream
        self.default_fg, self.default_bg = self.colors
        for attr in dir(original_stream):
            if hasattr(self, attr):
                continue
            setattr(self, attr, getattr(original_stream, attr))

    def __getattr__(self, item):
        """If an attribute/function/etc is not defined in this function, retrieve the one from the original stream.

        Fixes ipython arrow key presses.
        """
        return getattr(self._original_stream, item)

    @property
    def colors(self):
        """Return the current foreground and background colors."""
        try:
            return get_console_info(self._kernel32, self._stream_handle)
        except IOError:
            return WINDOWS_CODES['white'], WINDOWS_CODES['black']

    @colors.setter
    def colors(self, color_code):
        """Change the foreground and background colors for subsequently printed characters.

        None resets colors to their original values (when class was instantiated).

        Since setting a color requires including both foreground and background codes (merged), setting just the
        foreground color resets the background color to black, and vice versa.

        This function first gets the current background and foreground colors, merges in the requested color code, and
        sets the result.

        However if we need to remove just the foreground color but leave the background color the same (or vice versa)
        such as when {/red} is used, we must merge the default foreground color with the current background color. This
        is the reason for those negative values.

        :param int color_code: Color code from WINDOWS_CODES.
        """
        if color_code is None:
            color_code = WINDOWS_CODES['/all']

        # Get current color code.
        current_fg, current_bg = self.colors

        # Handle special negative codes. Also determine the final color code.
        if color_code == WINDOWS_CODES['/fg']:
            final_color_code = self.default_fg | current_bg  # Reset the foreground only.
        elif color_code == WINDOWS_CODES['/bg']:
            final_color_code = current_fg | self.default_bg  # Reset the background only.
        elif color_code == WINDOWS_CODES['/all']:
            final_color_code = self.default_fg | self.default_bg  # Reset both.
        elif color_code == WINDOWS_CODES['bgblack']:
            final_color_code = current_fg  # Black background.
        else:
            new_is_bg = color_code in self.ALL_BG_CODES
            final_color_code = color_code | (current_fg if new_is_bg else current_bg)

        # Set new code.
        self._kernel32.SetConsoleTextAttribute(self._stream_handle, final_color_code)

    def write(self, p_str):
        """Write to stream.

        :param str p_str: string to print.
        """
        for segment in RE_SPLIT.split(p_str):
            if not segment:
                # Empty string. p_str probably starts with colors so the first item is always ''.
                continue
            if not RE_SPLIT.match(segment):
                # No color codes, print regular text.
                self._original_stream.write(segment)
                self._original_stream.flush()
                continue
            for color_code in (int(c) for c in RE_NUMBER_SEARCH.findall(segment)[0].split(';')):
                if color_code in self.COMPILED_CODES:
                    self.colors = self.COMPILED_CODES[color_code]


class Windows(object):
    """Enable and disable Windows support for ANSI color character codes.

    Call static method Windows.enable() to enable color support for the remainder of the process' lifetime.

    This class is also a context manager. You can do this:
    with Windows():
        print(Color('{autored}Test{/autored}'))

    Or this:
    with Windows(auto_colors=True):
        print(Color('{autored}Test{/autored}'))
    """

    @classmethod
    def disable(cls):
        """Restore sys.stderr and sys.stdout to their original objects. Resets colors to their original values.

        :return: If streams restored successfully.
        :rtype: bool
        """
        # Skip if not on Windows or not enabled.
        if not IS_WINDOWS or not cls.is_enabled():
            return False

        # Restore default colors.
        if hasattr(sys.stderr, 'color'):
            getattr(sys, 'stderr').color = None
        if hasattr(sys.stdout, 'color'):
            getattr(sys, 'stdout').color = None

        # Restore original streams.
        if hasattr(sys.stderr, '_original_stream'):
            sys.stderr = getattr(sys.stderr, '_original_stream')
        if hasattr(sys.stdout, '_original_stream'):
            sys.stdout = getattr(sys.stdout, '_original_stream')

        return True

    @staticmethod
    def is_enabled():
        """Return True if either stderr or stdout has colors enabled."""
        return hasattr(sys.stderr, '_original_stream') or hasattr(sys.stdout, '_original_stream')

    @classmethod
    def enable(cls, auto_colors=False, reset_atexit=False):
        """Enable color text with print() or sys.stdout.write() (stderr too).

        :param bool auto_colors: Automatically selects dark or light colors based on current terminal's background
            color. Only works with {autored} and related tags.
        :param bool reset_atexit: Resets original colors upon Python exit (in case you forget to reset it yourself with
            a closing tag).

        :return: If streams replaced successfully.
        :rtype: bool
        """
        if not IS_WINDOWS:
            return False  # Windows only.
        if hasattr(sys.stderr, '_original_stream') and hasattr(sys.stdout, '_original_stream'):
            return False  # Nothing to do.

        # Overwrite stream references.
        kernel32, stderr, stdout = init_kernel32()
        if not hasattr(sys.stderr, '_original_stream'):
            sys.stderr.flush()
            sys.stderr = WindowsStream(kernel32, stderr, sys.stderr)
        if not hasattr(sys.stdout, '_original_stream'):
            sys.stdout.flush()
            sys.stdout = WindowsStream(kernel32, stdout, sys.stdout)
        if not hasattr(sys.stderr, '_original_stream') and not hasattr(sys.stdout, '_original_stream'):
            return False  # Something failed.

        # Automatically select which colors to display.
        bg_color = getattr(sys.stdout, 'default_bg', getattr(sys.stderr, 'default_bg', None))
        if auto_colors and bg_color is not None:
            if bg_color in (112, 96, 240, 176, 224, 208, 160):
                ANSICodeMapping.set_light_background()
            else:
                ANSICodeMapping.set_dark_background()

        # Reset on exit if requested.
        if reset_atexit:
            atexit.register(cls.disable)

        return True

    def __init__(self, auto_colors=False):
        """Constructor."""
        self.auto_colors = auto_colors

    def __enter__(self):
        """Context manager, enables colors on Windows."""
        self.enable(auto_colors=self.auto_colors)

    def __exit__(self, *_):
        """Context manager, disabled colors on Windows."""
        self.disable()
