Arcana Extension - changeme
===========================
.. image:: https://github.com/arcanaframework/arcana-data-store-extension-template/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/arcanaframework/arcana-data-store-extension-template/actions/workflows/tests.yml
.. .. image:: https://codecov.io/gh/arcanaframework/arcana-changeme/branch/main/graph/badge.svg?token=UIS0OGPST7
..    :target: https://codecov.io/gh/arcanaframework/arcana-changeme
.. .. image:: https://img.shields.io/pypi/pyversions/arcana-changeme.svg
..    :target: https://pypi.python.org/pypi/arcana-changeme/
..    :alt: Python versions
.. .. image:: https://img.shields.io/pypi/v/arcana-changeme.svg
..    :target: https://pypi.python.org/pypi/arcana-changeme/
..    :alt: Latest Version
.. image:: https://github.com/ArcanaFramework/arcana/actions/workflows/docs.yml/badge.svg
    :target: http://arcana.readthedocs.io/en/latest/?badge=latest
    :alt: Docs

This repository contains a template implementation of `DataStore` and `App` extension classes for the Arcana_ framework.

How to Customise
-----------------

After creating a new repository on GitHub from this template, there are a few things you
will need to change:

- do a global search and replace (across all file-types) for **changeme** and replace it with the proposed name for your extension
- change the author and maintainer tags in the **[project]** Section of the the ``pyproject.toml`` to your name and email address
- there are 4 classes within this template repostiory, which need to be either adopted and renamed (using global search and replace), or removed from the package
    - ``data.local.ExampleLocal`` for data stored on the local file-system in a specific structure (e.g. BIDS)
    - ``data.remote.ExampleRemote`` for data stored in remote data repositories. 
    - ``deploy.app.ExampleApp`` for specifying containerized apps that can be executed on data within the data store
    - ``deploy.command.ExampleCommand`` for specifying how the command within the containerized app is executed and configured in the data store
- install a local development copy of the new extension package with ``pip install -e .[dev,test]`` from inside the code-repo directory (using a virtualenv is recommended)
- install pre-commit in the development repo with ``pre-commit install``
- Implement the method stubs of your adopted classes (and ``install_and_launch_app`` in ``conftest.py`` if implementing ``ExampleApp``)
- Check the methods work by running the unittests with ``pytest`` from inside the code-repo directory. They are set to XFAIL (expected failure) by default so you can focus on them one at a time.
- Change the address of the test action badge at the top of this file to point to your new repository and uncomment out the other badges
- Delete this text and above and uncomment the default contents of this README below, adding in any relevant information about the extension (checking the license is appropriate).
- Create a new release on GitHub to deploy your new package to PyPI


.. This is a template repository for extensions to the Arcana_ framework to add support
.. for *changeme* data stores.

.. Quick Installation
.. ------------------

.. This extension can be installed for Python 3 using *pip*

.. .. code-block::bash
..     $ pip3 install arcana-changeme

.. This will also install the core Arcana_ package

License
-------

This work is licensed under a
`Creative Commons Attribution 4.0 International License <http://creativecommons.org/licenses/by/4.0/>`_

.. image:: https://i.creativecommons.org/l/by/4.0/88x31.png
    :target: http://creativecommons.org/licenses/by/4.0/
    :alt: Creative Commons Attribution 4.0 International License



.. _Arcana: http://arcana.readthedocs.io
