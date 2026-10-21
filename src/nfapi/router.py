from dataclasses import dataclass

MARKER = ">"
BUILDS = "builds"
SECTIONS = (BUILDS, "env", "settings")


@dataclass(frozen=True)
class Route:
    page: str
    text: str = ""
    site: str = ""
    deploy: str = ""
    path: str = ""
    parent: str = ""


def drill(path: str, ref: str) -> str:
    if not path:
        return f"{ref} {MARKER} "
    return f"{path} {MARKER} {ref} "


def _segments(query: str) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for word in query.split():
        if word == MARKER:
            segments.append([])
        else:
            segments[-1].append(word)
    return segments


def _join(*parts: str) -> str:
    return f" {MARKER} ".join(parts)


def parse(query: str) -> Route:
    segments = _segments(query)
    if len(segments) == 1 or not segments[0]:
        words = [word for segment in segments for word in segment]
        return Route("sites", " ".join(words))
    site = segments[0][0]
    rest = segments[1:]
    section = rest[0][0] if rest[0] else ""
    if section not in SECTIONS:
        words = [word for segment in rest for word in segment]
        return Route("site", " ".join(words), site, path=site)
    path = _join(site, section)
    deeper = rest[1:]
    if section == BUILDS and deeper and deeper[0]:
        deploy = deeper[0][0]
        words = deeper[0][1:] + [word for segment in deeper[1:] for word in segment]
        return Route("deploy", " ".join(words), site, deploy, _join(path, deploy), path)
    words = rest[0][1:] + [word for segment in deeper for word in segment]
    return Route(section, " ".join(words), site, path=path, parent=site)
