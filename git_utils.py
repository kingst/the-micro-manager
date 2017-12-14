#!/usr/bin/env python

import binascii

from git import Commit
from git import Repo

ro_repo = Repo('../karma')

for commit in Commit.list_items(ro_repo, ro_repo.head):
    print(commit.author.email + ' ' + commit.author.name)
    print(commit.committed_datetime)
    print(binascii.hexlify(commit.binsha))
    print(commit.message + "\n")
