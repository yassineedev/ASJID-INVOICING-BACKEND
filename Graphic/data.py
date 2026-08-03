import requests


class WaterApiClient:
    def __init__(self, base_url="https://script.google.com/macros/s/AKfycbzR4ayLk5HUYAFpilIWUm7ay9ga_5IcwwtOyUc50_MC9hkt5ueYeHyz_HniFGXo5Hs/exec?action=getClients"):
        self.base_url = base_url

    def fetch_users(self):
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            return None, str(e)


w = WaterApiClient()
print(w.fetch_users())