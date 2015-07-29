from __future__ import unicode_literals
from ben10.filesystem import (CanonicalPath, CreateDirectory, CreateFile, DeleteDirectory,
    DeleteFile, GetFileContents)
from gitit.git import (BranchAlreadyExistsError, DirtyRepositoryError, Git, GitExecuteError,
    GitRefDoesNotExistError, NotCurrentlyInAnyBranchError, RepositoryAccessError,
    SSHServerCantBeFoundError, TargetDirAlreadyExistsError)
import os
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testCall(self, git):
        assert git.__call__ == git.Execute


    def testFetch(self, git, embed_data):
        # Create a remote branch
        clone_1 = git.cloned_remote
        assert git.GetTags(clone_1) == set()

        # Create another clone of the repository
        clone_2 = embed_data['cloned_remote_2']
        git.Clone(git.remote, clone_2)

        # Use second clone to push a tag
        git.CreateTag(clone_2, 'my_tag')
        git.Push(clone_2, tags=True)

        # We still don't see that tag in first clone
        assert git.GetTags(clone_1) == set()

        # After a fetch, we should see it
        git.Fetch(clone_1)
        assert git.GetTags(clone_1) == {'my_tag'}


    def testPrune(self, git, embed_data):
        # Create a remote branch
        clone_1 = git.cloned_remote
        git.CreateRemoteBranch(clone_1, 'master', 'remote_branch')
        assert git.ListBranches(clone_1, remote=True) == ['master', 'remote_branch']

        # Create another clone of the repository
        clone_2 = embed_data['cloned_remote_2']
        git.Clone(git.remote, clone_2)

        # Use second clone to delete remote branch
        git.DeleteRemoteBranch(clone_2, 'remote_branch')
        assert git.ListBranches(clone_2, remote=True) == ['master']

        # First branch should still be listed as a remote in clone_1
        assert git.ListBranches(clone_1, remote=True) == ['master', 'remote_branch']

        # Pruning should fix this
        pruned_branches = git.RemotePrune(clone_1)
        assert pruned_branches == {'remote_branch'}
        assert git.ListBranches(clone_1, remote=True) == ['master']


    def testExists(self, git, embed_data):
        assert (
            git.Exists(os.path.abspath(embed_data['remote.git']))
            == True
        )
        assert (
            git.Exists(os.path.abspath(embed_data['badremote.git']))
            == False
        )


    def testLog(self, git):
        working_dir = git.cloned_remote

        r = git.Log(working_dir)
        assert r == [
            'commit 35ff01222f4c79baeccaf98ece11bebff9bec01c',
            'Author: Diogo de Campos <campos@esss.com.br>',
            'Date:   2012-07-17 13:33:56 -0300',
            '',
            '     "Added new_file"',
            '',
            'commit 2a5f12d2ba5dd9fd52df8896e6b18b214db29225',
            'Author: Diogo de Campos <campos@esss.com.br>',
            'Date:   2012-07-17 10:37:53 -0300',
            '',
            '    Added charlie.txt',
            '',
            'commit 59b4124603cbb614437a5896d7a028e9df0df276',
            'Author: Alexandre Andrade <ama@esss.com.br>',
            'Date:   2012-02-09 14:51:53 -0200',
            '',
            '    Adding alpha and bravo files',
        ]

        r = git.Log(working_dir, ('--oneline',))
        assert r == [
            '35ff012  "Added new_file"',
            '2a5f12d Added charlie.txt',
            '59b4124 Adding alpha and bravo files',
        ]


    def testShow(self, git):
        working_dir = git.cloned_remote

        r = git.Show(working_dir, '2a5f12d2ba5dd9fd52df8896e6b18b214db29225')
        assert (
            r
            == 'commit 2a5f12d2ba5dd9fd52df8896e6b18b214db29225\n'
            'Author: Diogo de Campos <campos@esss.com.br>\n'
            'Date:   2012-07-17 10:37:53 -0300\n\n'
            '    Added charlie.txt\n\ndiff --git a/charlie.txt b/charlie.txt\n'
            'new file mode 100644\nindex 0000000..197d36d\n--- /dev/null\n+++ b/charlie.txt\n'
            '@@ -0,0 +1 @@\n+This is charlie'
        )
        r = git.Show(working_dir, '2a5f12d2ba5dd9fd52df8896e6b18b214db29225', diff_only=True)
        assert (
            r
            == 'diff --git a/charlie.txt b/charlie.txt\n'
            'new file mode 100644\nindex 0000000..197d36d\n'
            '--- /dev/null\n+++ b/charlie.txt\n@@ -0,0 +1 @@\n'
            '+This is charlie'
        )


    def testStatus(self, git):
        working_dir = git.cloned_remote

        r = git.Status(working_dir, flat_output=False)
        assert len(r) == 1
        assert r[0] in (
            '## master...origin/master',
            '## master',
        )

        CreateFile(working_dir + '/zulu.txt', 'zulu')

        r = git.Status(working_dir, flat_output=False)
        assert len(r) == 2
        assert r[0] in (
            '## master...origin/master',
            '## master',
        )
        assert r[1] == '?? zulu.txt'


    def testReset(self, git):
        working_dir = git.cloned_remote

        r = git.Status(working_dir)
        assert len(r.splitlines()) == 1  # just the branch header

        CreateFile(working_dir + '/alpha.txt', 'Changed!')

        r = git.Status(working_dir)
        assert len(r.splitlines()) == 2  # one modified file

        git.Reset(working_dir)

        r = git.Status(working_dir)
        assert len(r.splitlines()) == 1  # just the branch header


    @pytest.mark.slow
    def testClone(self, embed_data, git):
        # Dir does not exist yet
        working_dir = embed_data['my_working_dir']
        assert not os.path.isdir(working_dir)

        # First clone should be easy
        git.Clone(embed_data['remote.git'], working_dir)
        assert os.path.isdir(working_dir)

        # Trying to clone again should raise an error
        with pytest.raises(TargetDirAlreadyExistsError):
            git.Clone(embed_data['remote.git'], working_dir)

        # Unless we allow it
        git.Clone(embed_data['remote.git'], working_dir, update_if_already_exists=True)

        from ben10.filesystem import Cwd
        with Cwd(embed_data['.']):
            # Using a bad ssh server should also raise an error
            with pytest.raises(SSHServerCantBeFoundError):
                git.Clone('git@badsshserver:foo', 'any_dir')

            # Repository that does not exist should also raise an error
            with pytest.raises(RepositoryAccessError):
                url = 'https://eden.esss.com.br/INEXISTENT'
                git.Clone(url, 'any_dir')


    def testCloneBranch(self, embed_data, git):
        '''
        Tests the branch selection for Clone method.

        REMARKS: Clone method must remember to clear all methods' cache.
        '''
        complex_dir = embed_data['complex']

        # By default, checkout the branch configured in the server, usually "master"
        git.Clone(embed_data['complex.git'], complex_dir)
        assert git.GetCurrentBranch(complex_dir) == 'master'
        DeleteDirectory(complex_dir)

        # Clone again, from scratch, in a specific branch.
        git.Clone(embed_data['complex.git'], complex_dir, branch='branch_1')
        assert git.GetCurrentBranch(complex_dir) == 'branch_1'

        # Now no clone is done, but the branch is propertly switched.
        git.Clone(embed_data['complex.git'], complex_dir, update_if_already_exists=True, branch='master')
        assert git.GetCurrentBranch(complex_dir) == 'master'


    def testGetCommitRepr(self, git):
        assert (
            git.GetCommitRepr(git.cloned_remote, short=False, date=False, summary=False)
            == '35ff01222f4c79baeccaf98ece11bebff9bec01c'
        )
        assert (
            git.GetCommitRepr(git.cloned_remote, short=True, date=False, summary=False)
            == '35ff012'
        )
        assert (
            git.GetCommitRepr(git.cloned_remote, ref='HEAD~1', short=True, date=False, summary=False)
            == '2a5f12d'
        )
        assert (
            git.GetCommitRepr(git.cloned_remote, short=False, date=True, summary=False)
            == '35ff01222f4c79baeccaf98ece11bebff9bec01c [2012-07-17 13:33:56 -0300]'
        )
        assert (
            git.GetCommitRepr(git.cloned_remote, short=False, date=False, summary=True)
            == '35ff01222f4c79baeccaf98ece11bebff9bec01c  "Added new_file"'
        )
        assert (
            git.GetCommitRepr(git.cloned_remote, short=True, date=True, summary=True)
            == '35ff012  "Added new_file" [2012-07-17 13:33:56 -0300]'
        )


    def testGetCommitCount(self, git):
        assert git.GetCommitCount(git.cloned_remote) == 3
        assert git.GetCommitCount(git.cloned_remote, 'HEAD~1') == 2


    def testDiff(self, git):
        assert (
            git.Diff(
                git.cloned_remote,
                '59b4124603cbb614437a5896d7a028e9df0df276',
                '2a5f12d2ba5dd9fd52df8896e6b18b214db29225'
            )
            == 'diff --git a/charlie.txt b/charlie.txt\n'
            'new file mode 100644\n'
            'index 0000000..197d36d\n'
            '--- /dev/null\n'
            '+++ b/charlie.txt\n'
            '@@ -0,0 +1 @@\n'
            '+This is charlie'
        )


    def testAuthor(self, git):
        assert (
            git.GetAuthor(git.cloned_remote, '59b4124603cbb614437a5896d7a028e9df0df276')
            == 'Alexandre Andrade'
        )
        assert (
            git.GetAuthor(git.cloned_remote, '2a5f12d2ba5dd9fd52df8896e6b18b214db29225')
            == 'Diogo de Campos'
        )


    def testAuthorEmail(self, git):
        assert (
            git.GetAuthorEmail(git.cloned_remote, '59b4124603cbb614437a5896d7a028e9df0df276')
            == 'ama@esss.com.br'
        )
        assert (
            git.GetAuthorEmail(git.cloned_remote, '2a5f12d2ba5dd9fd52df8896e6b18b214db29225')
            == 'campos@esss.com.br'
        )


    def testGetMessage(self, git):
        assert (
            git.GetMessage(git.cloned_remote, '59b4124603cbb614437a5896d7a028e9df0df276')
            == 'Adding alpha and bravo files'
        )
        assert (
            git.GetMessage(git.cloned_remote, '2a5f12d2ba5dd9fd52df8896e6b18b214db29225')
            == 'Added charlie.txt'
        )


    def testChangedPaths(self, git):
        assert git.GetChangedPaths(git.cloned_remote, 'HEAD') == set(['new_file'])
        assert git.GetChangedPaths(git.cloned_remote, 'HEAD~1') == set(['charlie.txt'])
        assert git.GetChangedPaths(git.cloned_remote, 'HEAD~2') == set(['alpha.txt', 'bravo.txt'])
        assert git.GetChangedPaths(git.cloned_remote, 'HEAD', 'HEAD~2') == set(['new_file', 'charlie.txt'])


    def testCommitStats(self, git):
        assert (
            git.GetCommitStats(git.cloned_remote, '59b4124603cbb614437a5896d7a028e9df0df276')
            == (2, 2, 0)
        )

        assert (
            git.GetCommitStats(git.cloned_remote, '2a5f12d2ba5dd9fd52df8896e6b18b214db29225')
            == (1, 1, 0)
        )


    def testCheckout(self, git, embed_data):
        # Charlie.txt exists
        assert os.path.isfile(embed_data['cloned_remote/charlie.txt'])

        # If we checkout a previous revision, it should be gone
        git.Checkout(git.cloned_remote, '59b4124603cbb614437a5896d7a028e9df0df276')
        assert not os.path.isfile(embed_data['cloned_remote/charlie.txt'])

        # Back to master
        git.Checkout(git.cloned_remote, 'master')
        assert os.path.isfile(embed_data['cloned_remote/charlie.txt'])

        # Trying to checkout a bad revision
        with pytest.raises(GitRefDoesNotExistError):
            git.Checkout(git.cloned_remote, '999999')


    def testIsDirty(self, git, embed_data):
        assert git.IsDirty(git.cloned_remote) == False

        # Creating a new file should not leave the repo dirty
        new_file = embed_data['cloned_remote/some_new_file.txt']
        CreateFile(new_file, contents='new_file')
        assert git.IsDirty(git.cloned_remote) == False
        DeleteFile(new_file)

        # Modifying a file should leave it dirty
        git.ClearCache()
        CreateFile(embed_data['cloned_remote/alpha.txt'], contents='modified alpha')
        assert git.IsDirty(git.cloned_remote) == True


    def testGetRevisions(self, git, embed_data):
        cloned_complex = embed_data['cloned_complex']
        git.Clone(embed_data['complex.git'], cloned_complex)

        assert git.GetRevisions(
            cloned_complex,
            r1='6952d5c4c89bc230288fbc4559f8e659ee0f9c6a',
            r2='f533d1d30dd042b073d30becca7deb7b901f54e7',
            ignore_merges=False
        ) == [
            'efa64656ba24edef6b9213e200aca022b9798059',
            '5ced71f1c70e85dc92aa75c01e1d60b4cf99d564',
            '472892a3e00dd6f9922bdb2296f38c90085bc435',
            '952f1f194cf91ae064203e22a8de2bf0f49a069f',
            '42b2140af9b6e6b078344d3db231e75bdc6124b7',
            'f533d1d30dd042b073d30becca7deb7b901f54e7',
        ]

        # Ignoring merges
        assert git.GetRevisions(
            cloned_complex,
            r1='6952d5c4c89bc230288fbc4559f8e659ee0f9c6a',
            r2='f533d1d30dd042b073d30becca7deb7b901f54e7',
            ignore_merges=True
        ) == [
            'efa64656ba24edef6b9213e200aca022b9798059',
            '5ced71f1c70e85dc92aa75c01e1d60b4cf99d564',
            '472892a3e00dd6f9922bdb2296f38c90085bc435',
            '952f1f194cf91ae064203e22a8de2bf0f49a069f',
            'f533d1d30dd042b073d30becca7deb7b901f54e7'
        ]

        # When r1 is 0000000000000000000000000000000000000000, the ref must be passed
        with pytest.raises(AssertionError):
            git.GetRevisions(
                cloned_complex,
                r1='0000000000000000000000000000000000000000',
                r2='f533d1d30dd042b073d30becca7deb7b901f54e7',
            )

        # If first revision is empty, list all commits reachable by r2, not reachable by any other
        # head
        assert git.GetRevisions(
            cloned_complex,
            r1='0000000000000000000000000000000000000000',
            r2='f533d1d30dd042b073d30becca7deb7b901f54e7',
            ref='refs/heads/master',
            ignore_merges=False
        ) == [
            '6952d5c4c89bc230288fbc4559f8e659ee0f9c6a',
            'efa64656ba24edef6b9213e200aca022b9798059',
            '5ced71f1c70e85dc92aa75c01e1d60b4cf99d564',
            '472892a3e00dd6f9922bdb2296f38c90085bc435',
            '952f1f194cf91ae064203e22a8de2bf0f49a069f',
            '42b2140af9b6e6b078344d3db231e75bdc6124b7',
            'f533d1d30dd042b073d30becca7deb7b901f54e7',
        ]

        # If last revision is empty, a branch was deleted, no commits here.
        assert git.GetRevisions(
            cloned_complex,
            r1='f533d1d30dd042b073d30becca7deb7b901f54e7',
            r2='0000000000000000000000000000000000000000',
            ref='refs/heads/master',
            ignore_merges=False
        ) == []


    def testAddCommitPush(self, git, embed_data):
        # We start out with 2 commits
        assert git.GetCommitCount(git.cloned_remote) == 3

        # Add something and check the new count
        test_file = embed_data['cloned_remote/test_file']
        CreateFile(test_file, contents='test_file')

        git.Add(git.cloned_remote, 'test_file')
        git.Commit(git.cloned_remote, commit_message='Added test_file')
        git.Push(git.cloned_remote)

        assert git.GetCommitCount(git.cloned_remote) == 4

        assert (
            git.GetCommitRepr(git.cloned_remote, commit_hash=False, summary=True)
            == 'Added test_file'
        )


    def testGetCurrentBranch(self, git):
        # Initial test
        assert git.GetCurrentBranch(git.cloned_remote) == 'master'

        # Create a new branch and check again
        git.ClearCache()
        git.CreateLocalBranch(git.cloned_remote, 'new_branch')
        assert git.GetCurrentBranch(git.cloned_remote) == 'new_branch'

        # Stay in headless state
        git.ClearCache()
        git.Checkout(git.cloned_remote, '59b4124603cbb614437a5896d7a028e9df0df276')
        with pytest.raises(NotCurrentlyInAnyBranchError):
            git.GetCurrentBranch(git.cloned_remote)


    def testGetRemoteUrl(self, git, embed_data):
        assert (
            CanonicalPath(git.GetRemoteUrl(git.cloned_remote))
            == CanonicalPath(os.path.abspath(embed_data['remote.git']))
        )


    def testRemote(self, git):
        repo_path = git.cloned_remote
        new_name = 'new'
        new_url = 'http://new_remote/git/project.git'

        # We receive a GitExecuteError if we ask for the URL of a unknown remote.
        with pytest.raises(GitExecuteError):
            git.GetRemoteUrl(repo_path, new_name)
        assert set(git.ListRemotes(repo_path)) == set(['origin'])
        assert git.RemoteExists(repo_path, new_name) == False

        git.AddRemote(repo_path, new_name, new_url),

        assert git.RemoteExists(repo_path, new_name) == True
        assert set(git.ListRemotes(repo_path)) == set(['origin', new_name])
        assert CanonicalPath(git.GetRemoteUrl(repo_path, new_name)) == CanonicalPath(new_url)


    def testIsValidRepository(self, git, embed_data):
        assert git.IsValidRepository(git.cloned_remote) == True
        assert git.IsValidRepository(embed_data.GetDataDirectory()) == False


    def testGetWorkingDir(self, git, embed_data, tmpdir):
        assert git.GetWorkingDir(git.cloned_remote) == os.path.abspath(git.cloned_remote)

        charlie_dir = git.cloned_remote + '/alpha/bravo/charlie'
        CreateDirectory(charlie_dir)
        assert git.GetWorkingDir(charlie_dir) == os.path.abspath(git.cloned_remote)

        assert git.GetWorkingDir(unicode(tmpdir.mkdir('not_a_git_dir'))) is None


    def testListLocalBranches(self, git, embed_data):
        cloned_complex = embed_data['cloned_complex']
        git.Clone(embed_data['complex.git'], cloned_complex)
        git.Checkout(cloned_complex, 'branch_1')

        assert set(git.ListBranches(cloned_complex)) == set(['master', 'branch_1'])

        git.CreateLocalBranch(
            cloned_complex,
            branch_name='branch-with-hyphens'
        )
        assert (
            set(git.ListBranches(cloned_complex))
            == set(['master', 'branch_1', 'branch-with-hyphens'])
        )


    def testListRemoteBranches(self, git, embed_data):
        cloned_complex = embed_data['cloned_complex']
        git.Clone(embed_data['complex.git'], cloned_complex)

        assert set(git.ListBranches(cloned_complex, remote=True)) == set(['master', 'branch_1'])

        git.CreateRemoteBranch(
            cloned_complex,
            original_branch='master',
            branch_name='branch-with-hyphens'
        )
        assert (
            set(git.ListBranches(cloned_complex, remote=True))
            == set(['master', 'branch_1', 'branch-with-hyphens'])
        )


    def testClean(self, git, embed_data):
        # Create some file and see that they are cleaned
        echo = embed_data['cloned_remote/echo.txt']
        foxtrot = embed_data['cloned_remote/foxtrot.txt']

        CreateFile(echo, contents='echo')
        CreateFile(foxtrot, contents='foxtrot')

        # Create .gitignore
        CreateFile(embed_data['cloned_remote/.gitignore'], contents='echo.txt')

        removed_files = git.Clean(git.cloned_remote)
        assert removed_files == ['echo.txt']

        assert not os.path.isfile(echo)
        assert os.path.isfile(foxtrot)


    def testGetDirtyFiles(self, git, embed_data):
        assert git.GetDirtyFiles(git.cloned_remote) == []

        # New files and directories are not considered dirty
        CreateFile(embed_data['cloned_remote/some_file'], contents='')
        CreateDirectory(embed_data['cloned_remote/some_dir'])
        assert git.GetDirtyFiles(git.cloned_remote) == []

        # Modify alpha.txt
        git.ClearCache()
        CreateFile(embed_data['cloned_remote/alpha.txt'], contents='')
        assert set(git.GetDirtyFiles(git.cloned_remote)) == set([('M', 'alpha.txt')])


    def testTags(self, git):
        # Check local clone before/after creating tag
        assert git.GetTags(git.cloned_remote) == set([])
        git.CreateTag(git.cloned_remote, name='tag1', message='tag_message\nother line')
        assert git.GetTags(git.cloned_remote) == set(['tag1'])

        # Testing with specific commits
        assert git.GetTags(git.cloned_remote, commit='HEAD') == set(['tag1'])
        assert git.GetTags(git.cloned_remote, commit='HEAD~1') == set([])

        # Check remote before/after push
        assert git.GetTags(git.remote) == set([])
        git.Push(git.cloned_remote, tags=True)
        assert git.GetTags(git.remote) == set(['tag1'])

        # Testing GetTagMessage
        assert git.GetTagMessage(git.cloned_remote, tag_name='tag1') == 'tag_message\nother line'


    def testLocalBranch(self, git, embed_data):
        # Initial test
        assert git.GetCurrentBranch(git.cloned_remote) == 'master'

        # Create a new branch and check again
        git.ClearCache()
        git.CreateLocalBranch(git.cloned_remote, 'new_branch')
        assert git.GetCurrentBranch(git.cloned_remote) == 'new_branch'

        # Try to create a branch that already exists
        with pytest.raises(BranchAlreadyExistsError):
            git.CreateLocalBranch(git.cloned_remote, 'new_branch')

        # Try to create a branch while dirty
        git.ClearCache()
        CreateFile(embed_data['cloned_remote/alpha.txt'], contents='')
        with pytest.raises(DirtyRepositoryError):
            git.CreateLocalBranch(git.cloned_remote, 'other_new_branch')

        # We are still in new_branch, but we should be able to delete it
        git.DeleteLocalBranch(git.cloned_remote, 'new_branch')

        # We can't go back to it
        with pytest.raises(GitRefDoesNotExistError):
            git.Checkout(git.cloned_remote, 'new_branch')


    @pytest.mark.slow
    def testStash(self, git):
        assert not git.IsDirty(git.cloned_remote)

        # Modify alpha.txt
        git.ClearCache()
        alpha_txt = git.cloned_remote + '/alpha.txt'
        CreateFile(alpha_txt, 'Changing alpha.txt\n')
        assert git.IsDirty(git.cloned_remote)

        # Stash changes so we have alpha.txt with its original content.
        git.ClearCache()
        git.Stash(git.cloned_remote)
        assert not git.IsDirty(git.cloned_remote)
        assert GetFileContents(alpha_txt) == 'alpha\n'

        # Pop changes so we have alpha.txt with our modification
        git.ClearCache()
        git.StashPop(git.cloned_remote)
        assert git.IsDirty(git.cloned_remote)
        assert GetFileContents(alpha_txt) == 'Changing alpha.txt\n'


    def testRemoteBranch(self, git):
        # Initial test
        assert git.ListBranches(git.cloned_remote, remote=True) == ['master']

        # Create new remote branch from master
        git.CreateRemoteBranch(git.cloned_remote, 'master', 'new_branch')
        assert git.ListBranches(git.cloned_remote, remote=True) == ['master', 'new_branch']

        # Create new remote branch from new_branch
        git.CreateRemoteBranch(git.cloned_remote, 'new_branch', 'new_branch_2')
        assert (
            git.ListBranches(git.cloned_remote, remote=True)
            == ['master', 'new_branch', 'new_branch_2']
        )

        # Delete remote branch and check again
        git.DeleteRemoteBranch(git.cloned_remote, 'new_branch')
        assert (
            git.ListBranches(git.cloned_remote, remote=True)
            == ['master', 'new_branch_2']
        )



#===================================================================================================
# git
#===================================================================================================
@pytest.fixture(scope='function')
def git(embed_data):
    '''
    Git fixture that gives us an instance of git, plus some configurations for test data
    repositories
    '''
    result = Git()
    result.remote = embed_data['remote.git']
    result.cloned_remote = embed_data['cloned_remote']
    result.Clone(result.remote, result.cloned_remote)
    result.Execute('config --local user.name "test"', result.cloned_remote)
    result.Execute('config --local user.email "test@ben10.com"', result.cloned_remote)
    result.Execute('config --local log.date iso', result.cloned_remote)
    result.Execute('config --local commit.date iso', result.cloned_remote)
    return result
