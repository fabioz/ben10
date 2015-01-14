from __future__ import unicode_literals
from ben10.foundation.memoize import Memoize
from ben10.foundation.singleton import Singleton
import os
import posixpath



#===================================================================================================
# Git
#===================================================================================================
class Git(Singleton):
    '''
    Python interface to git commands. Uses git executable available in the current environment.

    Some functions use Memoize for cache, and assume that files in a repository will not change
    during the lifetime of a Git instance.

    If you want to ensure that no cache is used, create a new instance of Git whenever necessary,

    If you wish to use this cache and share it globally, use Git.GetSingleton. You can also push a
    new singleton whenever you know that changes were made to local files, as a way to invalidate
    this cache
    '''
    # Expected output encoding from git commands
    OUTPUT_ENCODING = 'UTF-8'

    # Handle encode errors with 'replace'. We assume UTF-8 for all files, but we don't want git
    # commands to fail because someone is using the wrong encoding.
    OUTPUT_ENCODING_ERRORS = 'replace'

    # Constants for common refs
    ZERO_REVISION = '0' * 40
    REFS_HEADS = 'refs/heads/'
    REFS_TAGS = 'refs/tags/'


    def ClearCache(self):
        '''
        Clears Memoize cache from all our methods
        '''
        self.Log.ClearCache(self)
        self.GetCurrentBranch.ClearCache(self)
        self.GetCurrentRef.ClearCache(self)
        self.GetDirtyFiles.ClearCache(self)


    def Execute(
        self,
        command_line,
        repo_path=None,
        flat_output=False,
        **kwargs
        ):
        '''
        Executes a git command line in the given repository.

        :param list(unicode)|unicode command_line:
            List of commands to execute, not including 'git' as the first.

        :param unicode|None repo_path:
            Path to repository where the command will be executed (without .git)

            If None, runs command in current directory (useful for clone, for example)

        :param bool flat_output:
            If True, joins the output lines with '\n' (returning a single string)

        :param kwargs:
            .. seealso:: ben10.execute.Execute

        :returns list(unicode)|unicode:
            List of lines output from git command, or the complete output if parameter flat_output
            is True

        :raises GitExecuteError:
            If the git executable returns an error code
        '''
        if isinstance(command_line, unicode):
            import shlex
            command_line = shlex.split(command_line)
        command_line = ['git'] + list(command_line)

        clean_eol = kwargs.pop('clean_eol', True)
        output_encoding = kwargs.pop('output_encoding', self.OUTPUT_ENCODING)
        output_encoding_errors = kwargs.pop('output_encoding_errors', self.OUTPUT_ENCODING_ERRORS)

        from ben10.execute import Execute2
        output, retcode = Execute2(
            command_line,
            cwd=repo_path,
            clean_eol=clean_eol,
            output_encoding=output_encoding,
            output_encoding_errors=output_encoding_errors,
            **kwargs
        )

        # TODO: EDEN-245: Refactor System.Execute and derivates (git, scons, etc)
        if clean_eol:
            output_joiner = '\n'
        else:
            output_joiner = ''

        if retcode != 0:
            raise GitExecuteError(' '.join(command_line), retcode, output_joiner.join(output))

        if flat_output:
            return output_joiner.join(output)

        return output

    # call shortcut
    __call__ = Execute

    def Exists(self, repository_url):
        '''
        Checks if a remote Git repository exists

        :param unicode repository_url:

        :rtype: bool
        :returns:
            True if the repository exists
        '''
        try:
            self.Execute(['ls-remote', repository_url])
            return True
        except GitExecuteError, e:
            if e.retcode == 128:
                return False
            raise


    def Clone(
        self,
        repository_url,
        target_dir,
        update_if_already_exists=False,
        no_checkout=False,
        output_callback=None,
        ):
        '''
        Clone a repository_url

        :param unicode repository_url:
            The path to the repository_url.
            e.g. git@yoda:something.git, X:/.git_repos/something.git

        :param unicode target_dir:
            Target path to clone the repository_url into.
            e.g.: X:\something, $HOME/Projects/something

        :param bool update_if_already_exists:
            If True, instead of failing with a directory that already exists, this will try to
            perform a "git pull" in the directory, updating it.

        :param bool no_checkout:
            "No checkout of HEAD is performed after the clone is complete."

        :param output_callback:
            .. seealso:: self.Execute
        '''
        # Create target dir
        from ben10.filesystem import CreateDirectory, ListFiles
        CreateDirectory(target_dir)

        try:
            # If directory already contains files, we might need to do a pull instead
            if ListFiles(target_dir):
                if not update_if_already_exists:
                    raise TargetDirAlreadyExistsError(target_dir)
                self.Checkout(target_dir, 'master')
                self.Pull(target_dir, output_callback=output_callback)

            # If there's nothing there, just clone it
            else:
                cmdline = ['clone']
                if no_checkout:
                    cmdline += ['-n']
                cmdline += [repository_url, target_dir]
                self.Execute(
                    cmdline,
                    output_callback=output_callback,
                    clean_eol=False
                )
        except GitExecuteError, e:
            known_errors = [
                ('ssh: Could not resolve', SSHServerCantBeFoundError),
                ('ssh: badsshserver', SSHServerCantBeFoundError),
                ('Name or service not known', SSHServerCantBeFoundError),
                ('R access for', RepositoryAccessError),
                ('Repository does not exist', RepositoryAccessError),
                ('not found', RepositoryAccessError),
            ]

            for message, error in known_errors:
                if message in e.git_msg:
                    raise error(repository_url)

            raise e


    def CreateHookFile(
            self,
            repo_path,
            filename,
            content,
        ):
        '''
        Create a hook-file.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode filename:
            The hook filename.
            Just the base name.
            Ex.
                pre-commit
                post-commit
                hook_lib.py

        :param unicode content:
            The hook file content.

        :return unicode:
            Returns the hook *full* filename.
        '''
        from ben10.filesystem import CreateFile, EOL_STYLE_UNIX

        r_filename = '%(repo_path)s/.git/hooks/%(filename)s' % locals()
        CreateFile(r_filename, content, eol_style=EOL_STYLE_UNIX)
        return r_filename


    def SetRemoteUrl(self, repo_path, url, remote_name='origin'):
        '''
        Sets a remote Url in a git repository

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode url:
            Target url

        :param unicode remote_name:
        '''
        return self.Execute(
            ['remote', 'set-url', remote_name, url],
            repo_path=repo_path,
        )


    def Status(self, repo_path, flags=['--branch', '--short'], flat_output=True, source_dir='.'):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param list(unicode) flags:
            List of additional flags given to status.
            Defaults to --branch and --short

        :param bool flat_output:
            .. seealso:: self.Execute

        :param unicode source_dir:
            Directory (relative to repo_path) where status will be executed.

        :returns unicode:
            Output from git status with the given flags
        '''
        return self.Execute(['status', source_dir] + flags, repo_path, flat_output=flat_output)


    def GetCommitDict(self, repo_path, ref='HEAD'):
        '''
        Returns commit info from the given repository in a dictionary format

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode ref:
            Git ref pointing to commit

        :rtype: dict(unicode,unicode)
        :returns:
            ['commit']
            ['short_commit']
            ['author']
            ['summary']
            ['iso_date']
        '''
        result_format = "commit:%H%nshort_commit:%h%nauthor:%ae%nsummary:%s%niso_date:%ci"
        result = self.Execute(
            ['show', ref, '-s', '--pretty=format:%s' % result_format],
            repo_path,
            flat_output=False
        )

        result = [i.split(':', 1) for i in result]
        result = dict(result)
        return result


    def GetCommitRepr(self, repo_path, ref='HEAD', commit_hash=True, short=False, date=False, summary=False):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode ref:
            Git ref pointing to commit

        :param bool commit_hash:
            If True, show the commit hash

        :param bool short:
            If True, only uses 7 chars instead of the full 40 char hex

            Doesn't do anything if param 'commit_hash' is False

        :param bool date:
            If True, includes the date of the commit

        :param bool summary:
            If True, includes the commit summary

        :return unicode:
            The current (HEAD) commit name (commit_hash string), plus flavors depending on parameters
        '''
        result_format = ''

        if commit_hash:
            if short:
                result_format += '%(short_commit)s'
            else:
                result_format += '%(commit)s'

        if summary:
            result_format += ' %(summary)s'

        if date:
            result_format += ' [%(iso_date)s]'


        commit_dict = self.GetCommitDict(repo_path, ref=ref)
        result = result_format % commit_dict
        return result.strip()


    def GetCommitCount(self, repo_path, commit=None):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :type commit: unicode | None
        :param commit:
            Considers commits of the given commit. (Ex. HEAD)
            Defaults to None which means that we count all the commits in the repository.

        :return int:
            The amount of commits made until now
        '''
        if commit is None:
            rev_list = self.Execute(['rev-list', '--all'], repo_path)
        else:
            rev_list = self.Execute(['rev-list', '--full-history', commit], repo_path)
        return len(rev_list)


    def Diff(self, repo_path, old_revision=None, new_revision=None):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode old_revision:
            The previous revision to be compared with

        :param unicode new_revision:
            The revision to be compared with

        :return unicode:
            The diff obtained, generated by git
        '''
        args = ['diff']
        if old_revision is not None:
            args.append(old_revision)
        if new_revision is not None:
            args.append(new_revision)

        return self.Execute(args, repo_path, flat_output=True)


    def Show(self, repo_path, revision, diff_only=False, flags=[]):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode revision:
            The revision to be shown

        :param bool diff_only:
            If True, only shows diff for this commit. This is similar to git diffing to previous
            commit, but also works for commits without parents

        :param list(unicode) flags:
            Additional flags and parameters passed to 'git show'

        :return unicode:
            result from 'git show'
        '''
        if diff_only:
            output = self.Execute(
                ['show', revision, '--pretty=format:'] + flags,
                repo_path,
                flat_output=True,
            )
            output = output.lstrip('\n')  # Remove empty lines from empty format
            return output

        return self.Execute(['show', revision] + flags, repo_path, flat_output=True)


    def GetAuthor(self, repo_path, revision):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode revision:
            The name of the revision from which the author's name will be extracted

        :return unicode:
            The author's name
        '''
        return self.Execute(
            ['log', revision, '-1', '--pretty=format:%an'], repo_path, flat_output=True
        )


    def GetAuthorEmail(self, repo_path, revision):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode revision:
            The name of the revision from which the author's name will be extracted

        :return unicode:
            The author's email
        '''
        return self.Execute(
            ['log', revision, '-1', '--pretty=format:%ae'], repo_path, flat_output=True
        )


    def GetMessage(self, repo_path, revision):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode revision:
            The name of the revision from which the commit message will be extracted

        :return unicode:
            The commit message
        '''
        return self.Execute(
            ['log', revision, '-1', '--pretty=format:%B'], repo_path, flat_output=True
        )


    def GetChangedPaths(self, repo_path, revision, previous_revision=None):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode revision:
            The name of the revision from which the changed paths be extracted

        :param unicode|None previous_revision:
            Used to list changed paths in a range.
            Will list all changes between `previous_revision` and `revision` (not including changes
            in `previous_revision` itself)

        :return list(unicode):
            A list with the names of all changed paths
        '''
        revision_string = revision
        if previous_revision is not None:
            revision_string = previous_revision + '..' + revision

        # Use git show to list paths
        changed_paths = self.Execute(
            ['show', '-m', '--pretty=format:', '--name-only', revision_string], repo_path)

        changed_paths = set(changed_paths)
        changed_paths.discard('')

        return changed_paths


    def GetCommitStats(self, repo_path, revision):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode revision:
            The name of the revision.

        :rtype: tuple(int,int,int)
        :returns:
            Returns the commit status with the following information:
                result[0]: Number of changed files
                result[1]: Number of lines added
                result[2]: Number of lines deleted
        '''
        def ExtractValue(s, rexpr):
            import re
            result = re.search(rexpr, s)
            if result is None:
                return 0
            return int(result.group(1))

        stats = self.Execute(
            ['show', revision, '--shortstat', '--pretty=format:'],
            repo_path,
        )

        stats = stats[1]
        changed = ExtractValue(stats, '(\d+) file[s]? changed')
        insertions = ExtractValue(stats, '(\d+) insertion[s]?')
        deletions = ExtractValue(stats, '(\d+) deletion')

        return (changed, insertions, deletions)


    def Checkout(self, repo_path, ref):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode ref:
            An existing git ref (can be a branch, tag, or revision)

        :rtype: list(unicode)
        :returns:
            Output from git log
        '''
        try:
            return self.Execute(['checkout', ref], repo_path)
        except GitExecuteError, e:
            if 'did not match any file(s) known to git.' in e.git_msg:
                raise GitRefDoesNotExistError(ref)
            raise


    def IsDirty(self, repo_path):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :return bool:
            If the repository is dirty (has changes that weren't commited yet).

        .. note::
            Ignores untracked files
        '''
        return len(self.GetDirtyFiles(repo_path)) > 0


    def GetRevisions(self, repo_path, r1, r2, ref=None, ignore_merges=False):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode r1:
            The first revision to consider

        :param unicode r2:
            The last revision to consider

        :param unicode ref:
            Ref containing r2.

            This is only needed when r1 is a non-revision (self.ZERO_REVISION), seen in a first commit
            made to a branch or repository.

            e.g.:
                refs/heads/master
                refs/heads/my_branch


        :param bool ignore_merges:
            If True, will skip all merge commit revisions.

        :rtype: list(unicode)
        :returns:
            A list of all revision hashes that are reachable by r2, but not by r1.
            Orders from earliest to latest.
        '''
        # Handle branch deletion (no commits here)
        if r2 == self.ZERO_REVISION:
            return []

        # Handle new branches, or first pushes to a repository
        if r1 == self.ZERO_REVISION:
            assert ref is not None, 'Must receive ref name when r1 is ' + self.ZERO_REVISION

            # List all branches
            heads = self.Execute(
                ["for-each-ref", "--format=%(refname)", "refs/heads/*"],
                repo_path,
            )

            # Remove this branch from that list
            heads.remove(ref)

            # Find all commits reachable by r2, that can't be reached in any other branch
            command_line = ['log', r2, "--pretty=%H", "--not"] + heads

            if ignore_merges:
                command_line += ['--no-merges']
            hashes = self.Execute(command_line, repo_path)
        else:
            # Simple case
            command_line = ['log', '--pretty=format:%H', '%s..%s' % (r1, r2)]
            if ignore_merges:
                command_line += ['--no-merges']
            hashes = self.Execute(command_line, repo_path)

        hashes.reverse()

        return hashes


    def Add(self, repo_path, filename):
        '''
        Adds a filename to a repository's staged changes.

        :param unicode repo_path:

        :param unicode filename:
        '''
        self.Execute(['add', filename], repo_path)


    def Commit(self, repo_path, commit_message, flags=[]):
        '''
        Commits staged changes in a repository

        :param unicode repo_path:

        :param unicode commit_message:
        '''
        self.Execute(['commit', '-m', commit_message] + flags, repo_path)


    def Push(self, repo_path, remote_name=None, ref=None, tags=False):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The remote into which the push will be made.

        :param unicode ref:
            The name of the ref that will pushed into.

        :param bool tags:
            If True, also pushes tags
        '''
        command_line = ['push']

        if remote_name is not None:
            command_line.append(remote_name)

        if ref is not None:
            command_line.append(ref)

        if tags:
            command_line.append('--tags')

        self.Execute(command_line, repo_path)


    def Fetch(self, repo_path, remote_name=None, ref=None, tags=False, flags=[]):
        '''
        Fetches information from a remote

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The remote from which the info will be fetched

        :param unicode ref:
            Target remote refspec.

        :param bool tags:
            If True, adds --tags option

        :param list(unicode) flags:
            Additional flags passed to git fetch

        :rtype: list(unicode)
        :returns:
            Output from git log
        '''
        command_line = ['fetch']

        if remote_name is not None:
            command_line.append(remote_name)

        if ref is not None:
            command_line.append(ref)

        if tags:
            command_line.append('--tags')

        command_line += flags

        return self.Execute(command_line, repo_path)


    def Reset(self, repo_path, ref=None):
        '''
        Reset the current reference to the given one.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode ref:
            Reference to "reset" to.
            If None, resets the working dir to its original state.

        :rtype: list(unicode)
        :returns:
            Output from git log
        '''
        command_line = ['reset', '--hard']
        if ref is not None:
            command_line.append(ref)

        return self.Execute(command_line, repo_path)


    def Pull(self, repo_path, remote_name=None, branch=None, rebase=None, commit=None, output_callback=None):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The remote from which the pull will be made.

        :param unicode branch:
            The name of the branch that will be pulled.
            If None, uses the current branch

        :type rebase: bool | None
        :param rebase:
            A three state boolean (True,False,None) that indicates if we must force rebase (True),
            force not using rebase (False) or let the default behavior (None)

        :type commit: bool | None
        :param commit:
            A three state boolean (True,False,None) that indicates if we must create a commit
            (True), not create a commit (False) or let the default behavior (None)

        :param output_callback:
            .. seealso:: self.Execute

        :return list(unicode):
            Output from git pull
        '''
        command_line = ['pull']


        if rebase == True:
            command_line.append('--rebase')
        if rebase == False:
            command_line.append('--no-rebase')

        if commit == True:
            command_line.append('--commit')
        if commit == False:
            command_line.append('--no-commit')

        if remote_name is not None:
            command_line.append(remote_name)

        if branch is not None:
            command_line.append(branch)

        return self.Execute(
            command_line,
            repo_path,
            output_callback=output_callback,
            clean_eol=False
        )


    @Memoize(500)
    def Log(self, repo_path, flags=()):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param tuple(unicode) flags:
            Additional flags passed to git log

            e.g. ('--oneline',)

        :returns list(unicode):
            Output from git log
        '''
        return self.Execute(('log',) + flags, repo_path)


    @Memoize(500)
    def GetCurrentBranch(self, repo_path, submodule=False):
        '''
        :param repo_path:
            Path to the repository (local)

        :returns unicode|None:
            The name of the current branch.

        :raises NotCurrentlyInAnyBranchError:
            If not on any branch.
        '''
        # Returns the branch of the host repository if the given repo_path is a submodule.
        if submodule and self._IsSubModule(repo_path):
            repo_path = self._GetTopLevel(os.path.dirname(self._GetTopLevel(repo_path)))

        branches = self.Execute(['branch'], repo_path)

        for branch in branches:
            if '*' in branch:  # Current branch
                current_branch = branch.split(' ', 1)[1]
                break
        else:
            raise RuntimeError('Error parsing output from git branch')

        # The comment differs depending on Git version. The text "(no branch)' was used before version 1.8.3
        if current_branch == '(no branch)' or current_branch.startswith('(detached from'):
            raise NotCurrentlyInAnyBranchError(repo_path)

        return current_branch


    @Memoize(500)
    def GetCurrentRef(self, path, fail_if_dirty=False):
        '''
        :param unicode path:
            Path within a Git repository.

        :returns unicode:
            Git ref for last commit that changed `path`
        '''
        # Just to be safe, make sure that `path` is absolute and standard
        from ben10.filesystem import StandardizePath

        path = StandardizePath(os.path.abspath(path))

        if fail_if_dirty:
            # Always look for dirty files in root directory. Since we usually have many refs in a
            # single repository, this reduces the amount of 'git log' we have to execute
            git_root_dir = self._GetTopLevel(path)

            modified_files_in_repo = [
                posixpath.join(git_root_dir, dirty_file)
                for _status, dirty_file in self.GetDirtyFiles(git_root_dir)
            ]

            modified_files_in_path = [p for p in modified_files_in_repo if p.startswith(path)]
            if modified_files_in_path:
                raise DirtyRepositoryError(git_root_dir, modified_files_in_path)

        return self.Log(path, ('-n1', '--pretty=format:%H', '.'))[0]


    def _IsSubModule(self, path):
        '''
        Returns whether the repository of the given path is a submodule.

        :param unicode path:
            Path within a Git repository.

        :return bool:
        '''
        return os.path.isfile(self._GetTopLevel(path) + '/.git')


    def _GetTopLevel(self, path):
        '''
        Returns the git repository top-level (root) directory.

        :param unicode path:
            Path within a Git repository.

        :return unicode:
        '''
        return self.Execute(['rev-parse', '--show-toplevel'], path, flat_output=True)


    def BranchExists(self, repo_path, branch_name, remote=False):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode branch_name:
            The branches' name

        :param bool remote:
            Considers the remote branches instead of the local ones.

        :returns bool:
            True if the branch already exists
        '''
        return branch_name in self.ListBranches(repo_path, remote=remote)


    # Stash

    def Stash(self, repo_path):
        '''
        "Stash the changes in a dirty working directory away"

        :param unicode repo_path:
            Path to the repository (local)

        :rtype: list(unicode)
        :returns:
            Output from git log
        '''
        try:
            return self.Execute(['stash'], repo_path)
        except GitExecuteError:
            raise


    def StashPop(self, repo_path):
        '''
        "Remove a single stashed state from the stash list and apply it on top of the current
        working tree state"

        :param unicode repo_path:
            Path to the repository (local)

        :rtype: list(unicode)
        :returns:
            Output from git log
        '''
        try:
            return self.Execute(['stash', 'pop'], repo_path)
        except GitExecuteError:
            raise


    # Remotes

    def ListRemotes(self, repo_path):
        '''
        Lists remotes configured in a git repository.

        :param unicode repo_path:
            Path to the repository (local)

        :rtype: list(unicode)
        :returns:
            List of remotes.
        '''
        return self.Execute(['remote'], repo_path)


    def RemoteExists(self, repo_path, remote_name):
        '''
        Checks if a remote name exists in a git repository.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The remote name.

        :rtype: bool
        :returns:
            Returns True if the remote exists and False otherwise.
        '''
        return remote_name in self.ListRemotes(repo_path)


    def GetRemoteUrl(self, repo_path, remote_name='origin'):
        '''
        Returns the url associated with a remote in a git repository.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The remote name.

        :rtype: unicode
        :returns:
            The url of the remote.
        '''
        return self.Execute(
            ['config', '--local', '--get', 'remote.%s.url' % remote_name],
            repo_path,
            flat_output=True,
        )


    def RemoveRemote(self, repo_path, remote_name):
        '''
        Removes a remote from the git repository.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The name of the remote.
        '''
        self.Execute(
            ['remote', 'rm', remote_name],
            repo_path,
            flat_output=True,
        )


    def AddRemote(self, repo_path, remote_name, remote_url):
        '''
        Add a remote in a git repository.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The (new) remote name.

        :param unicode remote_url:
            The (new) remote url.
        '''
        self.Execute(
            ['remote', 'add', remote_name, remote_url],
            repo_path,
            flat_output=True,
        )


    def RemotePrune(self, repo_path, remote_name='origin'):
        '''
        Prunes branches from a remote

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode remote_name:
            The remote name.
        '''
        output = self.Execute(['remote', 'prune', remote_name], repo_path)

        pruned_branches = set()
        pruned_prefix = ' * [pruned] %s/' % remote_name
        for line in output:
            if line.startswith(pruned_prefix):
                pruned_branches.add(line[len(pruned_prefix):])
        return pruned_branches


    def IsValidRepository(self, repo_path):
        '''
        Checks if the given path is a valid git repository

        :param unicode repo_path:
            Path to the repository (local)

        :rtype: bool
        :returns:
            Returns True if the given path is a git-repository and False otherwise.
        '''
        from ben10.filesystem import Exists

        git_filename = os.path.join(repo_path, '.git')

        # Assume that if we have a .git dir, we are a valid repository
        # Assume that if we have a .git file, we have a valid sub-module repository
        return Exists(git_filename)


    def GetWorkingDir(self, path):
        '''
        Obtain the local working dir.

        :param unicode path:
            A path INSIDE a local repository.

        :returns unicode:
            The working (root) directory of the local git repository.
            Returns None if the given path does not belong to a local git repository.
        '''
        # Assume that if we have a .git dir, we are a valid repository
        result = os.path.normpath(os.path.abspath(path))
        dir_name = os.path.dirname(result)
        while result != dir_name:
            if self.IsValidRepository(result):
                return result
            result = dir_name
            dir_name = os.path.dirname(result)
        return None


    def ListBranches(self, repo_path, remote=False, remote_name='origin'):
        '''
        List the branches of the given repository.

        :param unicode repo_path:
            Path to the repository (local)

        :param bool remote:
            Considers the remote branches instead of the local ones.

        :param unicode remote_name:
            Name of the remote to check for the branch existence.
            Only used if the parameter remote=True.

        :return list(unicode):
            The first branch in the list is the current branch.
            All other branches are sorted alphabetically.
        '''
        import re

        if remote:
            all_branches = self.Execute(['branch', '-r'], repo_path)
            r_branches = set()
            for branch_name in all_branches:
                re_search = re.search('%s/(\S+)$' % remote_name, branch_name)
                if re_search is not None:
                    r_branches.add(re_search.groups()[0])
            return sorted(list(r_branches))
        else:
            r_current = None
            r_branches = []
            for i_branch in self.Execute('branch', repo_path):
                branch = i_branch.strip('* ')
                if '*' in i_branch:
                    r_current = branch
                elif branch:
                    r_branches.append(branch)
            return [r_current] + sorted(r_branches)


    def Clean(self, repo_path, ignored_only=True):
        '''
        Cleans a repository, removing files that match .gitignore (and nothing else).

        :param unicode repo_path:
            Path to the repository (local)

        :param bool ignored_only:
            If True, only delete files in .gitignore

        :rtype: list(unicode)
        :returns:
            List of files removed
        '''
        command_line = [
            'clean',
            '-f',  # Force
            '-d',  # Delete directories
        ]

        if ignored_only:
            command_line.append('-X'),  # Only delete files that are ignored by git
        else:
            command_line.append('-x'),  # Delete all untracked files

        output = self.Execute(command_line, repo_path)

        removed_files = []
        for line in output:
            filename = line.replace('Removing ', '')
            removed_files.append(filename)

        return removed_files


    @Memoize(500)
    def GetDirtyFiles(self, repo_path, source_dir='.'):
        '''
        Returns modified files from a repository (ignores untracked files).
        Parses output from git status to obtain this information.

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode source_dir:
            .. seealso:: Git.Status

        :rtype: list(tuple(unicode,unicode))
        :returns:
            List of (status, path) of modified files in a repository
        '''
        status = self.Status(
            repo_path,
            flags=['--porcelain'],
            flat_output=False,
            source_dir=source_dir,
        )

        def ExtractFileStatus(line):
            # Strip lines
            line = line.strip()

            # Split at first whitespaces
            import re
            return re.search('(\S*)\s+(\S*)', line).groups()

        result = map(ExtractFileStatus, status)

        # Ignore untracked files ('??')
        result = [i for i in result if i[0] != '??']

        return result


    def CreateTag(self, repo_path, name, message=None, message_file=None):
        '''
        Creates a tag in the repository

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode name:
            Name of the tag

        :type message: unicode | None
        :param message:
            If not None, adds a message to the tag

        :type message_file: unicode | None
        :param message_file:
            If not None, reads file at this path and sets this as the tag message.
        '''
        command_line = ['tag', name]
        if message is not None:
            command_line += ['-m', message]
        if message_file is not None:
            command_line += ['--file', message_file]

        self.Execute(command_line, repo_path)


    def GetTags(self, repo_path, commit=None):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode commit:
            If given, only return tags that point to this commit.

        :rtype: set(unicode)
        :returns:
            Set of available tag names
        '''
        if commit is not None:
            return set(self.Execute(['tag', '--points-at=' + commit], repo_path))
        return set(self.Execute(['tag'], repo_path))


    def GetTagMessage(self, repo_path, tag_name):
        '''
        :param unicode repo_path:
            Path to the repository (local)

        :param unicode tag_name:
            Name of the tag being read

        :returns unicode:
            Tag content
        '''
        tag_output = self.Execute(['cat-file', '-p', tag_name], repo_path, flat_output=True)

        # Output starts with some headers, followed by an empty line and then the tag message
        # e.g.:
        #    object ID
        #    type commit
        #    tag TAG_NAME
        #    tagger AUTHOR <EMAIL> TIMESTAMP TIMEZONE
        #
        #    TAG_MESSAGE
        tag_output = tag_output.split('\n\n', 1)[1]

        return tag_output


    def CreateLocalBranch(self, repo_path, branch_name, source=None):
        '''
        Creates a new local branch, and stays in it.
        Equivalent to 'git checkout -b branch_name'

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode branch_name:
            The name of the branch to be created.

        :param unicode|None source:
            If a ref is given, branch is created from this point.

        :raises DirtyRepositoryError:
            .. seealso:: DirtyRepositoryError

        :raises BranchAlreadyExistsError:
            .. seealso:: BranchAlreadyExistsError
        '''
        if self.IsDirty(repo_path):
            raise DirtyRepositoryError(repo_path)

        try:
            # Create the new branch
            if source is not None:
                self.Execute(['checkout', source, '-b', branch_name], repo_path)
            else:
                self.Execute(['checkout', '-b', branch_name], repo_path)
        except GitExecuteError, e:
            if 'already exists' in e.git_msg:
                raise BranchAlreadyExistsError(branch_name)
            raise


    def DeleteLocalBranch(self, repo_path, branch_name):
        '''
        Deletes a local branch

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode branch_name:
            The name of the branch to be deleted.

        :raises BranchDoesNotExistError:
            .. seealso:: BranchDoesNotExistError
        '''
        # If we currently are in the branch being removed, switch to master
        if self.GetCurrentBranch(repo_path) == branch_name:
            self.Checkout(repo_path, 'master')

        # Delete branch locally
        try:
            self.Execute(['branch', '-d', branch_name], repo_path)
        except GitExecuteError, e:
            if 'not found' in e.git_msg:
                raise BranchDoesNotExistError(branch_name)
            raise e


    def DeleteBranch(self, repo_path, branch_name):
        '''
        Deletes a branch, both locally and remotely

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode branch_name:
            The name of the branch to be deleted.

        :raises BranchDoesNotExistError:
            If the branch does not exist remotely.
        '''
        # Delete branch locally
        try:
            self.DeleteLocalBranch(repo_path, branch_name)
        except BranchDoesNotExistError:
            pass  # Doesn't matter if it does not exist locally

        self.DeleteRemoteBranch(repo_path, branch_name)


    def CreateRemoteBranch(self, repo_path, original_branch, branch_name, remote_name='origin'):
        '''
        Creates a new branch in origin

        :param unicode repo_path:
            Path to the repository (local)

        :type original_branch: unicode or None
        :param original_branch:
            Name of the remote branch from which the new branch will be created.
            If None, uses the current local branch

        :param unicode branch_name:
            The name of the branch to be created.

        :param unicode remote_name:
            Name of the remote into which the new branch will be created.

        :raises DirtyRepositoryError:
            .. seealso:: DirtyRepositoryError

        :raises BranchAlreadyExistsError:
            .. seealso:: BranchAlreadyExistsError

        :raises BranchDoesNotExistError:
            .. seealso:: BranchDoesNotExistError
        '''
        # Check if target branch already exists in remote
        if self.BranchExists(repo_path, branch_name, remote=True):
            raise BranchAlreadyExistsError(branch_name)

        # If original_branch is None, use the current local branch
        if original_branch is None:
            if self.IsDirty(repo_path):
                raise DirtyRepositoryError(repo_path)

            original_branch = self.GetCurrentBranch(repo_path)

        # Check if original_branch exists
        if not self.BranchExists(repo_path, original_branch, remote=True):
            raise BranchDoesNotExistError(original_branch)

        # Push the new branch to the remote
        ref = '%(remote_name)s/%(original_branch)s:refs/heads/%(branch_name)s' % locals()
        self.Push(repo_path, remote_name, ref)


    def DeleteRemoteBranch(self, repo_path, branch_name, remote_name='origin'):
        '''
        Deletes a branch in origin

        :param unicode repo_path:
            Path to the repository (local)

        :param unicode branch_name:
            The name of the branch to be deleted.

        :raises BranchDoesNotExistError:
            .. seealso:: BranchDoesNotExistError
        '''
        if not self.BranchExists(repo_path, branch_name, remote=True):
            raise BranchDoesNotExistError(branch_name)

        # Delete the remote branch
        self.Push(repo_path, remote_name=remote_name, ref=':' + branch_name)



