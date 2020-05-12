"""Command `new_rip`, rips a news article from a URL."""

from django.core.management.base import BaseCommand
from ripper.views import _process_article_from_url
from ripper.rip_tools import url_is_valid


class Command(BaseCommand):
    help = "Rips a news article, given its URL passed as an argument."

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            action="store",
            nargs="?",
            help="The URL for an article to be ripped",
        )

    def handle(self, *args, **options):
        """Handler: Rips a news article, given its URL passed as an argument."""
        url = options["url"]
        self.stdout.write(f"  Attempting to parse:\n  '{url}'...")
        if not url_is_valid(url):
            self.stderr.write(
                self.style.ERROR(
                    f"    '{url}' is not a valid URL.\n    No new processing performed."
                )
            )
            return

        article, created = _process_article_from_url(url)
        if not created:
            self.stdout.write(
                self.style.WARNING(
                    (
                        f"    Article already exists, ripped at {article.rip_time}.\n"
                        "    No new processing performed."
                    )
                )
            )
        else:
            article.save()
            self.stdout.write(self.style.SUCCESS("  Article ripped successfully."))
