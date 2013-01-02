# Copyright (C) 2012 Jannis Pohlmann <jannis.pohlmann@codethink.co.uk>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import pygit2
import tempfile
import shutil
import unittest

import gitpercs


class RepositoryTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.pygit2_repo = pygit2.init_repository(self.tempdir, False)
        self.create_commits()
        self.repo = gitpercs.repository.Repository(self.pygit2_repo)

    def create_commits(self):
        self.commits = []
        for i in xrange(1, 10):
            parent = self.commits[-1] if self.commits else None

            if self.commits:
                builder = self.pygit2_repo.TreeBuilder(parent.tree)
            else:
                builder = self.pygit2_repo.TreeBuilder()

            text = 'Commit %i' % i
            oid = self.pygit2_repo.write(pygit2.GIT_OBJ_BLOB, text)
            builder.insert('commit.txt', oid, 0100644)
            tree = builder.write()

            signature = pygit2.Signature('gitpercs Unit Tests', 'foo@bar.org')

            oid = self.pygit2_repo.create_commit(
                    'refs/heads/master', signature, signature,
                    text, tree, [parent.oid] if parent else [])

            self.commits.append(self.pygit2_repo[oid])
    
    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_constructor_sets_repository(self):
        self.assertEqual(self.repo.repository, self.pygit2_repo)

    def test_store_returns_the_same_store_when_called_multiple_timeS(self):
        stores = []
        for n in range(0, 10):
            stores.append(self.repo.store(self.commits[0]))
        for n in range(0, 9):
            self.assertEqual(stores[n], stores[n+1])

    def test_store_sets_commits_of_stores_for_different_commits(self):
        for commit in self.commits:
            store = self.repo.store(commit)
            self.assertEqual(store.commit, commit)

    def test_store_resolves_commit_sha1s_into_commit_objects(self):
        for commit in self.commits:
            store = self.repo.store(commit.hex)
            self.assertEqual(store.commit.hex, commit.hex)
