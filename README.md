# SharePy - Simple SharePoint Online authentication for Python

This module will handle authentication for your SharePoint Online/O365 site, allowing you to make straightforward HTTP requests from Python. It extends the commonly used *Requests* module, meaning that returned objects are familliar, easy to work with and well documented. 

## Installation

SharePy can be installed from the Python Package Index, PyPI.

```
pip install sharepy
```

## Initiate a SharePoint session:

```python
import sharepy
s = sharepy.connect("example.sharepoint.com")
```

You will be prompted to enter your username and password, which are used to request a security token from Microsoft. An access cookie and request digest token are then retrieved and saved to properties for later use. The digest token will be refreshed automatically as it expires.

A username and password can also be provided as arguments of the `connect` function, if prompts are not desirable.

## Make an API call:

```python
r = s.get("https://example.sharepoint.com/_api/web/lists/GetByTitle('Test Library')")
```

This will return a *Requests* `response` object. See the [requests documentation](http://docs.python-requests.org/en/master/) for details. By default, the headers `Accept: application/json; odata=verbose` and `Content-type: application/json; odata=verbose` are sent with all requests, so API responses will be formatted as JSON where available.

Headers can be added or overridden by supplying a dictionary to the relevant method:

```python
r = s.get("https://example.sharepoint.com/_api/...", headers={"Accept": "application/atom+xml"})
```

Currently only the `post()` method will send a digest header, allowing modifications to be made to SharePoint objects.

## Download a file:

```python
r = s.getfile("https://example.sharepoint.com/Library/Test%20File.pdf")
```

This will download the file to the current directory and return a `response` object. Alternatively you can specify a location to save the file to:

```python
r = s.getfile("https://example.sharepoint.com/Library/Test%20File.pdf", filename="downloads/file.pdf")
```

## Save and reload your authenticated session

Properties of the authentication session can be saved to a file using the `save()` method, so the same cookies can be reused multiple times. Later, the `load()` function can be used to restore the session:

```python
s.save()
```

```python
s = sharepy.load()
```

The default file name for saving and loading sessions is `sp-session.pkl`, however an alternative location can be provided as an argument to `save()` and `load()`.

## Useful reading

- Constructing SharePoint API calls: [SharePoint REST API documentation](https://msdn.microsoft.com/en-us/library/office/dn292552.aspx)
- Handling JSON objects in Python: [Python JSON module documentation](https://docs.python.org/3.4/library/json.html)

## Licence

This software is distributed under the GNU General Public License v3. Copyright 2016-2018 Jonathan Holvey.

## Credits

1. The authentication method used here is based on [this post](https://allthatjs.com/2012/03/28/remote-authentication-in-sharepoint-online/) by Luc Stakenborg.
2. Additional help regarding request digests from sadegh's comment on [this post](http://paulryan.com.au/2014/spo-remote-authentication-rest/) by Paul Ryan.
