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
# import rlcompleter
from cmd import Cmd as _Cmd

from vlc_analyze import utils


# misc functions / decorators
# None Here

# base level interpreters / mix-ins
# all of these classes inherit from the base Cmd class.
# they are designed to be compatible with each other
# for multiple inheritance use cases.


class CacheCompleteMix(_Cmd):
    """
    cmd shell mix-in that provides caching for tab completion
    """

    def __init__(self, *args, **kwargs):
        self.__cache = dict()
        self.completion_source = lambda *args: []
        super(CacheCompleteMix, self).__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def completedefault(self, text, line, begidx, endidx):
        return [i[3:] for i in self.get_names() if i.startswith('do_') and 'EOF' not in i]

    def completenames(self, text, *ignored):
        return [a[3:] for a in self.get_names() if
                (a.startswith('do_' + text) and getattr(self, a).__doc__ is not None)]

    def _cache_completion(self, key, text, line, begidx, endidx):
        try:
            # print('using cached names')
            return [i for i in {opt for opt in self.__cache[key]} if i.startswith(text) and i not in line]
        except KeyError:
            # print('fetching names')
            self.__cache[key] = self.completion_source(key)
            return [i for i in {opt for opt in self.__cache[key]} if i.startswith(text) and i not in line]


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
    SHOW_ALIAS = False

    def _wrap_alias(self, alias):
        return '{}{}'.format(self.ALIAS_PREFIX, alias)

    def __init__(self, *args, **kwargs):
        self.aliases = self.get_aliases()
        super(AliasMix, self).__init__(*args, **kwargs)

    # noinspection PyUnusedLocal
    def completedefault(self, text, line, begidx, endidx):
        return [i[3:] for i in self.get_names() if i.startswith('do_') and 'EOF' not in i]

    def completenames(self, text, *ignored):
        names = self.get_names()
        # noinspection SpellCheckingInspection
        cmds = [a[3:] for a in names if
                a.startswith('do_' + text) and getattr(self, a).__doc__ is not None]
        if self.SHOW_ALIAS:
            aliases = [a[6:] for a in names if
                       a.startswith(self.ALIAS_PREFIX + text) and getattr(self, a).__doc__ is not None]
        else:
            aliases = []
        return cmds + aliases

    def get_names(self):
        return dir(self)

    def get_aliases(self):
        return {i[6:] for i in self.get_names() if i.startswith(self.ALIAS_PREFIX)}

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        func = [getattr(self, n, None) for n in self.get_names() if
                (n == 'do_' + cmd) or (n == self._wrap_alias(cmd))]
        if func:  # maybe check if exactly one or more elements, and tell the user
            return func[0](arg)
        else:
            super(AliasMix, self).default(line)
            return None

    # noinspection SpellCheckingInspection
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
                            compfunc = getattr(self, 'complete_' + getattr(self, self._wrap_alias(cmd)).__name__[3:])
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

    # noinspection SpellCheckingInspection,PyShadowingBuiltins
    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n" % utils.trim_docstring(str(doc)))
                        return
                except AttributeError:
                    try:
                        doc = getattr(self, self._wrap_alias(arg)).__doc__
                        if doc:
                            self.stdout.write("%s\n" % utils.trim_docstring(str(doc)))
                            return
                    except AttributeError:
                        pass
                self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]] = 1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd = name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics(self.doc_header, cmds_doc, 15, 80)
            self.print_topics(self.misc_header, list(help.keys()), 15, 80)
            self.print_topics(self.undoc_header, cmds_undoc, 15, 80)

class TimeoutInputMix(_Cmd):
    """
    mixin for timeout supported input methods
    """

    def __init__(self, timeout=None, *args, **kwargs):
        super(TimeoutInputMix, self).__init__(*args, **kwargs)
        self.timeout = timeout
        # self.completer = rlcompleter.Completer(self.__dict__)

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
                                    get_input = lambda prompt: utils.input_timeout(caption=prompt, timeout=tout,
                                                                                   stream=self.stdout,
                                                                                   timeout_msg=timeout_msg,
                                                                                   completer=self.complete)
                            except NameError:
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
    AliasedShell with generally implemented command 'alias' that lists all aliases
    and can be used to create new ones on the fly.
    By default, 'alias' has also been mapped to 'a', this can be changed with the
    enable_alias and force_alias keyword arguments.

    enable_alias controls weather to try aliasing 'a' as an alias for the 'alias' command.
    force_alias controls weather to force (and potentially overwrite) 'a' as an alias for the 'alias' command.
        NOTE: forcing alias WILL delete whatever command/alias you had previously setup.
    """

    def __init__(self, enable_alias=True, force_alias=False, *args, **kwargs):
        super(AliasCmdInterpreter, self).__init__(*args, **kwargs)
        if enable_alias:
            self.__default_alias(force_alias)

    # noinspection PyPep8Naming,PyUnusedLocal
    @staticmethod
    def do_EOF(*args):
        return True

    # noinspection PyUnusedLocal
    def do_alias(self, *args, suppress=False):
        """
        Set/clear aliases.
        If no options are provided, print aliases and their corresponding commands.

        Usage:
          alias [alias] [command]

        Options:
          [alias]: alias to create
          [command]: command to map [alias] to.
                     If blank it will clear the alias for [alias]
        """
        if args[0] != '':
            args = args[0].split(' ')
            cmd = None
            try:
                cmd = getattr(self, 'do_{}'.format(args[1]))
            except (AttributeError, IndexError):
                try:
                    cmd = getattr(self, self._wrap_alias(args[1]))
                except (AttributeError, IndexError):
                    pass
            new_alias = self._wrap_alias(args[0])
            if cmd is not None:
                try:
                    setattr(self, new_alias, cmd)
                    self.aliases = self.get_aliases()
                except Exception as e:
                    self.stdout.write('failed to create alias.\n{}\n'.format(e))
                    self.stdout.flush()
            else:  # delete alias
                try:
                    delattr(self, new_alias)
                    self.aliases = self.get_aliases()
                except AttributeError:
                    pass
        else:
            alias_str = ''.join('{}: {}\n'.format(alias, getattr(self, self._wrap_alias(alias)).__name__[3:])
                                for alias in self.aliases)
            if not suppress:
                self.stdout.write(alias_str)
            else:
                return alias_str

    def __default_alias(self, force=False):
        if not hasattr(self, self._wrap_alias('a')) or force:
            setattr(self, self._wrap_alias('a'), self.do_alias)
