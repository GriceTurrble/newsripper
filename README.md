# Rip the News

Library of web scrapers designed to extract article contents, remove unwanted scripting, and output a simple Bootstrap layout, making that content more readable (and, yes, bypassing paywalls).

## Note on copyrights

This package runs a web instance that allows the user to copy content from the web, and presents it without original trademarks or images. These sites would very much like for you to view their content live on their websites (and, I presume, pay them for their hard work).

**Do not re-host article content that has been ripped using this package, as you will be in violation of the copyrights by the original content creators.** This code is intended solely for personal use, as a means to copy and archive articles that are publicly available on the web.

And please consider paying for the news content you consume the most. You can't read them if they can't write it!

## Usage

1. Checkout the repo.
2. Install requirements using `pip install -r requirements.txt`
3. Run `python manage.py migrate`.
4. Run the site: `python manage.py runserver`.

When running, open `localhost:8000` and start chucking Article URLs into the "Rip a new one" input in the top-right. If the rip is successful, the article will be opened, and it will be available for perusal from the front page list.

If an article was already ripped from the same URL, it will not be re-ripped: the original rip will be opened, instead. You can choose to manually re-rip the article using the controls inside the article page, or delete it and rip it again manually. Re-ripping may be beneficial if the original story has been updated since the original rip time.

*Currently, there is no rip versioning. If you re-rip the same article, the prior rip will be lost. This could be added in future!*

### Proxy note

The scripts attempt to automatically bypass proxies you may be running on, by calling `urllib.request.getproxies()` to pull in proxy data. If that's not sufficient, you may need to do some more work to customize it.

Refer to **PROXY_SETUP.md** if you need assistance here.

## Scrapers included

- New York Times (nyt.com)
- Washington Post (washingtonpost.com)
- CNN (cnn.com)
- Politico (politico.com)
- The Hill (thehill.com)
