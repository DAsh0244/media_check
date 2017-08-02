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
    Interpreters to use for the purposes of building shells.
    Built off of the "Cmd"  class from the builtin module "cmd"
"""
import os as _os
from cmd import Cmd as _Cmd
import _utils


# misc functions / decorators
# def make_alias(alias, method, args):
#     pass


# base level interpreters / mix-ins
# all of these classes inherit from the base Cmd class.
# they are designed to be compatible with each other
# for multiple inheritance use cases.


class ShellCmdMix(_Cmd):
    """
    cmd shell mix-in that provides shell access
    """

    def __init__(self, *args, **kwargs):
        super(ShellCmdMix, self).__init__(*args, *kwargs)

    @staticmethod
    def do_shell(s):
        """execute shell commands"""
        _os.system(s)


class HideNoneDocMix(_Cmd):
    """
    shell that hides sections of help depending on if their corresponding header is None
    """

    def __init__(self, *args, **kwargs):
        super(HideNoneDocMix, self).__init__(*args, **kwargs)

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if header is not None:
            super(HideNoneDocMix, self).print_topics(header, cmds, cmdlen, maxcol)


class AliasMix(_Cmd):
    """
    interpreter that allows aliasing or commands using the alias_prefix
    """
    ALIAS_PREFIX = 'alias_'

    def __init__(self, *args, **kwargs):
        self.aliases = self.get_aliases()
        super(AliasMix, self).__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def completedefault(self, text, line, begidx, endidx):
        return [i[3:] for i in self.get_names() if i not in self.aliases and i.startswith('do_') and 'EOF' not in i]

    def completenames(self, text, *ignored):
        return [a[3:] for a in self.get_names() if
                (a.startswith('do_' + text) and getattr(self, a).__doc__ is not None)]

    def get_names(self):
        return dir(self)

    def get_aliases(self):
        return {i[6:] for i in self.get_names() if i.startswith(self.ALIAS_PREFIX)}

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        func = [getattr(self, n) for n in self.get_names() if
                (n == 'do_' + cmd) or (n == self.ALIAS_PREFIX + cmd)]
        if func:  # maybe check if exactly one or more elements, and tell the user
            return func[0](arg)
        else:
            super(AliasMix, self).default(line)
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
            if begidx > 0:
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
            # noinspection PyAttributeOutsideInit
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None


class TimeoutInputMix(_Cmd):
    """
    mixin for timeout supported input methods
    """

    def __init__(self, timeout=None, *args, **kwargs):
        super(TimeoutInputMix, self).__init__(*args, **kwargs)
        self.timeout = timeout

    def cmdloop(self, timeout=None, intro=None, timeout_msg=''):
        """
        modified cmdloop method of the Cmd class supporting input with timeouts.
        """
        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                # noinspection PyUnresolvedReferences
                import readline
                # noinspection PyAttributeOutsideInit
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            try:
                                if timeout is not None:
                                    tout = timeout
                                elif self.timeout:
                                    tout = self.timeout

                                get_input = lambda prompt: _utils.input_timeout(caption=prompt, timeout=tout,
                                                                                stream=self.stdout,
                                                                                timeout_msg=timeout_msg)
                            except:
                                get_input = lambda prompt: input(prompt)
                            line = get_input(self.prompt)
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    # noinspection PyUnresolvedReferences
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass


# more specialized interpreters for ease of use.
# not guaranteed to be fully compatible for mixing purposes.
class AliasCmdInterpreter(AliasMix):
    """
    AliasedShell with generally implemented command 'alias' that lists all aliases.
    'alias' has also been mapped to 'a'
    """

    def __init__(self, *args, **kwargs):
        super(AliasCmdInterpreter, self).__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def do_alias(self, *args, supress=False):
        """
        print aliases and their corresponding commands

        Usage:
        alias

        Options:
        []
        """
        if args[0] != '':
            args = args[0].split(' ')
            cmd = None
            try:
                cmd = getattr(self, 'do_{}'.format(args[1]))
            except (AttributeError, IndexError):
                try:
                    cmd = getattr(self, '{}{}'.format(self.ALIAS_PREFIX, args[1]))
                except (AttributeError, IndexError):
                    pass
            if cmd is not None:
                setattr(self, '{}{}'.format(self.ALIAS_PREFIX, args[0]), cmd)
                self.aliases = self.get_aliases()
            else:
                self.stdout.write('failed to create alias.\n')
                self.stdout.flush()

        else:
            alias_str = ''.join('{}: {}\n'.format(alias, getattr(self, 'alias_' + alias).__name__[3:])
                                for alias in self.aliases)
            if not supress:
                self.stdout.write(alias_str)
            else:
                return alias_str

    # aliased cmds
    alias_a = do_alias


if __name__ == '__main__':
    import sys

    sys.exit(0)
