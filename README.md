# SharePy - Simple SharePoint Online authentication for Python

This module will handle authentication for your SharePoint Online/O365 site, allowing you to make straightforward HTTP requests from Python. It extends the commonly used *Requests* module, meaning that returned objects are familliar, easy to work with and well documented. 

## Installation

SharePy can be installed from the Python Package Index, PyPI.

```
pip install sharepy
```

## Initiating a SharePoint session

```python
import sharepy
s = sharepy.connect("example.sharepoint.com")
```

You will be prompted to enter your username and password, which are used to request a security token from Microsoft. An access cookie and request digest token are then retrieved and saved to properties for later use. The digest token will be refreshed automatically as it expires.

A username and password can also be provided as arguments of the `connect` function, if prompts are not desirable.

## Making API calls

```python
r = s.get("https://example.sharepoint.com/_api/web/lists/GetByTitle('Test Library')")
```

This will return a *Requests* `response` object. See the [requests documentation](http://docs.python-requests.org/en/master/) for details. By default, the headers `Accept: application/json; odata=verbose` and `Content-type: application/json; odata=verbose` are sent with all requests, so API responses will be formatted as JSON where available.

Headers can be added or overridden by supplying a dictionary to the relevant method:

```python
r = s.get("https://example.sharepoint.com/_api/...", headers={"Accept": "application/atom+xml"})
```

The request will send a digest header, allowing modifications to be made to SharePoint objects.

### Downloading a file

```python
r = s.getfile("https://example.sharepoint.com/Library/Test%20File.pdf")
```

This will download the file to the current directory and return a `response` object. Alternatively you can specify a location to save the file to:

```python
r = s.getfile("https://example.sharepoint.com/Library/Test%20File.pdf", filename="downloads/file.pdf")
```

### Uploading a file

Successfully uploading a file to SharePoint is a complex task which is described in detail in [issue #4](https://github.com/JonathanHolvey/sharepy/issues/4).

The actual file upload can be achieved with the following code, where `filepath` is the path to the file to upload, `folder` is the library on the SharePoint server and `filename` is the name to give to the file on upload.

```python
with open(filepath, "rb") as f:
    data = f.read()

url = "https://example.sharepoint.com/GetFolderByServerRelativeUrl('{}')/Files/add(url='{}',overwrite=true)"
r = s.post(url.format(folder, filename), data=data, headers={"content-length": len(data)})
```

## Saving an authenticated session

Properties of the authentication session can be saved to a file using the `save` method, so the session can be used without having to re-authenticate each time a program is run:

```python
s.save()
```

Later, the `load` function can be used to restore the session:

```python
s = sharepy.load()
```

The default file name for saving and loading sessions is `sp-session.pkl`, however an alternative location can be provided as an argument to `save()` and `load()`.

## Advanced usage

### Requests authentication

SharePy implements Requests authentication classes that can also be used directly with Requests itself:

```python
import requests
import sharepy

auth = sharepy.auth.SharePointOnline(username="user@example.com")
auth.login(site="example.sharepoint.com")
r = requests.get("https://example.sharepoint.com", auth=auth)
```

Available authentication classes are:

- `SharepointOnline` - For normal SharePoint Online sites
- `SharepointADFS` - For ADFS-enabled sites

### Custom authentication URL

The authentication URL is detected automatically when using `sharepy.connect()`. If a different URL is required for a region-specific account, it can be specified by manually creating an auth object and setting its `login_url` property:

```python
import sharepy

auth = sharepy.auth.SharePointOnline(username="user@example.com")
auth.login_url = "https://login.microsoftonline.de/extSES.srf"
s = sharepy.SharePointSession("example.sharepoint.com", auth)
```

## Useful reading

- Constructing SharePoint API calls: [SharePoint REST API documentation](https://msdn.microsoft.com/en-us/library/office/dn292552.aspx)
- Handling JSON objects in Python: [Python JSON module documentation](https://docs.python.org/3.4/library/json.html)

## Licence

This software is distributed under the GNU General Public License v3. Copyright 2016-2021 Jonathan Holvey.

## Credits

1. The authentication method used here is based on [this post](https://allthatjs.com/2012/03/28/remote-authentication-in-sharepoint-online/) by Luc Stakenborg.
2. Additional help regarding request digests from sadegh's comment on [this post](http://paulryan.com.au/2014/spo-remote-authentication-rest/) by Paul Ryan.
3. Contributed code from @joemeneses for ADFS authentication.
