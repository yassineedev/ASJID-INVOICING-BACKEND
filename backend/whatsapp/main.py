import requests

ACCESS_TOKEN = "EAAPGqAPBV20BSPAlu6Fj6Jl0oVvZA9pSZBsb3NIxAZACa6ehrJTL5956Qfhs9eZAuAWYeYZBKFXWZC1SBsMB5tV2XeyPB2jfvvgIwQVvmD4pAEjX6LgXbi8pflVzrdBPlugTQTEAT3wptqOEazdJ1NUFIvbFiSTRz8fGcaelno6ZBPC5Eb2nIeesjBB7ivqhJLHmY0RSb4xoyZBQ2FHLBlojrUmULB4LjGZBe5s3CZAWYex4TnntFDImaZBfTbup7ptty418tvMppQjnYHq1yY9JW6rUorhZCAZDZD"
PHONE_NUMBER_ID = "1278161872039401"

url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "messaging_product": "whatsapp",
    "to": "212611409417",
    "type": "text",
    "text": {
        "body": "Hello! This is my first message sent using the WhatsApp Cloud API 🚀"
    }
}

response = requests.post(url, headers=headers, json=payload)

print("Status Code:", response.status_code)
print("Response:")
print(response.json())