#===================================================================================================
# TargetDirAlreadyExistsError
#===================================================================================================
class TargetDirAlreadyExistsError(RuntimeError):
    '''
    Raised when trying to clone a repository into a location that already exists and is not empty.
    '''
    def __init__(self, target_dir):
        self.target_dir = target_dir
        RuntimeError.__init__(
            self,
            'Destination path "%s" already exists and is not an empty directory.' % self.target_dir
        )



#===================================================================================================
# RepositoryAccessError
#===================================================================================================
class RepositoryAccessError(RuntimeError):
    '''
    Raised when trying to access an inexistent repository, or one which you don't have reading
    permissions
    '''
    def __init__(self, repo_path):
        self.repo_path = repo_path
        RuntimeError.__init__(
            self,
            "Repository '%s' doesn't exist or you don't have permission to read it." \
            % self.repo_path
        )



#===================================================================================================
# DirtyRepositoryError
#===================================================================================================
class DirtyRepositoryError(RuntimeError):
    '''
    Raised when trying to perform some operations in a dirty (uncommited changes) repository.
    '''
    def __init__(self, repo_path, dirty_files=None):
        self.repo_path = repo_path
        self.dirty_files = dirty_files

        message = 'Repository at "%s" is dirty.' % repo_path
        if dirty_files:
            message += '\n\tfiles:\n\t\t' + '\n\t\t'.join(dirty_files)

        RuntimeError.__init__(self, message)



