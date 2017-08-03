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
import sys
import vlc
import time
from itertools import chain

from vlc_analyze import utils
from vlc_analyze.shells import AudioShell
from vlc_analyze import metadata


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
        utils.bookmark_clear_mark()
        sys.stdout.write('\nCleared Bookmarks!\n')
        sys.stdout.flush()
    else:
        bookmarks = utils.bookmarks_load()
        if bookmarks:
            for bookmark in bookmarks:
                comm_path = os.path.commonprefix([BASE_PATH, bookmark])
                relpath = bookmark[len(comm_path):]
                base_name = os.path.basename(bookmark)
                bk_msg = '\nExisting bookmark found: {}\nRelativePath: .{}\n'
                sys.stdout.write(bk_msg.format(base_name, relpath))
            sys.stdout.write('\nRun again with the -c flag to clear bookmarks\n')
        else:
            del bookmarks
    sys.stdout.write('Using vlc: {}\n'.format(str(vlc.libvlc_get_version(), 'utf-8')))
    sys.stdout.flush()
    # print(vars(args))
    # print(bookmarks)
    for path in args.path:
        if os.path.isdir(path):
            sys.stdout.write('\nnow searching in: {} {}\n'.format(os.path.abspath(path), '(recursive)' if args.recursive else ''))
            sys.stdout.flush()
            files = utils.multiple_file_types(path, utils.split_comma_str(args.extension),
                                              recursion=args.recursive)
            shell = AudioShell(media_files=files, interact=args.interact)
            try:
                while bookmarks:
                    try:
                        file = next(files)
                        if file in bookmarks:
                            shell.file_list = chain([file], files)
                            shell.cmdloop()
                            bookmarks.discard(file)
                    except StopIteration:
                        break
            except NameError:
                try:
                    shell.cmdloop()
                except (NameError, StopIteration):
                    sys.stdout.write('No Files Found.\n')
                    sys.stdout.flush()
        else:
            sys.stdout.write(path+'\n')
            sys.stdout.flush()
            shell = AudioShell([path], interact=args.interact)
            shell.cmdloop()
    sys.exit(0)
