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


import os
import vlc
import sys
import time
from itertools import chain
from collections import deque

import _utils
import metadata
from shells import AudioShell


# find the local copy of vlc.py from the cloned github repo
# _VLCPATH = os.path.abspath(os.path.join(os.curdir,'vlc_python','generated'))
# sys.path.append(_VLCPATH)
# # del _VLCPATH
# import vlc as _vlc


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
        meta = metadata.Metadata(media_file)
        md = meta.get_audio_metadata(['artist', 'title'])
        print(78 * '-', '\nplaying: %s \nTitle: %s\nArtist: %s' % (os.path.basename(media_file), *md))
        print('Path: {}'.format(os.path.abspath(media_file)))
        p = vlc.MediaPlayer(media_file)
        p.play()
        time.sleep(.1)
        while p.is_playing():
            try:
                raw_in = _utils.input_timeout(_prompt, timeout=(meta.length - .5))
                choice = raw_in.rstrip()
            except ValueError:
                choice = ''
            # print(choice + '\n')
            try:
                if choice == 'q':
                    p.stop()
                    sys.exit(0)
                elif choice == 'd':
                    if args.interact:
                        confirm = input('Really delete? (y/n): ')
                        if 'y' not in confirm.rstrip().lower():
                            raise KeyboardInterrupt
                    print('deleting media_file')
                    p.stop()
                    os.remove(media_file)
                    raise KeyboardInterrupt
                elif choice == 'e':
                    meta.edit_meta_data()
                elif 's' in choice:
                    try:
                        calc_pos = (float(choice[2:]) / meta.length) + p.get_position()
                        if calc_pos > 1:
                            p.set_position(0.999)
                            p.stop()
                            time.sleep(0.1)
                        elif calc_pos < 0:
                            p.set_position(0)
                        else:
                            p.set_position(calc_pos)
                    except ValueError:
                        # skip forward 30 seconds. equal to 's 30'
                        p.set_position((30.0 / meta.length) + p.get_position())
                elif choice == 'b':
                    _utils.bookmark_file(media_file)
            except (TypeError, UnicodeDecodeError):
                pass
            time.sleep(.1)
            if p.get_position() > .997:
                p.stop()
        p.stop()
        del p
        return
    except KeyboardInterrupt:
        p.stop()
        del p
        return


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser('vlc_analyze')
    parser.add_argument('--version', '-V', action='version', version="%(prog)s " + __version__)
    parser.add_argument('path', type=str, nargs='*', help='path of file(s) to be read in.', default=os.curdir)
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

    BASE_PATH = os.getcwd()
    args = parser.parse_args()
    # print(vars(args))
    if args.clear:
        bookmarks = {''}
        _utils.bookmark_clear_mark()
        sys.stdout.write('\nCleared Bookmarks!\n')
        sys.stdout.flush()
    else:
        bookmarks = _utils.bookmarks_load()
        if bookmarks:
            for bookmark in bookmarks:
                comm_path = os.path.commonprefix([BASE_PATH, bookmark])
                relpath = bookmark[len(comm_path):]
                base_name = os.path.basename(bookmark)
                bk_msg = ('\nExisting bookmark found: {}\n'
                          'RelativePath: .{}\n'
                          )
                sys.stdout.write(bk_msg.format(base_name, relpath))
            sys.stdout.write('\nRun again with the -c flag to clear bookmark\n')
    sys.stdout.write('Using vlc:{}\n'.format(str(vlc.libvlc_get_version(), 'utf-8')))
    sys.stdout.flush()
    # print(vars(args))
    # print(bookmarks)
    for path in args.path:
        if os.path.isdir(path):
            sys.stdout.write('\nnow searching in: {} {}\n'.format(path, '(recursive)' if args.recursive else ''))
            sys.stdout.flush()
            files = _utils.multiple_file_types(path, _utils.split_comma_str(args.extension),
                                               recursion=args.recursive)
            shell = AudioShell(media_files=files, interact=args.interact)
            if bookmarks:
                while bookmarks:
                    file = next(files)
                    try:
                        if file in bookmarks:
                            shell.file_list = chain([file], files)
                            shell.cmdloop()
                            bookmarks.remove(file)
                            # break
                    except StopIteration:
                        pass
            else:
                shell.cmdloop()
        else:
            sys.stdout.write(path+'\n')
            sys.stdout.flush()
            shell = AudioShell([path], interact=args.interact)
            shell.cmdloop()
    sys.exit(0)
