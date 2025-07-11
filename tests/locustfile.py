### `locustfile.py`

from locust import HttpUser, between, task


class MietSystemUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def get_listings(self):
        self.client.get("/api/listings/?city=Berlin&price_min=50&price_max=200")

    @task(2)
    def get_listing_detail(self):
        self.client.get("/api/listings/1/")

    @task(1)
    def search_listings(self):
        self.client.get("/api/listings/?q=apartment")

    def on_start(self):
        response = self.client.post(
            "/api/users/auth/token/",
            {"email": "test@example.com", "password": "pass123"},
        )
        if response.status_code == 200:
            self.client.headers.update(
                {"Authorization": f"Bearer {response.json()['access']}"}
            )
