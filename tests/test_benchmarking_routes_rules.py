import importlib
import os
import unittest
from unittest.mock import patch


BASE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_DB": "goia_test",
    "POSTGRES_USER": "goia",
    "POSTGRES_PASSWORD": "goia",
    "REDIS_URL": "redis://localhost:6379/0",
    "FIRST_ADMIN_EMAIL": "admin@example.com",
    "FIRST_ADMIN_PASSWORD": "secret123",
    "MODEL_ACCESS_CREDENTIALS_SECRET_KEY": "credential-secret",
    "APP_CORS_ORIGINS": "",
}


class BenchmarkingRoutesRulesTests(unittest.TestCase):
    def load_main(self):
        with patch.dict(os.environ, BASE_ENV, clear=True):
            import app.core.config as config_module
            import app.main as main_module

            importlib.reload(config_module)
            return importlib.reload(main_module)

    def test_models_router_is_the_official_model_registration_surface(self):
        main = self.load_main()
        route_methods = {
            (route.path, tuple(sorted(route.methods)))
            for route in main.app.routes
            if hasattr(route, "methods")
        }
        route_paths = {path for path, _ in route_methods}

        self.assertIn(("/models", ("GET",)), route_methods)
        self.assertIn(("/models", ("POST",)), route_methods)
        self.assertIn(("/models/{model_id}", ("DELETE",)), route_methods)
        self.assertIn(("/models/{model_id}", ("PUT",)), route_methods)
        self.assertNotIn("/modelos/modelo", route_paths)


if __name__ == "__main__":
    unittest.main()
