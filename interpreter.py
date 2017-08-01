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
import sys as _sys
import time as _time
from cmd import Cmd as _Cmd


# misc functions / deorators


if _sys.platform.startswith('win'):
    from msvcrt import getch, kbhit
    from string import printable as _printable
    special_key_sig = {0, 224}  # Special (arrows, f keys, ins, del, etc.) keys are started with one of these codes
    # special_key_sig = {b'\0', b'\xe0'}  # Special keys (arrows, f keys, ins, del, etc.)

    # todo: things to implement: delete/tab/esc/arrow-key support, readline support
    # http://help.adobe.com/en_US/AS2LCR/Flash_10.0/help.html?content=00000520.html
    printable = _printable.replace('\t', '')

    def input_timeout(caption, timeout=5, default='', *_, stream=_sys.stdout, timeout_msg='\n ----- timed out'):

        def write_flush(string):
            stream.write(string)
            stream.flush()
        start_time = _time.time()
        if default == '':
            write_flush('{}'.format(caption))
        else:
            write_flush('{}({}):'.format(caption, default))
        input_string = ''
        byte_arr = bytearray()
        while True:
            if kbhit():
                char = getch()
                if ord(char) in special_key_sig:  # if special key, get extra byte and merge
                    tmp = getch()
                    char = bytes(ord(char) + (ord(tmp) << 8))
                    # print(char)
                if char == b'\r':  # enter_key
                    input_string = str(byte_arr, 'utf-8')
                    # stream.write('\nEntered: {}\n'.format(input_string))
                    # stream.flush()
                    break
                elif char == b'\b':  # backspace_key
                    try:
                        byte_arr.pop()
                        write_flush('\b  \b\b')
                    except IndexError:
                        pass
                elif str(char, 'utf-8') in printable:  # printable character
                    byte_arr.append(ord(char))
                    write_flush(str(char, 'utf-8'))

            if (_time.time() - start_time) > timeout:
                stream.write(timeout_msg)
                break

        write_flush('\n')  # needed to move to next line
        if input_string:
            return input_string
        else:
            return default

            # def keypress():
            #     """
            #     Waits for the user to press a key. Returns the ascii code
            #     for the key pressed or zero for a function key pressed.
            #     """
            #     import msvcrt
            #     while 1:
            #         if msvcrt.kbhit():  # Key pressed?
            #             a = ord(msvcrt.getch())  # get first byte of keyscan code
            #             if a == 0 or a == 224:  # is it a function key?
            #                 msvcrt.getch()  # discard second byte of key scan code
            #                 return 0  # return 0
            #             else:
            #                 return a  # else return ascii code
            #
            #
            # def funkeypress():
            #     """
            #     Waits for the user to press any key including function keys. Returns
            #     the ascii code for the key or the scancode for the function key.
            #     """
            #     import msvcrt
            #     while 1:
            #         if msvcrt.kbhit():  # Key pressed?
            #             a = ord(msvcrt.getch())  # get first byte of keyscan code
            #             if a == 0 or a == 224:  # is it a function key?
            #                 b = ord(msvcrt.getch())  # get next byte of key scan code
            #                 x = a + (b * 256)  # cook it.
            #                 return x  # return cooked scancode
            #             else:
            #                 return a  # else return ascii code
            #
            #
            # def anykeyevent():
            #     """
            #     Detects a key or function key pressed and returns its ascii or scancode.
            #     """
            #     import msvcrt
            #     if msvcrt.kbhit():
            #         a = ord(msvcrt.getch())
            #         if a == 0 or a == 224:
            #             b = ord(msvcrt.getch())
            #             x = a + (b * 256)
            #             return x
            #         else:
            #             return a
elif _sys.platform.startswith('linux'):
    import select as _select


    def input_timeout(prompt, timeout):
        _sys.stdout.write(prompt)
        _sys.stdout.flush()
        ready, _, _ = _select.select([_sys.stdin], [], [], timeout)
        if ready:
            return _sys.stdin.readline().rstrip('\n')  # expect stdin to be line-buffered
        else:
            return ''
else:
    raise OSError('Unsupported platform %s' % _sys.platform)

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


class AliasedMix(_Cmd):
    """
    interpreter that allows aliasing or commands using the alias_prefix
    """
    ALIAS_PREFIX = 'alias_'

    def __init__(self, *args, **kwargs):
        self.aliases = self.get_aliases()
        super(AliasedMix, self).__init__(*args, **kwargs)

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
            super(AliasedMix, self).default(line)
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

    def __init__(self, timeout=None, *args, **kwargs):
        super(TimeoutInputMix, self).__init__(*args, **kwargs)
        self.timeout = timeout

    def cmdloop(self, timeout=None, intro=None):
        """
        modified cmdloop method of the Cmd class supporting input with timeouts.

        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """

        if timeout is not None:
            get_input = lambda prompt: input_timeout(caption=prompt, timeout=timeout, stream=self.stdout)
        elif self.timeout is not None:
            get_input = lambda prompt: input_timeout(caption=prompt, timeout=self.timeout, stream=self.stdout)
        else:
            get_input = lambda prompt: input(prompt)

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


class HideUndocumentedInterpreter(HideNoneDocMix):
    """
    interpreter that hides undocumented commands from being displayed
    in the help messages.
    """
    undoc_header = None

    def __init__(self, *args, **kwargs):
        super(HideUndocumentedInterpreter, self).__init__(*args, **kwargs)


class AliasCmdInterpreter(AliasedMix):
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
