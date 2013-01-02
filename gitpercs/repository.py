#!/usr/bin/env python
#
# Copyright (C) 2012 Jannis Pohlmann <jannis.pohlmann@codethink.co.uk>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import pygit2

import gitpercs


class Repository(object):

    '''Represents a Git repository with per-commit key/value stores.'''
    
    def __init__(self, repository):
        self.repository = repository
        self._stores = {}

    def store(self, rev):
        '''Returns a key/value store for a pygit2 commit object or name.
        
        Any repository object is guaranteed to always return the same
        store object for a commit SHA1. If, however, symbolic refs are
        passed, they may over time resolve to different commit SHA1s and
        thus yield different store objects.

        '''

        # resolve the rev parameter into a commit object
        if isinstance(rev, pygit2.Commit):
            commit = rev
        else:
            commit = self.repository.revparse_single(rev)

        # create the store on demand and return it
        if not commit in self._stores:
            self._stores[commit] = gitpercs.store.Store(self, commit)
        return self._stores[commit]
