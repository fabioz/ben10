        r = git.Log(working_dir, ('--oneline',))
        # Modifying a file should leave it dirty
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()
        git.ClearCache()



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
    return result