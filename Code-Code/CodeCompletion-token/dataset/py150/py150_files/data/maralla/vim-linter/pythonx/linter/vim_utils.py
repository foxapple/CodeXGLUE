# -*- coding: utf-8 -*-

from __future__ import absolute_import

import vim


def get_val(key):
    return vim.eval("g:{}".format(key))


def get_current_bufnr():
    return vim.current.buffer.number


def get_filetype():
    ft = vim.eval("&filetype")
    if not ft:
        vim.command("silent! filetype detect")
        ft = vim.eval("&filetype")
    return ft


def get_fpath():
    return vim.eval("expand('%:p')")


def cursor_jump(line, col):
    vim.command("call cursor({}, {})".format(line, col))


def place_sign(sign_id, line, name, bufnr):
    if line < 1:
        line = 1

    p_fmt = ('try | '
             'exec "sign place {} line={} name={} buffer={}" | '
             'catch | '
             'endtry')
    vim.command(p_fmt.format(sign_id, line, name, bufnr))


def unplace_sign(sign_id, bufnr):
    unplace_fmt = ('try | '
                   'exec "sign unplace {} buffer={}" | '
                   'catch /E158/ | '
                   'endtry')
    vim.command(unplace_fmt.format(sign_id, bufnr))


def save(filename):
    vim.command("call writefile(getline(1, '$'), '{}')".format(filename))
