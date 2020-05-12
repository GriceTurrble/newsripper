"""Models for ripper app."""

import urllib.parse
import urllib.request

from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector
import requests
import re

from dateutil.parser import parse
from dateutil.tz import gettz

from django.db import models
from django.urls import reverse as reverse_url
from django.core.validators import URLValidator
from django.utils import timezone

from .tools import adjust_anchors
from .tools import remove_tags
from .tools import TargetTag
from .tools import get_url_domain
from .tools import url_is_valid
from .exceptions import URLDoesNotExist


TZINFOS = {
    "EST": gettz("US/Eastern"),
    "est": gettz("US/Eastern"),
    "ET": gettz("US/Eastern"),
    "et": gettz("US/Eastern"),
}
PARAGRAPHS_AND_HEADERS = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]


def get_model_for_url(url):
    DOMAIN_TO_CLASS = {
        "cnn.com": CNNArticle,
        "nytimes.com": NYTArticle,
        "washingtonpost.com": WAPOArticle,
        "politico.com": PoliticoArticle,
        "thehill.com": HillArticle,
    }
    domain = get_url_domain(url)
    return DOMAIN_TO_CLASS.get(domain, Article)


class ArticleQuerySet(models.QuerySet):
    """Custom QuerySet for Article model."""

    def get_by_url(self, url):
        """Gets an Article instance using the passed URL."""
        try:
            # Attempt to find the URL with no schema first, which should be more common
            article = self.get(url_no_schema=url)
        except self.model.DoesNotExist:
            # If that doesn't work, try .get with raw URL
            # If exception raises from here, let the calling method handle it.
            article = self.get(url=url)
        return article


class ArticleManager(models.Manager):
    """Custom Manager for Article model."""

    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)

    def get_by_url(self, url):
        return self.get_queryset().get_by_url(url)


class Article(models.Model):
    """Content for an Article, including logic to grab its contents via URL
    and produce output to be displayed within the site.
    """

    objects = ArticleManager()

    _REMOVE_TAGS_BASE = ["figure", "img", "aside", "script"]
    REMOVE_TAGS = []

    # Article contents
    title = models.CharField(max_length=255, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    byline = models.TextField(null=True, blank=True)
    time_str = models.CharField(max_length=255, null=True, blank=True)
    body_content = models.TextField(null=True, blank=True)
    article_time = models.DateTimeField(null=True, blank=True)
    manual = models.BooleanField(default=False)

    # URL and Domain details
    url = models.TextField(null=True, blank=True, validators=[URLValidator()])
    url_no_schema = models.TextField(null=True, blank=True)
    RIP_TYPE_UNKNOWN = "UNKNOWN"
    RIP_TYPE_CNN = "CNN"
    RIP_TYPE_NYT = "NYT"
    RIP_TYPE_WAPO = "WAPO"
    RIP_TYPE_POLITICO = "POLITICO"
    RIP_TYPE_HILL = "HILL"
    RIP_TYPE_CHOICES = (
        (RIP_TYPE_UNKNOWN, "<unknown>"),
        (RIP_TYPE_CNN, "CNN"),
        (RIP_TYPE_NYT, "New York Times"),
        (RIP_TYPE_WAPO, "Washington Post"),
        (RIP_TYPE_POLITICO, "Politico"),
        (RIP_TYPE_HILL, "The Hill"),
    )
    rip_type = models.CharField(
        max_length=9, choices=RIP_TYPE_CHOICES, default=RIP_TYPE_UNKNOWN
    )

    # Timing
    rip_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rip_type} - {self.title}"

    @property
    def time_str_for_template(self):
        return f'"{self.time_str}"'

    def get_absolute_url(self):
        return reverse_url("ripper:article_detail", args=(self.url_no_schema,))

    def parse_url(self):
        self.url_no_schema = re.sub(r"^https?://", "", self.url)

    def process(self):
        """Defines all steps to fully process this article,
        from the URL to final content.
        """
        self.parse_url()
        soup = self.get_the_soup()
        # Remove the base tags all articles should not have...
        remove_tags(soup, *self._REMOVE_TAGS_BASE)
        # ...then specific tags defined for an article subclass
        remove_tags(soup, *self.REMOVE_TAGS)
        self.extract_content(soup)
        self.parse_time_str()

    def parse_time_str(self):
        """Uses dateutil to attempt to parse the time_str into a datetime object."""
        if not self.time_str:
            # Short circuit
            return
        test_str = self.time_str.lower()
        if "update" in test_str:
            test_str = re.search(r"updated?(.*)$", test_str).group(1)
        test_str = test_str.replace(" et", " est").replace(" est", " EST")
        try:
            parsed = parse(test_str, tzinfos=TZINFOS)
        except ValueError as exc:
            print(exc)
            return
        self.article_time = parsed

    def get_the_soup(self):
        if self.url is None:
            # Early exit
            return

        resp = requests.get(self.url, proxies=urllib.request.getproxies())
        http_encoding = (
            resp.encoding
            if "charset" in resp.headers.get("content-type", "").lower()
            else None
        )
        html_encoding = EncodingDetector.find_declared_encoding(
            resp.content, is_html=True
        )
        encoding = html_encoding or http_encoding
        soup = BeautifulSoup(resp.content, "lxml", from_encoding=encoding)
        adjust_anchors(soup)
        return soup

    def extract_content(self, soup):
        """Extracts article contents.

        Method should be overwritten by subclassed proxy models,
        with a `super()` call to get shared elements.
        """
        self.title = soup.title.text

    @property
    def summary_part(self):
        if self.summary:
            return self.summary
        soup = BeautifulSoup(self.body_content, "lxml")
        return soup.find_all("p")[0].text

    def copy_article(self, other_article):
        """Given another Article instance, copy relevant article details
        to this instance.
        Useful when re-processing an article: a temporary one is generated, but not
        saved in the database.
        """
        # List of fields that should be copied from `instance`.
        COPYABLE_FIELDS = [
            "title",
            "summary",
            "byline",
            "time_str",
            "body_content",
            "article_time",
            "rip_type",
        ]
        for field in COPYABLE_FIELDS:
            setattr(self, field, getattr(other_article, field))
        self.rip_time = timezone.now()


