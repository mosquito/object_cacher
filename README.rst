Object Cacher
=============

Simple object cacher decorator. Makes cache for results of hard functions or methods.
For example you have remote RESTful api with a lot of dictionaries. You may cache it:

    >>> from urllib import urlopen
    >>> from object_cacher import ObjectCacher
    >>> @ObjectCacher(timeout=60)
    ... def get_api():
    ...     print "This real call"
    ...     return urlopen('https://api.github.com/').read()
    ...
    >>> get_api()
    This real call
    '{"current_user_url":"https://api.github.com/user", ...'
    >>> get_api()
    '{"current_user_url":"https://api.github.com/user", ...'

As result you made http request only once.

For methods you may use it like this:

    >>> from urllib import urlopen
    >>> from object_cacher import ObjectCacher
    >>> class API(object):
    ...     @ObjectCacher(timeout=60, ignore_self=True)
    ...     def get_methods(self):
    ...         print "Real call"
    ...         return urlopen('https://api.github.com/').read()
    ...
    >>> a = API()
    >>> a.get_methods()
    Real call
    '{"current_user_url":"https://api.github.com/user", ...'
    >>> b = API()
    >>> b.get_methods()
    '{"current_user_url":"https://api.github.com/user", ...'

If ignore_self parameter is set, cache will be shared by all instance. Otherwise cache for instances will be split.

Also you may use persistent cache.
The "ObjectPersistentCacher" class-decorator makes file-based pickle-serialized cache storage.
When you want to keep cache after rerun you must determine cache id:

    >>> from urllib import urlopen
    >>> from object_cacher import ObjectCacher
    >>> class API(object):
    ...     @ObjectPersistentCacher(timeout=60, ignore_self=True, oid='com.github.api.listofmethods')
    ...     def get_methods(self):
    ...         print "Real call"
    ...         return urlopen('https://api.github.com/').read()
    ...
    >>> a = API()
    >>> a.get_methods()
    Real call
    '{"current_user_url":"https://api.github.com/user","authorizations_url":"https://api.github.com/authorizations","code_search_url":"https://api.github.com/search/code?q={query}{&page,per_page,sort,order}","emails_url":"https://api.github.com/user/emails","emojis_url":"https://api.github.com/emojis","events_url":"https://api.github.com/events","feeds_url":"https://api.github.com/feeds","following_url":"https://api.github.com/user/following{/target}","gists_url":"https://api.github.com/gists{/gist_id}","hub_url":"https://api.github.com/hub","issue_search_url":"https://api.github.com/search/issues?q={query}{&page,per_page,sort,order}","issues_url":"https://api.github.com/issues","keys_url":"https://api.github.com/user/keys","notifications_url":"https://api.github.com/notifications","organization_repositories_url":"https://api.github.com/orgs/{org}/repos{?type,page,per_page,sort}","organization_url":"https://api.github.com/orgs/{org}","public_gists_url":"https://api.github.com/gists/public","rate_limit_url":"https://api.github.com/rate_limit","repository_url":"https://api.github.com/repos/{owner}/{repo}","repository_search_url":"https://api.github.com/search/repositories?q={query}{&page,per_page,sort,order}","current_user_repositories_url":"https://api.github.com/user/repos{?type,page,per_page,sort}","starred_url":"https://api.github.com/user/starred{/owner}{/repo}","starred_gists_url":"https://api.github.com/gists/starred","team_url":"https://api.github.com/teams","user_url":"https://api.github.com/users/{user}","user_organizations_url":"https://api.github.com/user/orgs","user_repositories_url":"https://api.github.com/users/{user}/repos{?type,page,per_page,sort}","user_search_url":"https://api.github.com/search/users?q={query}{&page,per_page,sort,order}"}'
    >>> b = API()
    >>> b.get_methods()
    '{"current_user_url":"https://api.github.com/user","authorizations_url":"https://api.github.com/authorizations","code_search_url":"https://api.github.com/search/code?q={query}{&page,per_page,sort,order}","emails_url":"https://api.github.com/user/emails","emojis_url":"https://api.github.com/emojis","events_url":"https://api.github.com/events","feeds_url":"https://api.github.com/feeds","following_url":"https://api.github.com/user/following{/target}","gists_url":"https://api.github.com/gists{/gist_id}","hub_url":"https://api.github.com/hub","issue_search_url":"https://api.github.com/search/issues?q={query}{&page,per_page,sort,order}","issues_url":"https://api.github.com/issues","keys_url":"https://api.github.com/user/keys","notifications_url":"https://api.github.com/notifications","organization_repositories_url":"https://api.github.com/orgs/{org}/repos{?type,page,per_page,sort}","organization_url":"https://api.github.com/orgs/{org}","public_gists_url":"https://api.github.com/gists/public","rate_limit_url":"https://api.github.com/rate_limit","repository_url":"https://api.github.com/repos/{owner}/{repo}","repository_search_url":"https://api.github.com/search/repositories?q={query}{&page,per_page,sort,order}","current_user_repositories_url":"https://api.github.com/user/repos{?type,page,per_page,sort}","starred_url":"https://api.github.com/user/starred{/owner}{/repo}","starred_gists_url":"https://api.github.com/gists/starred","team_url":"https://api.github.com/teams","user_url":"https://api.github.com/users/{user}","user_organizations_url":"https://api.github.com/user/orgs","user_repositories_url":"https://api.github.com/users/{user}/repos{?type,page,per_page,sort}","user_search_url":"https://api.github.com/search/users?q={query}{&page,per_page,sort,order}"}'

That is keep cache after rerun.

You may change cache dir for ObjectPersistentCacher via changing 'CACHE_DIR' class-property.

    >>> ObjectPersistentCacher.CACHE_DIR = '/var/tmp/my_cache'


Installation
++++++++++++

You may install from pypi

        pip install SimpleAES

or manual

        python setup.py install
