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
import time as _time
import glob as _glob
import ctypes as _ctypes
import itertools as _it

# constants
BOOKMARK_FILENAME = 'vlc_analyze_bookmarks.txt'
BOOKMARK_PATH = _os.path.dirname(_os.path.abspath(__file__))
BOOKMARK_FILE = _os.path.join(BOOKMARK_PATH, BOOKMARK_FILENAME)

# util functions


def trim_docstring(docstring):
    """trims docstring as specified in PEP 257
    https://www.python.org/dev/peps/pep-0257/"""
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = _sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < _sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


# input_timeout implementations
if _sys.platform.startswith('win'):
    from msvcrt import getch, kbhit
    from string import printable as _printable
    # todo: things to implement: delete/esc/arrow-key support,
    # http://help.adobe.com/en_US/AS2LCR/Flash_10.0/help.html?content=00000520.html
    # Arrows:
    # Left  0, 37
    # Up    0, 38
    # Right 0, 39
    # Down  0, 40

    # default system encoding
    _encoding = _sys.getdefaultencoding()

    # char listings
    PRINTABLE = _printable.replace('\t', '')
    BKSPCE_ONE_CHR = '\b  \b\b'

    # special_key_sig = {0, 224}  # Special (arrows, f keys, ins, del, etc.) keys are started with one of these codes
    # arrow_keys = {'left': 19424,   # left arrow
    #               'up': 18656,     # up arrow
    #               'right': 19936,  # right arrow
    #               'down': 20704,   # down arrow
    #               }

    special_key_sig = {b'\0', b'\xe0'}  # Special keys (arrows, f keys, ins, del, etc.)
    arrow_keys = {'left': b'\x4b',   # left arrow
                  'up': b'\x48',     # up arrow
                  'right': b'\x4d',  # right arrow
                  'down': b'\x50',   # down arrow
                  }


    def input_timeout(caption, timeout=5, default='', *_,
                      stream=_sys.stdout, timeout_msg='\n ----- timed out', completer=None, encoding=_encoding):

        if completer is None:
            try:
                import readline
                import rlcompleter
                input_timeout.old_completer = readline.get_completer()
                completer = rlcompleter.Completer()
                readline.set_completer(completer)
                readline.parse_and_bind("tab: complete")
                readline.parse_and_bind("up: previous-history")
                readline.parse_and_bind("down: next-history")
                readline.parse_and_bind("Return: accept-line ")
            except ImportError:
                pass
        else:
            try:
                import readline
                readline.parse_and_bind("up: previous-history")
                readline.parse_and_bind("down: next-history")
                readline.parse_and_bind("Return: accept-line ")
            except ImportError:
                pass

        def write_flush(string):
            stream.write(string)
            stream.flush()

        start_time = _time.time()
        if default == '':
            write_flush('{}'.format(caption))
        else:
            write_flush('{}({}):'.format(caption, default))
        try:
            byte_arr = bytearray(input_timeout.partial)
            write_flush(str(input_timeout.partial, encoding))
        except AttributeError:
            byte_arr = bytearray()
        input_string = ''
        while True:
            try:
                if kbhit():
                    char = getch()
                    if char in special_key_sig:  # if special key, get extra byte and merge
                        # tmp = getch()
                        # char = ord(char) + (ord(tmp) << 8)
                        char = getch()
                    if char in arrow_keys.values():
                        try:
                            fake_keys = bytearray([224, 77, 224, 0x48])
                            old_stdin = _sys.stdin
                            _sys.stdin = fake_keys
                            readline.get_line_buffer()
                            _sys.stdin = old_stdin
                        except Exception as e:
                            # print(e)
                            pass

                        if char == arrow_keys['up']:
                            try:
                                write_flush(BKSPCE_ONE_CHR * len(byte_arr))
                                byte_arr = bytearray(input_timeout.previous)
                                write_flush(str(input_timeout.previous, encoding))
                                # input_timeout.previous = b''
                            except AttributeError:
                                pass
                    elif char == b'\r':  # enter_key
                        input_string = str(byte_arr, encoding)
                        try:
                            readline.add_history(input_string)
                        except:
                            pass
                        input_timeout.partial = b''
                        if input_string.strip():
                            input_timeout.previous = byte_arr
                        break
                    elif char == b'\b':  # backspace_key
                        try:
                            byte_arr.pop()
                            write_flush(BKSPCE_ONE_CHR)
                        except IndexError:
                            pass
                    elif char == b'\t':
                        try:
                            phrase = str(byte_arr, encoding)
                            terms = []
                            old_stdin = _sys.stdin
                            _sys.stdin = byte_arr
                            for idx in range(10):
                                term = completer(phrase, idx)
                                if term is None:
                                    break
                                terms.append(term)
                            _sys.stdin = old_stdin
                            if terms:
                                if len(terms) == 1:
                                    partial = terms[0][len(phrase):]
                                    byte_arr.extend(bytearray(partial, encoding))
                                    write_flush(partial)
                                else:
                                    complete_txt = '  '.join([term for term in terms])
                                    write_flush('\n' + complete_txt)
                                    input_timeout.partial = byte_arr
                                    break
                        except Exception as e:
                            print('\n', e, '\n')
                            pass
                    elif str(char, encoding) in PRINTABLE:  # PRINTABLE character
                        byte_arr.append(ord(char))
                        write_flush(str(char, encoding))

                if (_time.time() - start_time) > timeout:
                    stream.write(timeout_msg)
                    break
            except KeyboardInterrupt:
                write_flush('\n')
                _sys.exit(0)

        try:
            import readline
            readline.set_completer(input_timeout.old_completer)
        except (ImportError, AttributeError):
            pass

        write_flush('\n')  # needed to move to next line
        if input_string:
            return input_string
        else:
            return default


    input_timeout.partial = b''
    input_timeout.previous = b''
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
    with open(file_name, 'a') as f:
        f.write(data)

    # For windows set file attribute.
    if _os.name == 'nt':
        ret = win_set_attribute_func(file_name, FILE_ATTRIBUTE_HIDDEN)
        if not ret:  # There was an error.
            raise _ctypes.WinError()