class NYTArticle(Article):
    """Article from New York Times."""

    class Meta:
        proxy = True

    def extract_content(self, soup):
        """Extraction logic for New York Times articles."""
        super().extract_content(soup)
        self.rip_type = self.RIP_TYPE_NYT
        self.title = soup.find("h1", {"itemprop": "headline"}).text
        summary_tag = soup.find("p", {"id": "article-summary"})
        if summary_tag:
            self.summary = summary_tag.text

        # Pick out sections in the body that we want
        body_section = soup.find("section", {"name": "articleBody"})
        body_content = []
        for div in body_section.find_all("div", {"class": "StoryBodyCompanionColumn"}):
            body_content.extend([x for x in div.find_all(PARAGRAPHS_AND_HEADERS)])
        self.body_content = "\n".join([str(x) for x in body_content])

        # Byline. Reserve the tag in order to find time data relative to it.
        byline_tag = soup.find("p", {"itemprop": "author"})
        self.byline = byline_tag.text

        # Find the time portions relative to the byline.
        time_tags = None
        for parent in byline_tag.parents:
            time_tags = parent.find_all("time")
            if time_tags:
                break

        if time_tags is not None:
            self.time_str = " ".join([x.text for x in time_tags])


class WAPOArticle(Article):
    """Article from the Washington Post."""

    class Meta:
        proxy = True

    REMOVE_TAGS = [
        # These appear to all be wrappers for advertisements, and occasionally for figures.
        TargetTag("div", {"class": "cb"}),
        # Interstitials are used for links to other articles, breaking the article flow.
        TargetTag("p", {"class": "interstitial"}),
    ]

    def extract_content(self, soup):
        """Extraction logic for Washington Post articles."""
        super().extract_content(soup)
        self.rip_type = self.RIP_TYPE_WAPO

        # Main parts
        self.title = soup.find("h1", {"class": "font--headline"}).text
        self.body_content = soup.find("div", {"class": "article-body"}).prettify()

        # There's a lot of extra text inside the author-names section, mainly tooltip info.
        # To get the simpler name output, we have to build it manually.
        authors = soup.find("div", {"class": "author-names"})
        byline = "By "
        author_names = []
        for author in authors.find_all("span", {"class": "author-name"}):
            author_names.append(author.text)
        self.byline = byline + (
            ", ".join(author_names) if author_names else "<Unknown>"
        )

        self.time_str = soup.find("div", {"class": "display-date"}).text


