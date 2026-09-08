from menu import build_items


def test_build_items_returns_three_fixed_rows():
    items = build_items()
    assert [i["title"] for i in items] == [
        "Builds",
        "Environment Variables",
        "Settings",
    ]


def test_build_items_sets_site_action_variable_per_row():
    items = build_items()
    assert [i["variables"]["SITE_ACTION"] for i in items] == [
        "builds",
        "envvars",
        "settings",
    ]


def test_build_items_all_valid():
    assert all(i["valid"] for i in build_items())
