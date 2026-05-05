import json
import urllib.parse
import urllib.request
from pathlib import Path


AUTHOR_ID = "2680286"
OUTPUT_FILE = Path("publications.json")


def fetch_inspire_records():
    """
    Fetch publications from INSPIRE-HEP using the author's INSPIRE record ID.
    """

    query = f'authors.record.$ref:"https://inspirehep.net/api/authors/{AUTHOR_ID}"'

    params = {
        "q": query,
        "sort": "mostrecent",
        "size": "50",
    }

    url = "https://inspirehep.net/api/literature?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "danieleiannotti.github.io publication updater",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("hits", {}).get("hits", [])


def get_title(metadata):
    titles = metadata.get("titles", [])
    if titles:
        return titles[0].get("title", "Untitled")
    return "Untitled"


def get_year(metadata):
    publication_info = metadata.get("publication_info", [])

    for item in publication_info:
        if item.get("year"):
            return str(item["year"])

    preprint_date = metadata.get("preprint_date")
    if preprint_date:
        return preprint_date[:4]

    earliest_date = metadata.get("earliest_date")
    if earliest_date:
        return earliest_date[:4]

    return "Year unknown"


def get_journal(metadata):
    publication_info = metadata.get("publication_info", [])

    for item in publication_info:
        journal = item.get("journal_title")
        volume = item.get("journal_volume")
        page = item.get("page_start")
        year = item.get("year")

        parts = []

        if journal:
            parts.append(journal)

        if volume:
            parts.append(str(volume))

        if page:
            parts.append(str(page))

        if parts:
            return ", ".join(parts)

    document_type = metadata.get("document_type", [])

    if "article" in document_type:
        return "Article"

    return "Preprint"


def get_authors(metadata, max_authors=8):
    authors = metadata.get("authors", [])

    names = []
    for author in authors[:max_authors]:
        name = author.get("full_name")
        if name:
            names.append(name)

    if not names:
        return "Authors unavailable"

    if len(authors) > max_authors:
        return ", ".join(names) + ", et al."

    return ", ".join(names)


def get_arxiv(metadata):
    eprints = metadata.get("arxiv_eprints", [])

    if not eprints:
        return ""

    value = eprints[0].get("value")

    if not value:
        return ""

    return f"https://arxiv.org/abs/{value}"


def get_doi(metadata):
    dois = metadata.get("dois", [])

    if not dois:
        return ""

    value = dois[0].get("value")

    if not value:
        return ""

    return f"https://doi.org/{value}"


def convert_record(record):
    metadata = record.get("metadata", {})

    control_number = metadata.get("control_number") or record.get("id")
    inspire_url = ""

    if control_number:
        inspire_url = f"https://inspirehep.net/literature/{control_number}"

    return {
        "title": get_title(metadata),
        "authors": get_authors(metadata),
        "year": get_year(metadata),
        "journal": get_journal(metadata),
        "inspire": inspire_url,
        "arxiv": get_arxiv(metadata),
        "doi": get_doi(metadata),
    }


def main():
    records = fetch_inspire_records()
    publications = [convert_record(record) for record in records]

    publications.sort(
        key=lambda item: item.get("year", "0"),
        reverse=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(publications, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Updated {OUTPUT_FILE} with {len(publications)} publications.")


if __name__ == "__main__":
    main()
