from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from os.path import exists
from sys import exit

from logzero import setup_logger

from sprints.Lab01S01 import Query as sprint_01

l = setup_logger(name="main", level=WARNING)

# Loading token string
_token_file = "graphql.token"
l.info(f"Loading GitHub GraphQL token from {_token_file}")
if exists(_token_file):
    with open(_token_file, "r") as t:
        _token = t.read()
else:
    l.warning(f"Token file ({_token_file}) not found. Asking for user input...")
    _token = input("Insert token string: ")

# Stripping blanks from token
_token = _token.strip()

# Checking token string
_token_length = 40
l.debug(f"_token='{_token}'; len(_token)={len(_token)};")
if len(_token) != _token_length:
    l.error(
        f"Provided token length ({len(_token)}) does not match "
        f"expected length ({_token_length})!"
    )
    exit(1)

# Defining request parameters
url = "https://api.github.com/graphql"
headers = {
    "Accept": "application/vnd.github.v4.idl",
    "Authorization": f"bearer {_token}",
}

# Running HTTP POST request
query = sprint_01(url, headers)
response = query.response

# Checking if HTTP POST request was successful
if response.status_code != 200:
    l.error(f"HTTP POST request failed! Status code: {response.status_code}")
    exit(1)
if response.status_code == 200 and "errors" in response.json():
    l.error(
        f"HTTP POST request failed!"
        f"\nErrors:"
        f"\n{[err['message'] for err in response.json()['errors']]}"
    )
    exit(1)

# Printing request response
print(f"Raw JSON response: {response.json()}")
