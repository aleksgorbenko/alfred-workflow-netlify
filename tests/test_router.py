from router import Route, drill, parse


def test_empty_query_lists_sites() -> None:
    assert parse("") == Route("sites")


def test_text_without_marker_filters_sites() -> None:
    assert parse("my site") == Route("sites", text="my site")


def test_site_name_before_marker_opens_site() -> None:
    assert parse("my-site > ") == Route("site", site="my-site", path="my-site")


def test_unknown_word_after_site_filters_site_rows() -> None:
    route = parse("my-site > bui")
    assert route == Route("site", text="bui", site="my-site", path="my-site")


def test_section_opens_with_back_path() -> None:
    route = parse("my-site > builds main")
    assert route == Route(
        "builds",
        text="main",
        site="my-site",
        path="my-site > builds",
        parent="my-site",
    )


def test_env_and_settings_are_sections() -> None:
    assert parse("my-site > env").page == "env"
    assert parse("my-site > settings").page == "settings"


def test_deploy_after_builds_opens_deploy() -> None:
    route = parse("my-site > builds > d1 commit")
    assert route == Route(
        "deploy",
        text="commit",
        site="my-site",
        deploy="d1",
        path="my-site > builds > d1",
        parent="my-site > builds",
    )


def test_empty_segment_after_builds_stays_on_builds() -> None:
    assert parse("my-site > builds > ").page == "builds"


def test_segment_after_env_becomes_text() -> None:
    route = parse("my-site > env > API")
    assert route.page == "env"
    assert route.text == "API"


def test_drill_appends_a_segment() -> None:
    assert drill("", "my-site") == "my-site > "
    assert drill("my-site", "builds") == "my-site > builds "