def make_hidden(file_name):
    # noinspection PyPep8Naming
    try:
        open(file_name, 'w')
    except PermissionError:
        pass

    # noinspection PyPep8Naming
    FILE_ATTRIBUTE_HIDDEN = 0x02
    win_set_attribute_func = _ctypes.windll.kernel32.SetFileAttributesW
    # For *nix add a '.' prefix.
    prefix = '.' if _os.name != 'nt' else ''
    file_name = prefix + file_name
    if _os.name == 'nt':
        ret = win_set_attribute_func(file_name, FILE_ATTRIBUTE_HIDDEN)
        if not ret:  # There was an error.
            raise _ctypes.WinError()
    return file_name


def bookmarks_load(path=BOOKMARK_FILE):
    bkmarks = set()
    try:
        with open(path, 'r') as bkfile:
            for line in bkfile:
                bkmarks.add(line.rstrip())
                # bkmarks = set(filter(None, bkmarks))
                # bkmarks = set(filter(_os.path.isfile, bkmarks))
    except FileNotFoundError:
        write_hidden(path, '')
    finally:
        return bkmarks


def bookmark_file(media_file, path=BOOKMARK_FILE):
    with open(path, 'a') as bkfile:
        bkfile.write('{}\n'.format(media_file))


def bookmark_files(files, path=BOOKMARK_FILE):
    with open(path, 'a') as bkfile:
        for file in files:
            bkfile.write('{}\n'.format(file))


def bookmark_remove(bookmark, path=BOOKMARK_FILE):
    tmp_path, tmp_name = _os.path.split(path)
    tmp_name = _os.path.splitext(tmp_name)[0] + '.tmp'
    tmp_file = make_hidden(_os.path.join(tmp_path, tmp_name))
    with open(path, 'r') as bkfile:
        with open(tmp_file, 'r+') as tmpfile:
            for line in bkfile:
                if line.rstrip() != bookmark:
                    tmpfile.write(line)
    _os.remove(path)
    _os.rename(tmp_file, path)


def bookmark_clear_mark(path=BOOKMARK_FILE):
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


def search_through_dirs(path):
    # results = {}
    for subdir,dirs,files in _os.walk(path):
        try:
            # print(subdir)
            media = max(_glob.glob(_os.path.join(subdir,'*.mp3')),key=lambda x:_os.path.getsize(x))
            # results[subdir]=(media,_os.path.getsize(media))
            yield _os.path.abspath(media)
        except ValueError:
            pass
            # print(subdir)
    
