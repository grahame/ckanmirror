# ckanmirror

A simple command-line utility that enables incremental mirroring of a nominated package
from a CKAN instance. All CKAN resources associated with the package will be downloaded,
along with their associated metadata. Resources linked from previous versions of the package
are not changed, so this tool can be used to build up an archive of a CKAN package over time.

## Getting started

Install the tool:

```
pip install ckanmirror
```

In a directory you wish the CKAN package to be mirrored to, write your config into a file named `ckanmirror.json`:

```
{
    'apikey': '<your CKAN API key>',
    'remote': 'https://ckan.example.com',
    'package_id': '<CKAN package ID>',

}
```

... then, from that directory, simply run `ckanmirror`.

