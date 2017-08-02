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


import os as _os
import sys as _sys
import vlc as _vlc
import glob as _glob
import time as _time
import itertools as _it
import ctypes as _ctypes
import urllib.request as urllib

from metadata import Metadata
from interpreter import (
                          # AliasedMix,
                          TimeoutInputMix,
                          AliasCmdInterpreter,
                          HideUndocumentedInterpreter,
                        )

__version__ = '0.2'

# constants

HORIZ_LINE = 78 * '-'
BOOKMARK_FILE = 'vlc_analyze_bookmarks.txt'
BOOKMARK_PATH = _os.path.join(_os.path.dirname(_os.path.realpath(__file__)),
                              BOOKMARK_FILE)

# util functions


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


def load_bookmarks(path=BOOKMARK_PATH):
    bkmarks = set()
    try:
        with open(path, 'r') as bkfile:
            for line in bkfile:
                if _os.path.isfile(line):
                    bkmarks.add(line.rstrip())
        # bkmarks = set(filter(None, bkmarks))
        # bkmarks = set(filter(_os.path.isfile, bkmarks))
    except FileNotFoundError:
        write_hidden(path, '')
    finally:
        return bkmarks


def bookmark_file(media_file, path=BOOKMARK_PATH):
    with open(path, 'a') as bkfile:
            bkfile.write('{}\n'.format(media_file))


def clear_marks(path=BOOKMARK_PATH):
    with open(path, 'r+') as bkfile:
        bkfile.truncate()


def split_comma_str(comma_str):
    return [item for item in comma_str.replace(' ', '').split(',')]


def multiple_file_types(path, patterns, recursion=False):
    if recursion:
        files = (_glob.iglob(_os.path.abspath(_os.path.join(path, './**/*.{}'.format(pattern))), recursive=recursion)
                 for pattern in patterns)
    else:
        files = (_glob.iglob(_os.path.abspath(_os.path.join(path, '*.{}'.format(pattern))))
                 for pattern in patterns)
    return _it.chain.from_iterable(files)


if _sys.platform.startswith('win'):
    from msvcrt import getch, kbhit
    from string import printable as _printable

    import rlcompleter
    import readline

    old_completer = readline.get_completer()
    completer = rlcompleter.Completer()
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

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
                elif char == b'\t':
                    try:
                        phrase = str(byte_arr, 'utf-8')
                        for idx in range(_sys.maxsize):
                            term = completer.complete(phrase, idx)
                            if term is None:
                                continue
                            byte_arr.extend([char for char in term])
                            write_flush(term)
                    except:
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
        return ''
else:
    raise OSError('Unsupported platform {}'.format(_sys.platform))


