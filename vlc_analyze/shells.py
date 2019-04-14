#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
vlc_check_audio
shells.py
Author: Danyal Ahsanullah
Date: 8/2/2017
Copyright (c):  2017 Danyal Ahsanullah
License: N/A
Description: 
"""
import os as _os
import vlc as _vlc
import time as _time
from urllib import request as urllib
import shutil 

from . import utils
from .interpreter import AliasCmdInterpreter, HideNoneDocMix, TimeoutInputMix

from .metadata import Metadata

# constants
HORIZ_LINE = 78 * '-'


class AudioShell(AliasCmdInterpreter, HideNoneDocMix, TimeoutInputMix):
    # intro = 'now_playing: '
    prompt = '> '
    doc_header = 'Commands (type help/? <topic>):'
    misc_header = 'Reference/help guides (type help/? <topic>):'
    undoc_header = None

    def __init__(self, media_files, interact=False, move_path=None, *args, **kwargs):
        super(AudioShell, self).__init__(*args, **kwargs)
        self.file_list = iter(media_files)
        self.move_path = move_path
        self.played_files = []
        self.player_instance = _vlc.Instance()
        self.interactive = interact
        self.player = self.player_instance.media_player_new()

    def _set_timeout(self):
        self.timeout = self.metadata.length * (1 - self.player.get_position()) + .1

    def _set_prompt(self, file_name):
        name = _os.path.splitext(_os.path.basename(file_name))[0]
        if len(name) > 30:
            name = name[:27] + '...'
        self.prompt = '{} > '.format(name)

    def get_file_from_player(self):
        return urllib.unquote(self.player.get_media().get_mrl())[8:].replace('/', _os.sep)

    # noinspection PyMethodMayBeStatic
    def emptyline(self):
        return False

    # noinspection PyUnusedLocal
    def postcmd(self, stop, line):
        if stop:
            return True
        if not self.player.is_playing():
            return self.do_next_track()
        else:
            self._set_timeout()

    # noinspection PyUnusedLocal
    def do_quit(self, *args):
        """
        Cleanup and close the shell.

        Usage:
        quit
        """
        self.file_list = iter([])
        self.player.stop()
        self.player_instance.release()

    # noinspection PyUnusedLocal,PyAttributeOutsideInit
    def do_next_track(self, *args):
        """
        Move onto the next track.

        Usage:
        next_track
        """
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
            self.do_quit()
            return True

    # noinspection PyUnusedLocal
    def do_edit(self, *args):
        """
        Open the metadata shell to edit and view the current track's metadata.

        Usage:
        edit
        """
        self.mdatashell.cmdloop()

    # noinspection PyUnusedLocal
    def do_delete(self, *args):
        """
        Delete the current file begin played.
        If shell was launched in interactive mode, will prompt for a confirmation.

        Usage:
        delete
        """
        self.player.stop()
        file_path = urllib.unquote(self.player.get_media().get_mrl())[8:]
        if self.interactive:
            confirm = input('Really delete? (y/n): ')
            if 'y' == confirm.rstrip().lower():
                _os.remove(file_path)
                self.do_next_track()
        else:
            _os.remove(file_path)
            self.do_next_track()

    def do_skip(self, duration=''):
        """
        Skip a number of seconds forwards or back in the current track.
        Blank usage results in a +30 seconds skip.

        Usage:
        skip [seconds]

        Options:
        [seconds] -- number of seconds (+/-) to jump in the track. Defaults to 30 seconds.

        """
        if not duration:
            duration = 30.0
        calc_pos = (float(duration) / self.metadata.length) + self.player.get_position()
        if calc_pos > 1:
            self.player.stop()
            _time.sleep(0.1)
        elif calc_pos < 0:
            self.player.set_position(0)
        else:
            self.player.set_position(calc_pos)

    def do_bookmark(self, bookmark):
        """
        Add file to bookmarks.

        Usage:
        bookmark [bookmark-file]

        Options:
        [bookmark-file] -- file to be added to bookmarks. Defaults to currently playing file.
        """
        if bookmark.strip() != '':
            utils.bookmark_file(bookmark)
        else:
            utils.bookmark_file(self.get_file_from_player())

    def do_remove_bookmark(self, bookmark):
        """
        Remove currently bookmarked track from bookmarks file.

        Usage:
        remove_bookmark [bookmark-file]

        Options:
        [bookmark-file] -- file to be removed form bookmarks. Defaults to currently playing file.
        """
        if bookmark.strip() != '':
            utils.bookmark_remove(bookmark)
        else:
            utils.bookmark_remove(self.get_file_from_player())

    def do_help(self, arg):
        """
        Display help message for given topic/command if provided. Else print generic help menu.

        Usage:
        help [topic|command]

        Options:
        [topic|command] -- name of topic or command to print
        """
        # noinspection PyUnresolvedReferences
        super(AudioShell, self).do_help(arg)

    def do_move(self,*args):
        """
        Copies the current file to the desired output directory

        Usage:
        move 
        """
        if self.move_path is not None:
            file_path = urllib.unquote(self.player.get_media().get_mrl())[8:]
            dirname = _os.path.basename(_os.path.dirname(file_path))
            basename = _os.path.basename(file_path)
            _os.makedirs(_os.path.abspath(_os.path.join(self.move_path,dirname)),exist_ok=True)
            shutil.copy(file_path,_os.path.abspath(_os.path.join(self.move_path,dirname,basename)))


    # noinspection PyPep8Naming
    def do_EOF(self):
        self.do_quit()

    # internal masking:
    preloop = do_next_track

    # aliased commmands
    alias_h = do_help
    alias_d = do_delete
    alias_e = do_edit
    alias_q = do_quit
    alias_s = do_skip
    alias_b = do_bookmark
    alias_n = do_next_track
    alias_next = do_next_track
    alias_m = do_move
    alias_r = do_remove_bookmark
    alias_remove = do_remove_bookmark

class MetaDataShell(AliasCmdInterpreter, HideNoneDocMix):
    """
    Metadata Shell for interacting with MetaData objects.
    """
    intro = 'Metadata for: '
    prompt = 'Metadata: '
    doc_header = 'Commands (type help/? <topic>):'
    misc_header = 'Reference/help guides (type help/? <topic>):'
    undoc_header = None
    # ruler = '-'

    def __init__(self, mdata: Metadata, *args, parent=None, view=None, **kwargs):
        super(MetaDataShell, self).__init__(*args, **kwargs)
        self.meta = mdata
        self.intro += mdata.file
        self.tmp_dict = dict(mdata.tags)

        # handle nesting shells
        if parent is not None:
            self.prompt = ' -> '.join([parent.prompt.strip()[:30], self.prompt])

        # optional view avaible metadata on shell startup.
        if view is not None:
            self.intro += '\n{}'.format(self.do_view(supress=True))

    # def emptyline(self):
    #     pass

    # noinspection PyUnusedLocal
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
    NUM_TRACKS = 100
    src_dir = os.path.join(os.pardir, 'ref', 'music')
    tmp_dir = os.path.join(os.pardir, 'ref', 'temp')
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


    shell = MetaDataShell(Metadata(rand_track(src_dir, tmp_dir, ext)), view=False)

    # val = input_timeout('this is a test for 5 second timer.', 5)
    # print(val)

    # par = MdataShell(Metadata(rand_track()), view=True)
    # shell = MdataShell(Metadata(rand_track()), view=True, parent=par)
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
