import requests

headers = {
    "Host": "www.amazon.com",
    "device-memory": "8",
    "sec-ch-device-memory": "8",
    "dpr": "2",
    "sec-ch-dpr": "2",
    "viewport-width": "1260",
    "sec-ch-viewport-width": "1260",
    "rtt": "200",
    "downlink": "10",
    "ect": "4g",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-ch-ua-platform-version": "\"10.0.0\"",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "referer": "https://www.amazon.com/errors/validateCaptcha",
    "accept-language": "zh-CN,zh;q=0.9",
    "priority": "u=0, i"
}
cookies = {
    "session-id": "146-3789168-9900125",
    "lc-main": "en_US",
    "i18n-prefs": "USD",
    "ubid-main": "130-7895899-3319940",
    "session-id-time": "2082787201l",
    "skin": "noskin",
    "x-amz-captcha-1": "1753588988324049",
    "x-amz-captcha-2": "uK6Lk1w9SspQJJC6VY5PHA==",
    "session-token": "+ksMYRpI6n++l1+tEw+274bURT/O62krugR0Lck9+G5JtVUB2PcmJErVX84APa4Wh0kOi+K/NwMAxcoIj/D/WZxZ7UeK7KSeFndRszLbfNoluk2S2JHMrCdIUa7o5eLdaaVqbF0yTe/XIxUR1AeasOdIMOnsqqI6GJ6k5fQKgEQOuu4KIHoVZ8YriQCxnfIMpHYXvdP7G3HGxByaifyuBq92TLkocNphT/Q4HLv1rZQgZjWwO2epfbsOiSZtZvOjqY2N9WBqqSmt3Jcstg8jgAUEDYrmdnGhSHW+sjgoK94pcIlhkHrQvQ8x+jxX4rDTgvf3jQ5dD1M+wLOfIFT4xg7/aBYS/r2I",
    "rxc": "AJneQn3ulzt1x6xrr/8",
    "csm-hit": "tb:M4TXGYH9PASAJGH9NT7J+s-M4TXGYH9PASAJGH9NT7J|1754227645517&t:1754227645517&adb:adblk_no"
}
url = "https://www.amazon.com/errors/validateCaptcha"
params = {
    "amzn": "Ki3NnPzbRy3WD6bDMlcYTQ==",
    "amzn-r": "/",
    "field-keywords": "GNBCRA"
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)