class CNNArticle(Article):
    """Article from CNN."""

    class Meta:
        proxy = True

    REMOVE_TAGS = [
        # Shit-ton of ad embeds.
        TargetTag("div", {"class": "ad"}),
        TargetTag("div", {"class": "el__embedded"}),
        # Instagram shit
        TargetTag("div", {"class": "el__leafmedia--instagram-aside"}),
        # "Read more" sections at the end
        TargetTag("div", {"class": "zn-body__read-more-outbrain"}),
        TargetTag("div", {"class": "zn-body__read-more"}),
        # More ad bullshit
        TargetTag("ul", {"class": "cn-zoneAdContainer"}),
    ]

    def extract_content(self, soup):
        """Extraction logic for CNN articles."""
        super().extract_content(soup)
        self.rip_type = self.RIP_TYPE_CNN

        # CNN puts all their paragraphs in `div.zn-body__paragraph` tags, which is dumb
        # Replace each one with a simpler `p` tag, by changing that tag's name
        # (the class is irrelevant, as we don't make changes based on it)
        for graf in soup.find_all("div", {"class": "zn-body__paragraph"}):
            graf.name = "p"

        # Main parts
        self.title = soup.find("h1", {"class": "pg-headline"}).text
        self.summary = ""
        self.body_content = soup.find("section", {"id": "body-text"}).prettify()

        # Byline. Reserve the tag in order to find time data relative to it.
        self.byline = soup.find("span", {"class": "metadata__byline__author"}).text
        self.time_str = soup.find("p", {"class": "update-time"}).text


class PoliticoArticle(Article):
    """Article from Politico."""

    class Meta:
        proxy = True

    REMOVE_TAGS = [
        # The topbar sits in the middle of stuff for some reason.
        # Probably not going to end up grabbing it, but just in case.
        TargetTag("div", {"class": "pop-up-bar"}),
        # Some sections that look like story content are "below" and "comments" sections.
        TargetTag("section", {"class": "below-article-section"}),
        TargetTag("section", {"class": "comments-section"}),
        # Some "section"s are used for ads.
        "section[data-ad-section]",
        # Literally an "ad" div. Good job.
        TargetTag("div", {"class": "ad"}),
    ]

    def extract_content(self, soup):
        """Extraction logic for Politico articles."""
        super().extract_content(soup)
        self.rip_type = self.RIP_TYPE_POLITICO

        # Title
        self.title = (
            soup.find("h2", {"class": "headline"})
            or soup.find("span", {"itemprop": "headline"})
        ).text

        # Summary
        summary = soup.find("p", {"class": "dek"})
        if summary is not None:
            self.summary = summary.text

        # Body
        body_content = soup.select("p.story-text__paragraph") or soup.select(
            "p:not(.byline):not(.timestamp)"
        )
        self.body_content = "\n".join([str(x) for x in body_content])

        # Byline
        self.byline = (
            soup.find("p", {"class": "story-meta__authors"})
            or soup.find("p", {"class": "byline"})
        ).text

        # Time string
        self.time_str = (
            soup.find("p", {"class": "story-meta__timestamp"})
            or soup.find("time", {"itemprop": "datePublished"})
        ).text


class HillArticle(Article):
    """Article from The Hill."""

    REMOVE_TAGS = [TargetTag("span", {"class": "rollover-people-block"})]

    class Meta:
        proxy = True

    def extract_content(self, soup):
        """Extraction logic for The Hill articles."""
        super().extract_content(soup)
        self.rip_type = self.RIP_TYPE_HILL

        self.title = soup.find("h1", {"id": "page-title"}).text

        # Byline and timestr are joined in the same element.
        # Split out the time_str, then use that to strip it from the byline text
        byline = soup.find("span", {"class": "submitted-by"})
        self.time_str = byline.find("span", {"class": "submitted-date"}).text
        self.byline = byline.text.replace(self.time_str, "").strip("- ")

        # Most of the body content can be found in `p` tags,
        # but a summary may be available in a preceding `div`,
        # which can mess things up.
        # Fortunately, it appears to all be wrapped up in some deep-nested
        # `div.field-item` tag beneath `div.field-name-body`. So we'll look there.
        body = soup.select("article.node-article div.field-name-body div.field-item")[0]
        self.summary = body.select("div:first-child")[0].text

        # body = soup.find("article", {"class": "node-article"})
        self.body_content = "\n".join(
            [str(x) for x in body.find_all(PARAGRAPHS_AND_HEADERS)]
        )
