#! /bin/env/python

r"""
HKEY_CLASSES_ROOT\Applications\python.exe\shell\open\command
"C:\Program Files\Python36\python.exe" "%1" %*

This program allows you to use the command line to cycle through all the media files in a directory
and play them with vlc player as well as edit each file's metadata
"""


__author__ = 'Danyal Ahsanullah'
__version_info__ = (0, 3, 3)
__version__ = '.'.join(map(str, __version_info__))


import os as _os
import vlc as _vlc
import sys as _sys
import time as _time
from argparse import ArgumentParser as _ArgParser

import _utils
import metadata


# find the local copy of vlc.py from the cloned github repo
# _VLCPATH = os.path.abspath(os.path.join(os.curdir,'vlc_python','generated'))
# sys.path.append(_VLCPATH)
# # del _VLCPATH
# import vlc as _vlc

# create cli parser
parser = _ArgParser('vlc_analyze')
parser.add_argument('--version', '-V', action='version', version="%(prog)s " + __version__)
parser.add_argument('path', type=str, nargs='*', help='path of file(s) to be read in.', default=_os.curdir)
# parser.add_argument('--output', '-o', type=str,
#                     help='base directory to save results into. If the path given doesnt exist, it will be made.')
parser.add_argument('--extension', '-e', type=str, nargs='+',
                    help=('comma separated extension(s) to use for file(s) in directory provided\n'
                          'NOTE: As of now, only mp3 files support metadata editing'),
                    default='mp3'
                    # default='mp3, wav, flac, ogg, mp4'
                    )
parser.add_argument('--interact', '-i', action="store_true",
                    help=('if enabled will allow for interactive prompts ' 
                          'before proceeding with modifying/removing files.'),
                    )
parser.add_argument('--recursive', '-r', action='store_true', help='flag that sets recursive file search')
parser.add_argument('--clear', '-c', action='store_true', help='clears bookmarks')
# parser.add_argument('--verbose', '-v', action="store_true", help='prints a more detailed output.')
# parser.add_argument('--quiet', '-q', action="store_true", help='supresses console output.')


def audio_file_edit(media_file):
    _prompt = ('\n'
               'press Ctrl-c to skip to next track.\n'
               'press "e" to edit metadata.\n'
               'press "d" to delete.\n'
               'press "q" to quit immediately.\n'
               'press "s <num>" to jump that many seconds (+/-) in the track. ("s" is +30s)\n'
               'press "b" to bookmark the current track as the spot to startup on the next run\n'
               )
    try:
        # flag = threading.Event()
        meta = metadata.Metadata(media_file)
        md = meta.get_audio_metadata(['artist', 'title'])
        print(78 * '-', '\nplaying: %s \nTitle: %s\nArtist: %s' % (_os.path.basename(media_file), *md))
        print('Path: {}'.format(_os.path.abspath(media_file)))
        p = _vlc.MediaPlayer(media_file)
        # code.interact(local=locals())
        p.play()
        _time.sleep(.1)
        while p.is_playing():
            try:
                # raw_in = input_with_timeout(_prompt, (meta.get_audio_length() - .5), interrupt_func=flag.is_set)
                # choice = str(raw_in, 'utf-8').rstrip()
                raw_in = _utils.input_timeout(_prompt, timeout=(meta.length - .5))
                                           # interrupt=p.is_playing, inverse=True)
                choice = raw_in.rstrip()
            except ValueError:
                choice = ''
            # print(choice + '\n')
            try:
                if choice == 'q':
                    p.stop()
                    _sys.exit(0)
                elif choice == 'd':
                    if args.interact:
                        confirm = input('Really delete? (y/n): ')
                        if 'y' not in confirm.rstrip().lower():
                            raise KeyboardInterrupt
                    print('deleting media_file')
                    p.stop()
                    _os.remove(media_file)
                    raise KeyboardInterrupt
                elif choice == 'e':
                    meta.edit_meta_data()
                elif 's' in choice:
                    try:
                        # print(float(choice[2:])/meta.get_audio_length())
                        # print(p.get_position())
                        calc_pos = (float(choice[2:]) / meta.length) + p.get_position()
                        if calc_pos > 1:
                            p.set_position(0.999)
                            # flag.set()
                            p.stop()
                            _time.sleep(0.1)
                        elif calc_pos < 0:
                            p.set_position(0)
                        else:
                            p.set_position(calc_pos)
                            # print(p.get_position())
                    except ValueError:
                        # skip forward 30 seconds. equal to 's 30'
                        p.set_position((30.0 / meta.length) + p.get_position())
                elif choice == 'b':
                    _utils.bookmark_file(media_file)
            except (TypeError, UnicodeDecodeError):
                pass
            _time.sleep(.1)
            if p.get_position() > .997:
                p.stop()
                # flag.set()
        p.stop()
        del p
        return
    except KeyboardInterrupt:
        p.stop()
        del p
        return


if __name__ == '__main__':
    BASE_PATH = _os.getcwd()
    args = parser.parse_args()
    # print(vars(args))
    if args.clear:
        bookmarks = ''
        _utils.clear_marks()
        print('\nCleared Bookmarks!')
    else:
        bookmarks = _utils.load_bookmarks()
        if bookmarks:
            for bookmark in bookmarks:
                comm_path = _os.path.commonprefix([BASE_PATH, bookmark])
                relpath = bookmarks[0][len(comm_path):]
                base_name = _os.path.basename(bookmarks[0])
                bk_msg = ('\nExisting bookmark found: {}\n'
                          'RelativePath: .{}\n'
                          )
                print(bk_msg.format(base_name, relpath))
            print('\nRun again with the -c flag to clear bookmark\n')
    print('Using vlc:', str(_vlc.libvlc_get_version(), 'utf-8'))
    # print(vars(args))
    # print(bookmarks)
    for path in args.path:
        if _os.path.isdir(path):
            print('\nnow searching in: {} {}'.format(path, '(resursive)' if args.recursive else ''))
            files = _utils.multiple_file_types(path, _utils.split_comma_str(args.extension), recursion=args.recursive)
            hit = False if bookmarks else True
            while not hit:  # skip until hit the bookmark
                for file in files:
                    # print(file)
                    if file in bookmarks:
                        audio_file_edit(file)
                        try:
                            bookmarks.remove(file)
                        except KeyError:
                            hit = True
                            break
                    else:
                        pass
            for file in files:
                audio_file_edit(file)
        else:
            print(path)
            audio_file_edit(path)
    _sys.exit(0)
