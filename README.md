***This project is no longer maintained***

# F4NSIX URL Shortener

URL shortener is a tool that used to generate shorten URL from long URL.

This project is of URL shortener and has following features:

- Shorten URL
- QRCode generator
- Track shorten URL
    - Total clicks
    - Devices
    - OS
    - Browsers
    - Referrers
    - Countries
    - Past days/hours clicks info
- Account login(GitHub)
- API (access with API key)
    - Previous API requests
- Requests are stored to track users

## REQUIREMENTS

- [DATABASE_URI](https://neon.tech/) (PostgreSQL)
- [IPINFO.IO API TOKEN](https://ipinfo.io/)
- [GitHub OAuth ID and Secret](https://github.com/settings/applications/new)
- [CLARITY ID](https://clarity.microsoft.com/) (Optional)


## Install and set variables

### Install the requirements using pip

```
pip install -r requirements.txt
```

### Set following environment variables
```python
# for app
SECRET_KEY

# url to database to store data
DATABASE_URI

# to track user geolocation
IPINFO_API_TOKEN

# for github login
GITHUB_AUTH_CLIENT_ID
GITHUB_AUTH_CLIENT_SECRET

# to track usage of website
CLARITY_ID
```

## Run the web app
```
flask run
```
