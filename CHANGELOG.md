# SharePy changelog

## v2.0.0 - 5 February 2022

Previously released as v2.0.0-beta.1 in January 2021.

A major refactor of SharePy to provide a standard [Requests auth](https://requests.readthedocs.io/en/master/user/authentication/#new-forms-of-authentication) interface.

- Converted the existing SharePoint Online authentication to a Requests auth class
- Added ADFS auth to compliment the default SharePoint Online authentication. Thanks to @joemeneses
- Added automatic authentication method detection for `sharepy.connect()`
- Added version checking for saved session objects. Major version number changes invalidate a session
- Removed `auth_tld` argument from `sharepy.connect()` and replaced with an `login_url` property in auth classes
- Removed connection status messages and added Python exceptions when errors are encountered
- Fixed session files not being closed when reading and writing
- Fixed missing dependencies in PyPI package
- Added `setup.py` script to repository

## v1.3.0 - 28 June 2018

- Added option to specify top level domain of authentication URL
- Changed status messages to display errors from authentication response

## v1.2.0 - 23 February 2018

- Added the option to use a username and password in `sharepy.connect()`. Thanks to @capps1994
- Changed status messages so they can be printed on a single line in consoles that support it

## v1.1.3 - 9 November 2017

- Bumped version number to fix PyPI release

## v1.1.2 - 7 November 2017

- Updated readme

## v1.1.1 - 26 October 2017

- Added license file and fixed typos in readme

## v1.1.0 - 18 June 2017

- Added support for usernames and passwords with special characters in SAML templates

## v1.0.0 - 26 April 2017

Initial release
