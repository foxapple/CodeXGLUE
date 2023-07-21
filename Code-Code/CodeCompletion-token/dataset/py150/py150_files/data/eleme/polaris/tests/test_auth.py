import unittest

from _fixtures import PolarisFixture


class PolarisAuthTest(PolarisFixture):

    def test_index(self):

        rv = self.app.get('/')
        content = rv.data.decode(rv.charset)

        # assert csrf token enabled.
        assert "csrf_token" in content
        # assert page 200
        assert "Polaris - Dashboard made easy" in content

    def test_auth(self):
        # test signup
        self.signup()
        assert self._is_login()

        # test logout
        self.logout()
        assert self._is_logout()

        # test login
        self.login()
        assert self._is_login()
        self.logout()

        # test failed login
        self.login("nonexists", "nopwd")
        assert self._is_logout()

if __name__ == '__main__':
    unittest.main()
