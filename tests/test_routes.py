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


class TestDashboard:
    def test_dashboard_unauthenticated_redirects_to_landing(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    def test_dashboard_wrong_role_returns_403(self, client):
        with client.session_transaction() as sess:
            sess["user"] = "viewer@askfleets.com"
            sess["role"] = "viewer"
        response = client.get("/dashboard")
        assert response.status_code == 403

    def test_dashboard_authenticated_returns_200(self, client):
        with client.session_transaction() as sess:
            sess["user"] = "admin@askfleets.com"
            sess["role"] = "admin"
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
