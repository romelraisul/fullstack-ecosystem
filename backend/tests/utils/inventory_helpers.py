from backend.app.main import app


def set_inventory(systems: list[dict]):
    app.state.systems_inventory = systems


def minimal_quantum_inventory():
    return [
        {
            "slug": "qcae",
            "api_base": "http://local/qcae",
            "category": "quantum",
            "maturity": "stable",
        },
        {
            "slug": "qdc",
            "api_base": "http://local/qdc",
            "category": "quantum",
            "maturity": "stable",
        },
    ]
