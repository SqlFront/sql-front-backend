import pytest

def test_admin_dependencies_importable():
    import sqladmin
    import itsdangerous
    import jinja2
    import plotly
    assert hasattr(sqladmin, "Admin")
    assert itsdangerous.__version__
    assert jinja2.__version__
    assert plotly.__version__

def test_admin_config_settings():
    from config import settings
    assert hasattr(settings, "ADMIN_USERNAME")
    assert hasattr(settings, "ADMIN_PASSWORD")
    assert hasattr(settings, "SECRET_KEY")
    assert settings.SECRET_KEY is not None

def test_src_config_compatibility():
    from src.config import settings
    assert hasattr(settings, "ADMIN_USERNAME")
    assert hasattr(settings, "ADMIN_PASSWORD")
    assert hasattr(settings, "SECRET_KEY")
