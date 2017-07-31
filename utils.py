#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
vlc_check_audio
utils.py
Author: Danyal Ahsanullah
Date: 7/29/2017
Copyright (c):  2017 Danyal Ahsanullah
License: N/A
Description: 
"""


import rlcompleter
import readline
import ctypes as _ctypes
import glob as _glob
import itertools as _it
import os as _os
import sys as _sys
import time as _time

from metadata import Metadata
from interpreter import (
    HideUndocumentedInterpreter,
    # AliasedInterpreter,
    AliasCmdInterpreter
                    )

__version__ = '0.1'

readline.parse_and_bind("tab: complete")

if _sys.platform.startswith('win'):
    import msvcrt as _msvcrt
    from string import printable as _printable
    _special_key_sig = {0, b'\xe0'}  # Special keys (arrows, f keys, ins, del, etc.)
    # _special_key_sig = {b'\0', b'\xe0'}  # Special keys (arrows, f keys, ins, del, etc.)

    # todo: thing to implement: arrow key support, delete key support, tab support, readline support
    _printable = _printable.replace('\t', '')

    def input_timeout(caption, timeout=5, default='', *_, stream=_sys.stdout, timeout_msg='\n ----- timed out'):
        start_time = _time.time()

        def write_flush(string):
            stream.write(string)
            stream.flush()

        if default == '':
            write_flush('{}'.format(caption))
        else:
            write_flush('{}({}):'.format(caption, default))
        input_string = ''
        byte_arr = bytearray()
        while True:
            if _msvcrt.kbhit():
                char = _msvcrt.getch()
                if ord(char) in _special_key_sig:  # if special key, get extra byte and merge
                    tmp = _msvcrt.getch()
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
                elif str(char, 'utf-8') in _printable:  # printable character
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


    def read_input(prompt, timeout):
        _sys.stdout.write(prompt)
        _sys.stdout.flush()
        ready, _, _ = _select.select([_sys.stdin], [], [], timeout)
        if ready:
            return _sys.stdin.readline().rstrip('\n')  # expect stdin to be line-buffered
        raise TimeoutExpired
else:
    raise OSError('Unsupported platform %s' % _sys.platform)


class TimeoutExpired(Exception):
    """timeout occurred"""


# class MdataShell(AliasedShell, HideUndocumentedShell):
class MdataShell(AliasCmdInterpreter, HideUndocumentedInterpreter):
    __doc__ = ('version: {}\n'
               'Metadata Shell for interacting with MetaData objects.\n'
               ''.format(__version__)
               )
    intro = 'Metadata for: '
    prompt = 'Metadata: '
    doc_header = 'Commands (type help/? <topic>):'
    misc_header = 'Reference/help guides (type help/? <topic>):'
    # ruler = '-'

    def __init__(self, mdata: Metadata, *args, parent=None, view=None, **kwargs):
        super(MdataShell, self).__init__(*args, **kwargs)
        self.meta = mdata
        self.intro += mdata.file
        # self.intro = '{}"{}"'.format(self.intro, mdata.file)
        if parent is not None:
            self.prompt = ' -> '.join([parent.prompt.strip(), self.prompt])
        self.tmp_dict = mdata.tags

        if view is not None:
            self.intro += '\n{}'.format(self.do_view(supress=True))

    # def emptyline(self):
    #     pass

    # noinspection PyUnusedLocal,PyPep8Naming

    @staticmethod
    def do_cancel(*args):
        """
        Cancel making changes to current file's metadata and quit editing.
        Discards any unsaved changes to metadata.

        Usage:
        cancel

        Options:
        []
        """
        return True

    # noinspection PyUnusedLocal
    def do_view_dict(self, *args):
        # """
        # debug option
        # """
        self.stdout.write('\ntemp dict\n')
        for key in self.tmp_dict:
            self.stdout.write('{}: {}\n'.format(key, self.tmp_dict[key]))

        self.stdout.write('\nactual dict\n')

        for key in self.meta.audio:
            self.stdout.write('{}: {}\n'.format(key, self.meta.audio[key]))

        if 'save' in args:
            self.do_save()
            self.stdout.write('\nactual dict after merge\n')

            for key in self.meta.audio:
                self.stdout.write('{}: {}\n'.format(key, self.meta.audio[key]))


            # noinspection PyUnusedLocal
    def do_save(self, *args):
        """
        Save current metadata tags to current file.

        Usage:
        save

        Options:
        []
        """
        self.meta.save(self.tmp_dict)

    def do_view(self, args='', supress=False):
        """
        View current working set of metadata tags.

        Usage:
        view [<field1>,<field2>,...]

        Options:
        [field] -- comma separated list of fields to find.
                   if not provided, will print all entries.

        Example:
        view artist,title,track
        """
        ags = [arg.lower() for arg in filter(None, args.strip().replace(' ', ',').split(','))]
        if ags:
            for arg in ags:
                try:
                    self.stdout.write('{:>15}: {}\n'.format(arg, self.tmp_dict[arg][0]))
                except KeyError:
                    self.stdout.write('No such field {}\n'.format(arg))
        elif supress:
            return ''.join('{:>15}: {}\n'.format(key, self.tmp_dict[key][0]) for key in self.tmp_dict)
        else:
            for key in self.tmp_dict:
                if self.tmp_dict[key][0] != '':
                    self.stdout.write('{:>15}: {}\n'.format(key, self.tmp_dict[key][0]))

    # noinspection PyUnusedLocal
    def do_quit(self, *args):
        """
        Temporarily close shell. Updates metadata but does NOT apply changes to file.

        Usage:
        quit [-c]

        Options:
        [-c] -- clear, if enabled, will reload local metadata from file again.
        """
        if '-c' in args:
            self.tmp_dict = self.meta.tags
        else:
            self.meta.update(self.tmp_dict)
            # self.tmp_dict = {k: v for k, v in self.tmp_dict.items() if v[0] != ''}
        return True

    def do_edit(self, args):
        """
        Edit metadata tags on current file.

        Usage:
        edit [params | -c]

        Options:
        [params] -- list of field, value paris in the following order:
                    <field1>::<val>,, <field2>::<val>,, ...
        [-c] -- reset metadata from file.

        Examples:
        edit <artist>::<Artist_1>,, <title>::<Title_Track>,, <track>:<1/42>
        """
        if '-c' != args:
            tmp_dict = self.meta.parse_update_line(args)
            self.tmp_dict.update(tmp_dict)
            # self.tmp_dict = {k: v for k, v in self.tmp_dict.items() if v[0] != 0}
        else:
            self.stdout.write('reset metadata\n')
            self.tmp_dict = self.meta.tags

    # noinspection PyUnusedLocal
    def complete_edit(self, text, line, begidx, endidx):
        active_tags = [i for i in self.meta.tags if i.startswith(text)]
        if active_tags:
            return active_tags
        else:
            return [i for i in self.meta.possible_tags if i.startswith(text)]

    # noinspection PyUnusedLocal
    def help_tutorial(self, *args):
        self.stdout.write(self.__doc__)

    # noinspection PyUnusedLocal,PyPep8Naming
    def do_EOF(self, *args):
        return  self.do_cancel()

    # internal masking -- not aliased
    complete_view = complete_edit

    # alias commands
    alias_e = do_edit
    alias_q = do_quit
    alias_s = do_save
    alias_v = do_view
    alias_c = do_cancel


