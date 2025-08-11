# locustfile.py
from locust import HttpUser, task, between


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

    def on_start(self):
        response = self.client.post('/api/token/', {'email': 'tenant@example.com', 'password': 'testpass'})
        if response.status_code == 200:
            self.token = response.json()['access']
        else:
            self.token = None

    @task(4)
    def search_listings(self):
        if self.token:
            self.client.get('/api/listings/?search=Berlin&price_min=50&amenities=WiFi', headers={'Authorization': f'Bearer {self.token}'})

    @task(2)
    def list_bookings(self):
        if self.token:
            self.client.get('/api/bookings/', headers={'Authorization': f'Bearer {self.token}'})

    @task(1)
    def create_review(self):
        if self.token:
            self.client.post('/api/reviews/', json={'booking': 1, 'rating': 5, 'comment': 'Good'}, headers={'Authorization': f'Bearer {self.token}'})

    @task(1)
    def get_analytics(self):
        if self.token:
            self.client.get('/api/analytics/', headers={'Authorization': f'Bearer {self.token}'})

    @task(1)
    def view_analytics_csv(self):
        if self.token:
            self.client.get('/api/analytics/export/', headers={'Authorization': f'Bearer {self.token}'})