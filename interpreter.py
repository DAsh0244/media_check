#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
vlc_check_audio
interpreter.py
Author: Danyal Ahsanullah
Date: 7/30/2017
Copyright (c):  2017 Danyal Ahsanullah
License: N/A
Description: 
"""
from cmd import Cmd as _Cmd
import os as _os


class HideNoneDocInterpreter(_Cmd):
    """
    shell that hides sections of help depending on if their corresponding header is None
    """
    def __init__(self, *args, **kwargs):
        super(HideNoneDocInterpreter, self).__init__(*args, **kwargs)

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if header is not None:
            super(HideNoneDocInterpreter, self).print_topics(header, cmds, cmdlen, maxcol)


class HideUndocumentedInterpreter(HideNoneDocInterpreter):
    """
    interpreter that hides undocumented commands from being displayed
    in the help messages.
    """
    undoc_header = None

    def __init__(self, *args, **kwargs):
        super(HideUndocumentedInterpreter, self).__init__(*args, **kwargs)


class ShellCmdInterpreter(_Cmd):
    """
    cmd shell mix-in that provides shell access
    """
    def __init__(self, *args, **kwargs):
        super(ShellCmdInterpreter, self).__init__(*args, *kwargs)

    def do_shell(self, s):
        """execute shell commands"""
        _os.system(s)



def make_alias(alias, method, args):
    pass


class AliasedInterpreter(_Cmd):
    """
    interpreter that allows aliasing or commands using the alias_prefix
    """
    ALIAS_PREFIX = 'alias_'

    def __init__(self, *args, **kwargs):
        self.aliases = self.get_aliases()
        super(AliasedInterpreter, self).__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def completedefault(self, text, line, begidx, endidx):
        return [i[3:] for i in self.get_names() if i not in self.aliases and i.startswith('do_') and 'EOF' not in i]

    def completenames(self, text, *ignored):
        return [a[3:] for a in self.get_names() if
                (a.startswith('do_' + text) and getattr(self, a).__doc__ is not None)]

    def get_aliases(self):
        return {i[6:] for i in self.get_names() if i.startswith(self.ALIAS_PREFIX)}

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        func = [getattr(self, n) for n in self.get_names() if
                (n.startswith('do_' + cmd)) or (n.startswith(self.ALIAS_PREFIX + cmd))]
        if func:  # maybe check if exactly one or more elements, and tell the user
            return func[0](arg)
        else:
            super(AliasedInterpreter, self).default(line)
            return None

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx>0:
                cmd, args, foo = self.parseline(line)
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        try:
                            compfunc = getattr(self, 'complete_' + getattr(self, 'alias_' + cmd).__name__[3:])
                        except AttributeError:
                            compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None


class AliasCmdInterpreter(AliasedInterpreter):
    """
    AliasedShell with generally implemented command 'alias' that lists all aliases.
    'alias' has also been mapped to 'a'
    """
    def __init__(self, *args, **kwargs):
        super(AliasCmdInterpreter, self).__init__(*args, **kwargs)

    def do_alias(self, *args, supress=False):
        """
        print aliases and their corresponding commands

        Usage:
        alias

        Options:
        []
        """
        alias_str = ''.join('{}: {}\n'.format(alias, getattr(self, 'alias_' + alias).__name__[3:])
                            for alias in self.aliases)
        if not supress:
            self.stdout.write(alias_str)
        else:
            return alias_str

    # aliased cmds
    alias_a = do_alias