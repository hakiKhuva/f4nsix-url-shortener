### Endpoints

You can request to following endpoints to perform operations as described below

| Endpoint | Method | Description | Limit |
| -------- | ------ | ----------- | ----- |
| {{ url_for('API.shorten_url') }} | POST | create shorten urls | 30 requests per 60 seconds
| {{ url_for('API.all_urls') }} | GET | get all shorten urls | 30 requests per 60 seconds
| {{ url_for('API.track_or_delete_the_url', tracking_id="(url-tracking-id)") }} | GET, DELETE | get information about url or delete the url | 10 requests per 60 seconds

-----

All API requests requires an API key, you can create one by *[creating an account]({{ url_for('Auth.index') }})*, make sure you add it in the Headers of the request as `x-api-key`
```
Headers['x-api-key'] = "your api key"
```

-----

### POST {{url_for('API.shorten_url')}}

Generate a shorten url from long url.

#### Parameters:
- url : long url that to be shorten

```
# API request in Python
# pip install requests

import requests

API_KEY = "<your_api_key>" # replace your api key here
URL = "https://github.com/hakiKhuva" # replace the url here
req = requests.post("{{ url_for('API.shorten_url') }}", json={"url": URL}, headers={'x-api-key': API_KEY})

print(req.status_code) # status code of the response
print(req.json()) # response in json
```

```
# response returned by server if all values are set properly
{
    'data': {
        'code': '<shorten_code>',
        'shorten_url': '<shorten_url>',
        'tracking_id': '<tracking_id>'
    },
    'status': 'ok'
}
```

-----

### GET {{url_for('API.all_urls')}}

Returns all shorten URLs created using passed **api key**

```
# API request in Python
# pip install requests

import requests

API_KEY = "<your_api_key>" # replace your api key

req = requests.get("{{ url_for('API.all_urls') }}", headers={'x-api-key': API_KEY})

print(req.status_code)
print(req.json())
```

```
# response returned by server if all values are set properly
{
    'current_page': <number>,
    'data': [
        {
            'destination': '<url_destination>',
            'shorten_url': '<shorten_url>',
            'tracking_id': '<tracking_id>'
        },
        ...
    ],
    'pages': <number>,
    'status': 'ok',
    'total_links': <number>
}
```

-----

### GET {{url_for('API.track_or_delete_the_url', tracking_id="(tracking_id)")}}

Get the details about shorten url using tracking id. Total clicks, referrers, countries, etc. data is returned.

```
# API request in Python
# pip install requests

import requests

API_KEY = "<your_api_key>" # your api key
TRACKING_ID = "<tracking_id>" # tracking id of the shorten url

req = requests.get("{{url_for('API.track_or_delete_the_url', tracking_id='')}}{}".format(TRACKING_ID), headers={'x-api-key': API_KEY})

print(req.status_code)
print(req.json())
```


```
# response returned by server if all values are set properly
{
    "data": {
        "clicks": <number>,
        "countries": <dict>,
        "referrers": <dict>,
        "seven_days_clicks": [
            {
                "clicks": <number>,
                "date": "<date>"
            },
            ...
            {
                "clicks": <number>,
                "date": "<date>"
            }
        ]
    },
    "date": "<date in ISO format>",
    "destination": "<url_destination>",
    "shorten_link": "<shorten_url>",
    "status": "ok"
}
```

-----

### DELETE {{url_for('API.track_or_delete_the_url', tracking_id="(tracking_id)")}}

Delete the shorten URL using tracking id if it's no longer use.

***Note:You can only delete the url that is created using the API key**

```
import requests

API_KEY = "<your_api_key>" # your api key
TRACKING_ID = "<tracking_id>" # tracking id of the shorten url

req = requests.delete("{{ url_for('API.track_or_delete_the_url', tracking_id='') }}{}".format(TRACKING_ID), headers={'x-api-key': API_KEY})

print(req.status_code)
print(req.json())
```

```
# response returned by server if all values are set properly
{
    'destination': '<url_destination>',
    'shorten_url': '<shorten_url>',
    'status': 'ok'
}
```