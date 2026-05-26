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
    def test_dashboard_unauthenticated_redirects_to_login(self, dash_client):
        response = dash_client.get("/dashboard")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_dashboard_wrong_role_returns_403(self, dash_client):
        with dash_client.session_transaction() as sess:
            sess["user"] = "viewer"
            sess["role"] = "viewer"
        response = dash_client.get("/dashboard")
        assert response.status_code == 403

    def test_dashboard_authenticated_returns_200(self, dash_client):
        with dash_client.session_transaction() as sess:
            sess["user"] = "admin"
            sess["role"] = "admin"
        response = dash_client.get("/dashboard")
        assert response.status_code == 200


class TestLogout:
    def test_logout_clears_session_and_redirects(self, dash_client):
        with dash_client.session_transaction() as sess:
            sess["user"] = "admin"

        response = dash_client.get("/logout")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

        with dash_client.session_transaction() as sess:
            assert "user" not in sess
