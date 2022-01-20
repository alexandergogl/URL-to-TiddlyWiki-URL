"""
Alfred script to convert TW5 files to org-mode.
Author: Alexander Gogl
Code based on tworg 0.1.0 by Kyle Johnston
https://pypi.org/project/tworg/
Licence: MIT
Version: 2022-01-20
"""

import os
import re


class Convertor:
    """ Converts a TiddlyWiki Tiddler (.tid) file to an Emacs org-mode file """
    def __init__(self):
        self.metadata = {
            'created': None,
            'creator': None,
            'modified': None,
            'modifier': None,
            'tags': [],
            'title': None,
            'color': None
        }
        self.tid_body = []

    def load(self, f):
        """ Read an iterative object containing TiddlyWiki WikiText strings """
        keywords_regex = '|'.join(self.metadata.keys())
        for line in f:
            # metadata_match = re.match(rf"^({keywords_regex}|type):\s?(.*)", line)
            metadata_match = re.match(
                r"^(created|modified|tags|title|type):\s?(.*)", line)
            if metadata_match:
                key, value = metadata_match.groups()
                if key == 'tags':
                    self.metadata['tags'] = self.__split_tags(value)
                elif key == 'type':
                    pass
                else:
                    self.metadata[key] = value
            else:
                self.tid_body.append(line)

    @property
    def org_header(self):
        """ Return org-formatted header metadata as a list of lines """
        field_mappings = {'title': 'TITLE', 'creator': 'AUTHOR'}
        header = [
            '#+' + field_mappings[x] + ': ' + self.metadata[x]
            for x in field_mappings if self.metadata[x]
        ]
        if self.metadata['tags']:
            header.append("#+TAGS: " + ' '.join(self.metadata['tags']))
        return header

    @property
    def org_body(self):
        """ Represent self.tid_body in org-mode formatting """
        org_body = []
        multiline_tmp = []
        multiline_type = None
        for line in self.tid_body:
            if len(multiline_tmp) > 0:
                if multiline_type == 'code' and line.startswith('```'):
                    multiline_tmp.append('#+END_SRC\n')
                    org_body += multiline_tmp
                    multiline_tmp = []
                elif multiline_type == 'quote' and line.startswith('<<<'):
                    # TODO: What to do with quote attribution? Does org-mode
                    # have an attribute for that?
                    multiline_tmp.append('#+END_QUOTE\n')
                    org_body += multiline_tmp
                    multiline_tmp = []
                else:
                    multiline_tmp.append(line)
            elif line.startswith('```'):
                match = re.match(r'^```(\w*)', line)
                lang = match.groups()[0]
                multiline_tmp.append('#+BEGIN_SRC ' + lang + '\n')
                multiline_type = 'code'
            elif line.startswith('<<<'):
                multiline_tmp.append('#+BEGIN_QUOTE\n')
                multiline_type = 'quote'
            elif line.startswith('!'):
                match = re.match(r'^(!+).+', line).groups()[0]
                org_body.append(
                    self.__org_fmt(line.replace(match, '*' * len(match))))
            elif line.startswith('*'):
                match = re.match(r'^(\*+).+', line).groups()[0]
                org_body.append(
                    self.__org_fmt(
                        line.replace(match, '\t' * (len(match) - 1) + '-')))
            else:
                org_body.append(self.__org_fmt(line))
        return org_body

    def __str__(self):
        return '\n'.join(self.org_header) + '\n' + ''.join(self.org_body)

    def __org_fmt(self, string):
        """ Given a string in WikiText formatting, return it with
        org formatting """
        return (self.__fmt_links(string).replace('`', '~').replace(
            "''", '*').replace('//', '/').replace('__',
                                                  '_').replace('~~', '+'))

    def __fmt_links(self, string):
        """ Given a string, replace any links formatted TiddlyWiki WikiText-style
        with links formatted org-mode style. Return the new string. """
        links = re.findall(r'\[\[([^\]\|]+\|?[^\]]+)?\]\]', string)
        for link in links:
            try:
                desc, target = link.split('|')
            except ValueError:
                desc, target = None, link
            if re.match(r'^(https?:\/\/|mailto:)', target):
                prefix = ''
            elif target.startswith('file://'):
                prefix = ''
                target = target.replace('file://', 'file:')
            else:
                prefix = 'roam:'

            if desc:
                new_link = '[[' + prefix + target + '][' + desc + ']]'
            else:
                new_link = '[[' + prefix + target + '][' + target + ']]'

            string = string.replace('[[' + link + ']]', new_link)
        return string

    def __split_tags(self, tags):
        """ Given a string of tags from a .tid file, split it into a list of
        tags. Tags are separated by spaces, but can also contain spaces if
        they are enclosed by brackets. E.g. an example tag string could look
        like:

        [[Load Testing]] Node.js Docker nginx notes.muumu.us PM2

        This method will convert spaces within a tag to underscores. So, in the
        example above, [[Load Testing]] will become Load_Testing.
        """
        tags_w_spaces = re.findall(r'\[\[([^\]]+)\]\]', tags)
        for tag in tags_w_spaces:
            tags = tags.replace('[[' + tag + ']]', tag.replace(' ', '_'))
        return tags.split(' ')


def run(in_files):
    for fp in in_files:
        # Ignore system tiddlers
        if not fp.split('/')[-1].startswith('$_'):
            print(fp)
            with open(fp, 'r') as f:
                c = Convertor()
                c.load(f)
            if c.metadata['title']:
                with open(
                        os.path.join(
                            '/'.join(fp.split('/')[:-1]) + "/",
                            c.metadata['title'].replace('/', '_') + '.org'),
                        'w') as f:
                    f.write(c.__str__())


# Multiple files are separated by tabs
in_files = "{query}".split('	')
run(in_files)
