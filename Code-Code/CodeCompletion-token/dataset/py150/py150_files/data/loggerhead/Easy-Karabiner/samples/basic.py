DEFINITIONS = {
    '{{EMACS_IGNORE_APP}}': ('X11', 'GOOGLE_CHROME'),
}

REMAPS = [
    ['ctrl B', 'left'   , ['!{{EMACS_IGNORE_APP}}']],
    ['ctrl B', 'left'   , ['!{{EMACS_IGNORE_APP}}']],
    ['cmd  D', 'cmd_r D', ['VIRTUALMACHINE', 'X11']],
    ['(double)' , 'fn' , 'f12'],
    ['(double)' , 'fn' , 'cmd alt I'                 , ['GOOGLE_CHROME']],
    ['(holding)', 'esc', 'cmd_r ctrl_r alt_r shift_r', ['GOOGLE_CHROME']],
]
