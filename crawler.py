import random

from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError

import subprocess
import os

import genanki

sign_model = genanki.Model(
  1980445846,
  'Simple Model',
  fields=[
    {'name': 'English'},
    {'name': 'Sign'},
    {'name': 'Category'},
  ],
  templates=[
    {
      'name': 'FromSign',
      'qfmt': '{{English}}',
      'afmt': '''{{English}} <hr id="answer"> {{Sign}}''',
    },
    {
      'name': 'FromSign',
      'qfmt': '{{Sign}}',
      'afmt': '{{English}} <hr id="answer"> {{Sign}}',
    }
  ])

sign_deck = genanki.Deck(
  1594228109,
  'SpreadTheSign')

categories_page = "https://www.spreadthesign.com/en.us/search/by-category/"

soup = BeautifulSoup(urlopen(categories_page))

soup.nav.replace_with("")
soup.find(id="footer").replace_with("")

categories = []
for a in soup.ul.find_all("a"):
    if a.next_sibling.next_sibling.name == "ul" and not a.next_sibling.next_sibling.text.strip():
        categories.append(a["href"])
    else:
        print("Skipped", a.text.strip(), a.next_sibling.next_sibling.text)

categories = iter(categories)
page = next(categories)
category_page = urljoin(categories_page, page)

lemmata = {}

media_files = []

def load_video(word_link, category):
    word_page = urljoin(categories_page, word_link)
    try:
        soup = BeautifulSoup(urlopen(word_page))
    except HTTPError:
        return

    soup.nav.replace_with("")
    soup.find(id="footer").replace_with("")
    content = soup.find(class_="search-result-content")
    word = content.h2.text.strip().replace("/", "⁄")
    lemma = word
    suffix = 1
    while lemma in lemmata:
        suffix += 1
        lemma = "{:} {:}".format(word, suffix)

    filename_mp4 = "{:}.mp4".format(lemma)
    filename = "{:}.gif".format(lemma)


    if content.video:
        if not os.path.exists(filename_mp4):
            video_url = content.video["src"]
            with urlopen(video_url) as video:
                with open(filename_mp4, "wb") as videofile:
                    r = video.read(2048)
                    while r:
                        videofile.write(r)
                        r = video.read(2048)
            print(".", end="")

        media_files.append(filename_mp4)

        note = genanki.Note(
            model=sign_model,
            fields=[word, "[sound:{:}]".format(filename_mp4), category])
        sign_deck.add_note(note)

        return lemma

words = []
while True:
    category_page = urljoin(category_page, page)
    url = urlparse(category_page)
    assert url.hostname == "www.spreadthesign.com"

    soup = BeautifulSoup(urlopen(category_page))
    soup.nav.replace_with("")
    soup.find(id="footer").replace_with("")
    try:
        soup.find(class_="breadcrumb").replace_with("")
    except AttributeError:
        pass

    try:
        category = soup.h1.text.strip()
    except AttributeError:
        category = "None"

    print(category)
    words.extend([a.a["href"] for a in soup.find_all(class_="search-result")])

    try:
        page = soup.find(class_="search-pager-next").a["href"]
    except (AttributeError, TypeError):
        # End of this category.
        random.shuffle(words)
        for word in words:
            load_video(word, category)
        words = []
        try:
            page = next(categories)
        except StopIteration:
            break

package = genanki.Package(sign_deck)
package.media_files = media_files
package.write_to_file('spreadthesign.apkg')

sign_deck = genanki.Deck(
  1594228110,
  'SpreadTheSign Sentences')
media_files = []

words = set()
for letter in "abcdefghijklmnopqrstuvwxyz":
    search_results = (
        "https://www.spreadthesign.com/en.us/search/?q={:}&cls=1".format(
            letter))
    url = urlparse(search_results)
    assert url.hostname == "www.spreadthesign.com"

    soup = BeautifulSoup(urlopen(search_results))
    soup.nav.replace_with("")
    soup.find(id="footer").replace_with("")
    try:
        soup.find(class_="breadcrumb").replace_with("")
    except AttributeError:
        pass

    words = words.union(
        [a.a["href"][:-4] for a in soup.find_all(class_="search-result")])

for word in words:
    print(load_video(word, "Sentences"))

package = genanki.Package(sign_deck)
package.media_files = media_files
package.write_to_file('spreadthesign_sentences.apkg')

