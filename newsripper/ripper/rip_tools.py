"""Tools related to the ripper, but with no better place to live."""

from dataclasses import dataclass
from typing import Union
import urllib.parse
import re

from dateutil.zoneinfo import tzfile
import pytz

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


@dataclass
class TargetTag:
    tagtype: str
    properties: dict


def adjust_anchors(soup):
    """Edit all anchors in the article body with new `target` and `rel` properties."""
    for anchor in soup.find_all("a"):
        anchor["target"] = "_blank"
        anchor["rel"] = "nofollow"


def get_url_domain(url: str):
    """Parses the domain from the given URL."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc
    return re.sub(r"^www\.", "", domain)


def remove_tags(soup, *tags: Union[str, TargetTag]):
    """Extract each type of selected tag from the document."""
    for tag in tags:
        if isinstance(tag, TargetTag):
            search_args = (tag.tagtype, tag.properties)
        else:
            # simple str argument
            search_args = (tag,)
        for content in soup.find_all(*search_args):
            content.extract()


def url_is_valid(url: str) -> bool:
    """Check that a URL is valid and can be reached."""
    validate = URLValidator()
    try:
        validate(url)
    except ValidationError as exc:
        return False
    return True
