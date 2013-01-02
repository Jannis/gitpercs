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


class StoreTests(unittest.TestCase):

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
        store = self.repo.store(self.commits[0])
        self.assertEqual(store.repository, self.repo)

    def test_constructor_sets_commit(self):
        store = self.repo.store(self.commits[0])
        self.assertEqual(store.commit, self.commits[0])

    def test_using_non_string_as_key_fails(self):
        store = self.repo.store(self.commits[0])
        self.assertRaises(TypeError, store.__setitem__, 123, 'foo')

    def test_inserting_a_single_toplevel_key_works(self):
        store = self.repo.store(self.commits[0])
        store['foo'] = 'bar'
        self.assertEqual(store['foo'], 'bar')

    def test_inserting_two_toplevel_keys_works(self):
        store = self.repo.store(self.commits[0])
        store['foo'] = 'bar'
        store['baz'] = '123'
        self.assertEqual(store['foo'], 'bar')
        self.assertEqual(store['baz'], '123')

    def test_storing_non_alphanumeric_key_fails(self):
        store = self.repo.store(self.commits[0])
        self.assertRaises(ValueError, store.__setitem__, '?+<23=?><///', 'foo')

    def test_storing_hierarchical_keys_works(self):
        store = self.repo.store(self.commits[0])
        store['foo/bar'] = 'baz'
        store['1/2/3'] = '123'
        self.assertEqual(store['foo/bar'], 'baz')
        self.assertEqual(store['1/2/3'], '123')

    def test_storing_keys_with_existing_prefixes_works(self):
        store = self.repo.store(self.commits[0])
        store['foo'] = 'bar'
        store['foo/bar'] = 'baz/ruux'
        store['foo/bar/baz'] = 'ruux/123'
        self.assertEqual(store['foo'], 'bar')
        self.assertEqual(store['foo/bar'], 'baz/ruux')
        self.assertEqual(store['foo/bar/baz'], 'ruux/123')

    def test_multiple_stores_do_not_interfere_with_each_other(self):
        stores = {}
        for commit in self.commits:
            stores[commit] = self.repo.store(commit)
            stores[commit]['foo'] = commit.hex
        for commit in self.commits:
            self.assertEqual(stores[commit]['foo'], commit.hex)
