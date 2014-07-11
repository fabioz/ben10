# Basic ESSS Namespace 1.0

[![Build Status](https://travis-ci.org/ESSS/ben10.png)](https://travis-ci.org/ESSS/ben10)
[![Coverage Status](https://coveralls.io/repos/ESSS/ben10/badge.png)](https://coveralls.io/r/ESSS/ben10)


## About

This is an experimental library that will serve as a showcase of library good practices including:

* consistent organization
* pytests
* coverage 100%
* code format (pylint)
* dependency control
* documentation

The contents of this library is composed by all code from coilib50 that is common to both Aasimar and ESSS Projects.

## Directives


* pytest: All tests must be using py.test.
* coverage: Aim for 100% coverage.
* travis-ci: The project must be passing on travis-ci.
* pypi: Make it available on PyPI.

## Modules

* **archivist/**: An API to create and extract archives.
* **ben10/**:
    * **filesystem/**: An API to handle files.
    * **foundation/**: A LOT of stuff!
        * **bunch.py**: A simpler object definition for python.
        * **callback.py**: Callback implementation.
        * **debug.py**: Debugging utitilities.
        * **decorators.py**: A collection of decorators such as Overwrite. 
        * **enum.py**: Enumerate implementation.
        * **fifo.py**: "First In First Out" stack implementation.
        * **handle_exception.py**: Handles an exception, printing the traceback without breaking the process.
        * **hash.py**: ?
        * **immutable.py**: ?
        * **is_frozen.py**: Check if you're inside an excutable (cx_Freeze).
        * **klass.py**: Class related python extensions.
        * **log.py**: ?
        * **lru.py**: "Last Recently Used" implementation.
        * **memoize.py**: Simple way of caching a function;
        * **namedtuple.py**: A named tuple implementation in python.
        * **odict.py**: ?
        * **platform_.py**: Platform class with our platform naming convention implemented.
        * **profiling.py**: Profiling utitilies.
        * **pushpop.py**: 
        * **redirect_output.py**: Redirect stdout and stderr output using a context manager.
        * **reraise.py**: Reraise an exception adding some information to its backlog.
        * **singleton.py**: Implement singleton, including push and pop operations.
        * **string.py**: String utitlies such as Indent and Dedent.
        * **translation.py**: Translation methods placeholder.
        * **types_.py**: A colection of basic types to extend Python.
        * **uname.py**: Obtain machine information.
        * **url.py**: URL handling functions.
        * **weak_ref.py**: Weak-reference extensions such as weak-function.
    * **interface/**: Implement interfaces for python.
    * **dircache.py**: Implements a cache system with three layers: remote package, local cache and local directory.
    * **execute.py**: Command execution API.
    * **fixtures.py**: Test fixtures.
    * **module_finder.py**: A python module finder.
    * **registry_dict.py**: A dict-like API to read/write on Windows registry.
* **clikit/**: A command-line application generator based on fixtures;
* **gitit/**: A Pythonic API to git;
* **terraforming/**: Python code refactoring;
* **txtout/**: Console output API;
* **xml_factory/**: A fast and simple API to create XML files.

### Module ben10.interface

#### Dependencies:

* ben10.foundation.decorators
* ben10.foundation.immutable
* ben10.foundation.is_frozen
* ben10.foundation.klass
* ben10.foundation.odict
* ben10.foundation.reraise
* ben10.foundation.singleton
* ben10.foundation.types_
* ben10.foundation.weak_ref
* pytest (test only)
* ben10.foundation.callback (test only)


