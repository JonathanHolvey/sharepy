# Simple SharePoint authentication for Python

This library will handle authentication for your sharepoint site, allowing you to make straightforward HTTP requests from Python. The `get()`, `post()` and `getfile()` methods are wrapped around the commonly used `requests` module, meaning that returned objects are familliar, easy to work with and well documented. 

## Initiate a SharePoint session:

```python
import sharepoint as sp
s = sp.Session("example.sharepoint.com")
```

You will be prompted to enter your username and password, which are used to request an STS token from Microsoft. An authentication cookie and request digest token are then requested and saved to properties for later use. The digest token will be refreshed automatically as it expires.

## Make an API call:

```python
r = s.get("https://example.sharepoint.com/_api/web/lists/GetByTitle('Test Library')")
```

This will return a `requests` object. See the [requests documentation](http://docs.python-requests.org/en/master/) for details. The `get()` and `post()` methods send an `Accept: application/json; odata=verbose` header with all requests, so API responses will be formatted as JSON.

Headers can be added or overridden by supplying a dictionary to the `get()` method:

```python
r = s.get("https://example.sharepoint.com/_api/...", headers = {"Accept": "application/atom+xml"})
```

Additionally, POST requests can made by specifying the `data` attribute in the `post()` method:

```python
r = s.post("https://example.sharepoint.com/_api/...", data = "{'Title': 'New test item'}")
```

## Download a file:

```python
r = s.getfile("https://example.sharepoint.com/Test%20Library/Test%20File.pdf")
```

This will download the file to the current directory and return a `requests` object. Alternatively you can specify a location to save the file to:

```python
r = s.getfile("https://example.sharepoint.com/Test%20Library/Test%20File.pdf", "downloads/file.pdf")
```

## Useful reading

- Constructing SharePoint API calls: [SharePoint REST API documentation](https://msdn.microsoft.com/en-us/library/office/dn292552.aspx)
- Handling JSON objects in Python: [Python JSON module documentation](https://docs.python.org/3.4/library/json.html)

## Credits

1. The authentication method used here is based on [this post](https://allthatjs.com/2012/03/28/remote-authentication-in-sharepoint-online/) by Luc Stakenborg.
2. Additional help regarding request digests from sadegh's comment on [this post](http://paulryan.com.au/2014/spo-remote-authentication-rest/) by Paul Ryan.
