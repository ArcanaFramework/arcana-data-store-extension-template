Arcana Extension - changeme
===========================
.. CHANGEME, update the test actions badge to the name of your repo
.. image:: https://github.com/arcanaframework/arcana-data-store-extension-template/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/arcanaframework/arcana-data-store-extension-template/actions/workflows/tests.yml
.. .. image:: https://codecov.io/gh/arcanaframework/arcana-changeme/branch/main/graph/badge.svg?token=UIS0OGPST7
..    :target: https://codecov.io/gh/arcanaframework/arcana-changeme
.. image:: https://github.com/ArcanaFramework/arcana/actions/workflows/docs.yml/badge.svg
   :target: http://arcana.readthedocs.io/en/latest/?badge=latest
   :alt: Docs


This is a template repository for extensions to the Arcana_ framework to add support
for *changeme* data stores.

Customisation

After creating a new extension repository from this template, do a global
search for "changeme" and replace it with the name of your package to update the package
settings. Next, update the author and maintainer tags in the "[project]" Section of the
the ``pyproject.toml``.

There are two template classes for the data store connector `data.local.ExampleLocal`
for data stored on the local file-system in a specific structure (e.g. BIDS), and
`data.remote.ExampleRemote` for data stored in remote data repositories. Keep the relevant
class and customise it for your use case.


Quick Installation
------------------

This extension can be installed for Python 3 using *pip*::

    $ pip3 install arcana-changeme

This will also install the core Arcana_ package

License
-------

This work is licensed under a
`Creative Commons Attribution 4.0 International License <http://creativecommons.org/licenses/by/4.0/>`_

.. image:: https://i.creativecommons.org/l/by/4.0/88x31.png
  :target: http://creativecommons.org/licenses/by/4.0/
  :alt: Creative Commons Attribution 4.0 International License



.. _Arcana: http://arcana.readthedocs.io
