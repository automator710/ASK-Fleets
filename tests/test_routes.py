class TestLanding:
    def test_landing_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_landing_contains_brand_name(self, client):
        response = client.get("/")
        assert b"ASKFLEETS" in response.data


class TestFeatures:
    def test_features_returns_200(self, client):
        response = client.get("/features")
        assert response.status_code == 200


class TestLogin:
    def test_login_get_returns_200(self, client):
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_valid_credentials_redirects(self, client):
        response = client.post("/login", data={
            "email": "admin@askfleets.com",
            "password": "fleet123",
        })
        assert response.status_code == 302
        assert "/dashboard" in response.headers["Location"]

    def test_login_invalid_credentials_returns_401(self, client):
        response = client.post("/login", data={
            "email": "wrong@example.com",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    def test_login_missing_fields_returns_400(self, client):
        response = client.post("/login", data={"email": "", "password": ""})
        assert response.status_code == 400


class TestDashboard:
    def test_dashboard_unauthenticated_redirects_to_login(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_dashboard_authenticated_returns_200(self, client):
        with client.session_transaction() as sess:
            sess["user"] = "admin@askfleets.com"
        response = client.get("/dashboard")
        assert response.status_code == 200


class TestLogout:
    def test_logout_clears_session_and_redirects(self, client):
        with client.session_transaction() as sess:
            sess["user"] = "admin@askfleets.com"

        response = client.get("/logout")
        assert response.status_code == 302
        assert "/" in response.headers["Location"]

        with client.session_transaction() as sess:
            assert "user" not in sess
