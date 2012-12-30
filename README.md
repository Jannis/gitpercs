gitpercs
========

gitpercs is a versioned per-commit key/value store for Git. It is
written in Python to allow easy integration in Python-based (web)
applications.

The idea behind gitpercs
------------------------

What makes gitpercs interesting? At a high level perspective, it is a
highly efficient way to annotate commits with arbitrary information
such as meta data or data used for caching.

It was born from a mild sort of enlightenment we had when optimising a
web application that rendered content from a Git repository: assume the
data used to generate the pages of a website is represented as files a
Git repository (e.g. in Markdown, JSON or YAML format). A non-optimised
web application would load the data and render it as HTML, possible
involving a template engine, for every single request. There are various
ways to improve this. The ultimate improvement, however, is what
gitpercs aims to help with: caching the full renderings of all static
pages for the entire website for each commit (where a commit represents
a version of the website content).

This is just one scenario where a per-commit key/value store can be
useful. Another example are source code repositories where every single
commit can be annotated with computationally intensive meta data such
as licenses being used etc. gitpercs can be used to store and retrieve
this data in a highly performant way. Even better: by maintaining this
key/value store in the same repository as the commits themselves rather
than a separate repository, it is preserved as repositories are copied
and moved around on the internet.

Features
--------

* Annotate Git commits with arbitrary key/value data within the same
  Git repository.

* Preserve data across repository clones by using Git's object store,
  trees, commits and refs.

* Versioning by committing key/value changes to refs/heads/gitpercs.

* High performance thanks to pygit2.

Copyright
---------

This software is

Copyright (c) 2012 Jannis Pohlmann <jannis.pohlmann@codethink.co.uk>

and is licensed under MPLv2. For more information about this license see
the COPYING file.
