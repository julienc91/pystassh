## 1.2.2 - 2022-05-17

List of changes
* fix infinite loop that could occur during a read operation (thanks @richvdh!)

## 1.2.1 - 2022-04-05

List of changes
* fix an error occurring when running too many commands (thanks @reivilibre!)

## 1.2.0 - 2021-06-26

List of changes
* NEW: `privkey_file` parameter on the `Session` constructor to use a custom key (thanks @eldipa!)
* NEW: API to use a `Channel` in shell mode (thanks @eldipa!)

## 1.1.0 - 2021-06-25

List of changes
* fix memory leaks (thanks @eldipa!)
* BREAKING: drop support for python < 3.6
* remove test dependency on `mock`

## 1.0.1 - 2016-08-02

List of changes
* bigger buffer size for better performances
* decoding errors when fetching stdout and stderr used to raise exceptions but are now ignored
* added `__version__`, `__author__` and `__license__` information
* requirements updated in the documentation, `libffi-dev` was missing

## 1.0 - 2016-07-30

Initial version of `pystassh`.
