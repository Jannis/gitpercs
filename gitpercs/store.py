#!/usr/bin/env python
#
# Copyright (C) 2012 Jannis Pohlmann <jannis.pohlmann@codethink.co.uk>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import pygit2
import re

import gitpercs


class Store(object):

    '''A per-commit key/value store.
    
    Store objects take a repository and a commit and allow users to
    store and read arbitrary key/value data for this commit.

    Key names are restricted to a very basic format: slashes mixed with
    alphanumeric characters, dashes, underscores and colons. Slashes provide
    a way to group key/value pairs logically. Leading and trailing slashes as
    well as empty "path segments" are stripped, so "/foo//bar/" is the same
    as "foo/bar".

    Any data can be passed in as values as long as it can be converted to a
    string representation that is meaningful.

    Internally, the key/value pairs are stored in a special Git ref called
    "ref/heads/percs". This ref points to a Git tree that is organised as
    follows:

        <first SHA1>/
            foo/
                bar/
                    .value
                baz/
                    .value
            bar/
                baz/
                    .value 
        <second SHA1>/
            123/
                456/
                    .value

    The path of each ".value" file represents the commit SHA1 and key. The
    ".value" files themselves store the corresponding key/value data. This
    could in theory be simplified by avoiding sub-trees whenever possible
    but this would require reorganising the trees when writing new values
    into an already existing path prefix. Using ".value" files allows to
    store keys like "foo" and "foo/bar" without having to transition from
    a file "foo" to a directory "foo" with a ".value" and a "bar" file.

    The key/value pairs for all commits in a repository can be listed via

        git ls-tree -r --name-only refs/heads/percs | sed 's;/.value;;g'

    Store objects do not cache any of the key/value pairs for faster reading
    as they may change at any point in time.

    '''
    
    def __init__(self, repository, commit):
        '''Creates a Store object for a repository and a commit.'''

        self.repository = repository
        self.commit = commit
    
    def __setitem__(self, key, value):
        '''Stores a value for a key.'''

        # verify the key is not malformatted
        self._verify_key_format(key)

        # try to resolve refs/heads/percs into a pygit2 reference
        ref = self._ref()

        # split key into path segments
        segments = self._path_segments(key)

        # try to resolve Git trees for the key path as deep as we can
        # and store them along with the segments
        trees = self._segment_trees(segments, ref)

        # prepend the existing refs/heads/percs tree to the segment/tree
        # pairs. this may seem odd but all it does is ensure that the new
        # refs/heads/percs tree is a modification of the existing
        # key/value store rather than a replacement when writing it back
        # to the repository
        trees = [(ref, ref.tree if ref else None)] + trees

        # create a new Git tree for the .value file and add the .value
        # file to it with the data converted into a string
        builder = self.repository.repository.TreeBuilder()
        oid = self.repository.repository.write(pygit2.GIT_OBJ_BLOB, str(value))
        builder.insert('.value', oid, 0100644)
        oid = builder.write()
        trees[-1] = (trees[-1][0], self.repository.repository[oid])

        # propagate the tree changes up to the toplevel tree. this will
        # create intermediate Git trees or update them if they already
        # exist
        trees = self._propagate_change(trees)

        # commit the changes to refs/heads/percs
        # FIXME we may want to use something like refs/percs/... here
        # FIXME the author should probably be taken from the git config
        path = os.path.join(self.commit.hex, key)
        author = committer = pygit2.Signature('gitpercs', 'gitpercs@localhost')
        message = 'Update %s' % path
        self.repository.repository.create_commit(
                self._refname(), author, committer, message,
                trees[0][1].oid, [ref.oid] if ref else [])

    def __getitem__(self, key):
        '''Looks up the value for a key.
        
        Raises a KeyError if the key does not exist in the store.
        
        '''

        # try to resolve refs/heads/percs into a pygit2 reference
        ref = self._ref()

        # split the key up into path segments
        segments = self._path_segments(key)

        # try to resolve the trees for all parts of the key path
        trees = self._segment_trees(segments, ref)

        # obtain the tree entry for the .value file in corresponding
        # to the key to be looked up
        entry = trees[-1][1]['.value']

        # obtain the entry blob from Git and return its data
        return self.repository.repository[entry.oid].data
        
    def _verify_key_format(self, key):
        if not isinstance(key, basestring):
            raise TypeError('Key "%s" is not a string' % key)
        pattern = '^[a-z0-9-_/:]+$'
        if not re.match(pattern, key, re.IGNORECASE):
            raise ValueError(
                    'Key "%s" does not match format "%s"' % (key, pattern))

    def _refname(self):
        return 'refs/heads/percs'

    def _ref(self):
        try:
            ref = self.repository.repository.lookup_reference(self._refname())
            return self.repository.repository[ref.oid]
        except KeyError:
            return None

    def _path_segments(self, path):
        return [self.commit.hex] + [x for x in path.split('/') if x]

    def _segment_trees(self, segments, commit):
        trees = []
        tree = commit.tree if commit else None
        for segment in segments:
            segment_tree = None
            if tree:
                try:
                    entry = tree[segment]
                    segment_tree = self.repository.repository[entry.oid]
                except (KeyError, pygit2.GitError):
                    pass
            trees.append((segment, segment_tree))
            tree = segment_tree
        return trees

    def _propagate_change(self, trees):
        for n in reversed(range(len(trees))):
            segment, tree = trees[n]
            if not tree:
                builder = self.repository.repository.TreeBuilder()
                if n < len(trees)-1:
                    child_segment, child_tree = trees[n+1]
                    builder.insert(child_segment, child_tree.oid, 0040000)
                oid = builder.write()
                tree = self.repository.repository[oid]
                trees[n] = (segment, tree)
            else:
                builder = self.repository.repository.TreeBuilder(tree)
                if n < len(trees)-1:
                    child_segment, child_tree = trees[n+1]
                    builder.insert(child_segment, child_tree.oid, 0040000)
                    oid = builder.write()
                    tree = self.repository.repository[oid]
                    trees[n] = (segment, tree)
        return trees