class BookMark:
    BOOKMARK_FILE = 'vlc_analyze_bookmarks.txt'
    bookmark_path = _os.path.join(_os.path.dirname(_os.path.realpath(__file__)),
                                  BOOKMARK_FILE)

    @staticmethod
    def write_hidden(file_name, data):
        """
        Cross platform hidden file writer.
        """
        # noinspection PyPep8Naming
        FILE_ATTRIBUTE_HIDDEN = 0x02
        win_set_attribute_func = _ctypes.windll.kernel32.SetFileAttributesW
        # For *nix add a '.' prefix.
        prefix = '.' if _os.name != 'nt' else ''
        file_name = prefix + file_name

        # Write file.
        with open(file_name, 'w') as f:
            f.write(data)

        # For windows set file attribute.
        if _os.name == 'nt':
            ret = win_set_attribute_func(file_name, FILE_ATTRIBUTE_HIDDEN)
            if not ret:  # There was an error.
                raise _ctypes.WinError()

    if not _os.path.isfile(bookmark_path):
        write_hidden(bookmark_path, '')

    @staticmethod
    def load_bookmarks():
        bkmarks = []
        with open(BookMark.bookmark_path, 'r') as bookmark_file:
            for line in bookmark_file:
                bkmarks.append(line.rstrip())
        bkmarks = list(filter(None, bkmarks))
        return bkmarks

    @staticmethod
    def bookmark_file(media_file):
        with open(BookMark.bookmark_path, 'r+') as bookmark_file:
            bookmark_file.truncate()
            if media_file is not None:
                bookmark_file.write('{}\n'.format(media_file))

    @staticmethod
    def clear_marks():
        BookMark.bookmark_file(None)


def split_comma_str(comma_str):
    return [item for item in comma_str.replace(' ', '').split(',')]


def multiple_file_types(path, patterns, recursion=False):
    if recursion:
        files = (_glob.iglob(_os.path.abspath(_os.path.join(path, './**/*.{}'.format(pattern))), recursive=recursion)
                 for
                 pattern in patterns)
    else:
        files = (_glob.iglob(_os.path.abspath(_os.path.join(path, '*.{}'.format(pattern)))) for pattern in patterns)
    return _it.chain.from_iterable(files)


if __name__ == '__main__':
    import os
    import sys
    import shutil
    from glob import glob
    from random import choice

    val = input_timeout('this is a test for 5 second timer.', 5)
    print(val)

    def rand_track(clean=False):
        source_dir = os.path.join(os.curdir, 'ref', 'music', '**')
        tmp_dir = os.path.join(os.curdir, 'ref', 'temp')
        fetched_track = choice(glob(os.path.join(source_dir, '*.mp3'), recursive=True))
        dup = os.path.isfile(os.path.join(tmp_dir, os.path.basename(fetched_track)))
        if dup and not clean:
            return dup
        else:
            if not os.path.isdir(tmp_dir):
                os.mkdir(tmp_dir)
            local = os.path.join(tmp_dir, '{}_tmp{}'.format(*os.path.splitext(os.path.basename(fetched_track))))
            shutil.copy(fetched_track, local)
            return local

    # par = MdataShell(Metadata(rand_track()), view=True)
    # shell = MdataShell(Metadata(rand_track()), view=True, parent=par)
    shell = MdataShell(Metadata(rand_track()), view=False)
    shell.cmdloop()
    sys.exit(0)
