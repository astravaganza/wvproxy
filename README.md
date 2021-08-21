# wvproxy

Widevine CDM API

## Setup
1. Install Python 3.6 or newer and [Poetry](https://python-poetry.org/)
2. Install Python package dependencies using `poetry install`
3. Activate the virtual environment using `poetry shell`
4. Run the Flask web app using `python wvproxy.py` (this part can run on any OS)
5. Open the web app on a Windows computer with Chrome and [widevine-l3-guesser](https://github.com/Satsuoni/widevine-l3-guesser) installed and leave it running
6. (Optional but recommended) Put the API behind a reverse proxy such as nginx for HTTPS support
7. Put one or more users and keys in `authorized_users.txt` in TSV (tab-separated values) format:
```
alice	e50af8c5-02ef-4546-8449-77ab4cf8a271
bob	5fdb1375-e529-4f51-a8a4-9296bfadedfa
```

## API request format

### Get challenge

#### Request
```json
{
  "method": "GetChallenge",
  "params": {
    "init": "<pssh as base64>",
    "cert": "<service certificate as base64>"
  },
  "token": "<user key from authorized_users.txt>"
}
```

#### Response
```json
{
  "status_code": 200,
  "message": {
    "session_id": "<unique session uuid>",
    "challenge": "<license request as base64>"
  }
}
```

### Get keys

#### Request
```json
{
  "method": "GetKeys",
  "params": {
    "session_id": "<unique session uuid>",
    "cdmkeyresponse": "<license response as base64>"
  },
  "token": "<user key from authorized_users.txt>"
}
```

#### Response
```json
{
  "status_code": 200,
  "message": {
    "keys": [
      {
        "kid": "<key id as hex>",
        "key": "<key as hex>"
      },
      {
        "kid": "<key id as hex>",
        "key": "<key as hex>"
      },
      ...
    ]
  }
}
```

### Error responses
```json
{
  "status_code": 4XX|5XX,
  "message": "<error description>"
}
```

## Disclaimer
This project is purely for educational purposes. The author claims no responsibility for what you do with it.