class AudioShell(AliasCmdInterpreter, HideUndocumentedInterpreter, TimeoutInputMix):
    # intro = 'now_playing: '
    prompt = '> '
    doc_header = 'Commands (type help/? <topic>):'
    misc_header = 'Reference/help guides (type help/? <topic>):'

    def __init__(self, media_files, interact=False, *args, parent=None, **kwargs):
        super(AudioShell, self).__init__(*args, **kwargs)
        self.file_list = iter(media_files)
        self.played_files = []
        self.player_instance = _vlc.Instance()
        self.interactive = interact
        self.player = self.player_instance.media_player_new()

        try:
            file = next(self.file_list)
            media = self.player_instance.media_new(file)
            self.player.set_media(media)
            self.metadata = Metadata(file)
            self.timeout = self.metadata.get_audio_length() + .1
            self._set_prompt(file)
            self.mdatashell = MetaDataShell(self.metadata, parent=self, view=True)
        except StopIteration:
            raise IOError('Empty file list provided.')

    # audio_set_volume(self, i_volume) # (0 = mute, 100 = 0dB). ret 0 on sucess, -1 if out of range
    # audio_get_volume(self)
    # audio_get_track_count
    # audio_get_track (ret track ID )
    # audio_set_track (i_id field from track description)
    # audio_set_mute (bool)
    # audio_get_mute (bool)
    # audio_toggle_mute
    # pause
    # stop
    # play
    # set_pause # toggle pause/resume
    # get_media
    # set_media

    def _set_timeout(self):
        self.timeout = self.metadata.get_audio_length() * (1 - self.player.get_position()) + .1

    def _set_prompt(self, file_name):
        name = _os.path.splitext(_os.path.basename(file_name))[0]
        if len(name) > 30:
            name = name[:27] + '...'
        self.prompt = '{} > '.format(name)


    @staticmethod
    def emptyline():
        return False

    def preloop(self):
        self.player.play()
        file = urllib.unquote(self.player.get_media().get_mrl())[8:]
        md = self.metadata.get_audio_metadata(['artist', 'title'])
        self.stdout.write('{}\nplaying: {}\nTitle: {}\nArtist: {}\n'
                          'Path: {}\n'.format(HORIZ_LINE, _os.path.basename(file), *md,_os.path.abspath(file))
                          )
        self.stdout.flush()
        _time.sleep(.2)
        # return self.postcmd(None, '')

    # noinspection PyUnusedLocal
    def postcmd(self, stop, line):
        if stop:
            return True
        if not self.player.is_playing():
            return self.next_track()
        else:
            self._set_timeout()

    def cleanup(self):
        self.file_list = iter([])
        self.player.stop()
        self.player_instance.release()

    def next_track(self):
        try:
            self.player.stop()
            file = next(self.file_list)
            media = self.player_instance.media_new(file)
            self.player.set_media(media)
            self.metadata = Metadata(file)
            self._set_prompt(file)
            self.mdatashell = MetaDataShell(self.metadata, parent=self, view=True)
            self._set_timeout()
            self.player.play()
            md = self.metadata.get_audio_metadata(['artist', 'title'])
            self.stdout.write('{}\nplaying: {}\nTitle: {}\nArtist: {}\n'
                              'Path: {}\n'.format(HORIZ_LINE, _os.path.basename(file), *md, _os.path.abspath(file))
                              )
            self.stdout.flush()
            _time.sleep(.2)
            return False
        except StopIteration:
            self.cleanup()
            return True

    def do_edit(self, *args):
        self.mdatashell.cmdloop()

    def do_delete(self, *args):
        self.player.stop()
        file_path = urllib.unquote(self.player.get_media().get_mrl())[8:]
        if self.interactive:
            confirm = input('Really delete? (y/n): ')
            if 'y' == confirm.rstrip().lower():
                _os.remove(file_path)
                self.next_track()
        else:
            _os.remove(file_path)
            self.next_track()

    # noinspection PyUnusedLocal
    def do_quit(self, *args):
        self.cleanup()

    def do_skip(self, duration=''):
            if not duration:
                duration = 30.0
            calc_pos = (float(duration) / self.metadata.get_audio_length()) + self.player.get_position()
            if calc_pos > 1:
                self.player.stop()
                _time.sleep(0.1)
            elif calc_pos < 0:
                self.player.set_position(0)
            else:
                self.player.set_position(calc_pos)

    def do_bookmark(self, *args):
        pass

    def do_next_track(self, *args):
        self.next_track()

    # internal masking:
    do_EOF = do_quit

    # aliased commmands
    alias_d = do_delete
    alias_e = do_edit
    alias_q = do_quit
    alias_s = do_skip
    alias_b = do_bookmark
    alias_n = do_next_track
    alias_next = do_next_track