#===================================================================================================
# BranchAlreadyExistsError
#===================================================================================================
class BranchAlreadyExistsError(RuntimeError):
    '''
    Raised when trying to create a branch that already exists.
    '''
    def __init__(self, branch_name):
        self.branch = branch_name
        RuntimeError.__init__(self, 'Branch "%s" already exists.' % branch_name)



#===================================================================================================
# BranchDoesNotExistError
#===================================================================================================
class BranchDoesNotExistError(RuntimeError):
    '''
    Raised when trying to operate with a branch that does not exist.
    '''
    def __init__(self, branch):
        self.branch = branch
        RuntimeError.__init__(self, 'Branch "%s" does not exist.' % branch)



#===================================================================================================
# GitRefDoesNotExistError
#===================================================================================================
class GitRefDoesNotExistError(RuntimeError):
    '''
    Raised when trying to checkout a ref that does not exist.
    '''

    def __init__(self, ref):
        self.ref = ref
        RuntimeError.__init__(self, 'Ref "%s" does not exist.' % ref)


#===================================================================================================
# NotCurrentlyInAnyBranchError
#===================================================================================================
class NotCurrentlyInAnyBranchError(RuntimeError):
    '''
    Raised when operating while not on any branch (headless state)
    '''
    def __init__(self, repo_path):
        self.repo_path = repo_path
        RuntimeError.__init__(self, 'Repository "%s" is not currently on any branch.' % repo_path)



#===================================================================================================
# SSHServerCantBeFoundError
#===================================================================================================
class SSHServerCantBeFoundError(RuntimeError):
    '''
    Raised when trying to connect to a git ssh server that cannot be found.
    '''

    def __init__(self, repository_url):
        self.repository_url = repository_url
        RuntimeError.__init__(self, 'SSH server at "%s" could not be found.' % repository_url)



#===================================================================================================
# GitExecuteError
#===================================================================================================
class GitExecuteError(RuntimeError):
    '''
    Raised when running the git executable returns anything other than 0.
    '''
    def __init__(self, command, retcode, git_msg):
        self.command = command
        self.retcode = retcode
        self.git_msg = git_msg

        RuntimeError.__init__(
            self,
            'Command "%(command)s" returned with error %(retcode)s\n\n' % locals() + \
            'Output from git:\n\n' + git_msg
        )