class MetaDataShell(AliasCmdInterpreter, HideUndocumentedInterpreter):
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
        super(MetaDataShell, self).__init__(*args, **kwargs)
        self.meta = mdata
        self.intro += mdata.file

        # handle nesting shells
        if parent is not None:
            self.prompt = ' -> '.join([parent.prompt.strip()[:30], self.prompt])
        self.tmp_dict = mdata.tags

        # optional view avaible metadata on shell startup.
        if view is not None:
            self.intro += '\n{}'.format(self.do_view(supress=True))

    # def emptyline(self):
    #     pass

    def do_cancel(self, *args):
        """
        Cancel making changes to current file's metadata and quit editing.
        Discards any unsaved changes to metadata.

        Usage:
        cancel

        Options:
        []
        """
        self.stdout.write('\n')
        return True

    # noinspection PyUnusedLocal
    # def do_view_dict(self, *args):
    #     # """
    #     # debug option
    #     # """
    #     self.stdout.write('\ntemp dict\n')
    #     for key in self.tmp_dict:
    #         self.stdout.write('{}: {}\n'.format(key, self.tmp_dict[key]))
    #
    #     self.stdout.write('\nactual dict\n')
    #
    #     for key in self.meta.audio:
    #         self.stdout.write('{}: {}\n'.format(key, self.meta.audio[key]))
    #
    #     if 'save' in args:
    #         self.do_save()
    #         self.stdout.write('\nactual dict after merge\n')
    #
    #         for key in self.meta.audio:
    #             self.stdout.write('{}: {}\n'.format(key, self.meta.audio[key]))

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
            return ''.join('{:>15}: {}\n'.format(key, self.tmp_dict[key][0])
                           for key in self.tmp_dict if self.tmp_dict[key][0] != '')
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
            self.intro = 'Metadata for: {}\n{}'.format(_os.path.basename(self.meta.file), self.do_view(supress=True))
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
            self.tmp_dict.update(tmp_dict)                  # todo: handle user inputting invalid keys
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

    # # noinspection PyUnusedLocal
    # def help_tutorial(self, *args):
    #     self.stdout.write(self.__doc__)

    # noinspection PyUnusedLocal,PyPep8Naming
    def update_prompt(self, new_prompt):
        self.prompt = '{} -> Metadata: '.format(new_prompt)

    # internal masking -- not aliased
    complete_view = complete_edit
    do_EOF = do_cancel

    # alias commands
    alias_e = do_edit
    alias_q = do_quit
    alias_s = do_save
    alias_v = do_view
    alias_c = do_cancel


if __name__ == '__main__':
    import os
    import sys
    import shutil
    from glob import glob
    from random import choice

    # f = open(os.devnull, 'w')
    # sys.stderr = f

    # val = input_timeout('this is a test for 5 second timer.', 5)
    # print(val)

    NUM_TRACKS = 100
    src_dir = os.path.join(os.curdir, 'ref', 'music')
    tmp_dir = os.path.join(os.curdir, 'ref', 'temp')
    ext = 'mp3'

    def rand_track(source_dir, temp_dir, extension, clean=False, recur=True):
        fetched_track = choice(glob(os.path.join(source_dir, '**', '*.{}'.format(extension)), recursive=recur))
        tmp = os.path.join(temp_dir, os.path.basename(fetched_track))
        if os.path.isfile(tmp) and not clean:
            return tmp
        else:
            if not os.path.isdir(temp_dir):
                os.mkdir(temp_dir)
            local = os.path.join(temp_dir, '{}_tmp{}'.format(*os.path.splitext(os.path.basename(fetched_track))))
            shutil.copy(fetched_track, local)
            return local

    def rand_tracks(n, *args, **kwargs):
        num = 0
        while num < n:
            yield rand_track(*args, **kwargs)
            num += 1

    # par = MdataShell(Metadata(rand_track()), view=True)
    # shell = MdataShell(Metadata(rand_track()), view=True, parent=par)
    shell = MetaDataShell(Metadata(rand_track(src_dir, tmp_dir, ext)), view=False)
    # shell.cmdloop()

    # file_list = []
    # for i in range(3):
    #     file_list.append(rand_track(src_dir, tmp_dir, ext))
    #
    # shell = AudioShell(file_list, interact=True)
    shell = AudioShell(rand_tracks(NUM_TRACKS, src_dir, tmp_dir, ext), interact=True)
    shell.cmdloop()

    # f.close()
    sys.exit(0)
