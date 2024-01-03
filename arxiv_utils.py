import re

import arxiv  # type: ignore

from _types import Paper

client = arxiv.Client()


def convert_arxiv_url_to_id(url: str) -> str | None:
    match = re.search(r"\d{4}\.\d{5}", url)
    return match.group(0) if match else None


def arxiv_result_to_paper(result: arxiv.Result) -> Paper:
    return Paper(
        title=result.title,
        url=result.entry_id,
        arxiv_id=convert_arxiv_url_to_id(result.entry_id),
        abstract=result.summary,
        authors=[a.name for a in result.authors],
        published=result.published,
    )


def search_arxiv(query: str, max_results=10) -> list[arxiv.Result]:
    return list(
        client.results(
            arxiv.Search(
                query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )
        )
    )


def search_arxiv_as_paper(query: str, max_results=10) -> list[Paper]:
    return [
        arxiv_result_to_paper(result) for result in search_arxiv(query, max_results)
    ]


def search_arxiv_by_id(id: str) -> arxiv.Result | None:
    for result in client.results(arxiv.Search(id_list=[id])):
        return result
    return None


def fill_papers_with_arxiv(papers: list[Paper]) -> list[Paper]:
    for paper in papers:
        if paper.has_arxiv_props():
            continue

        result: arxiv.Result | None = None

        if paper.url:
            paper.arxiv_id = convert_arxiv_url_to_id(paper.url)

        if paper.arxiv_id:
            result = search_arxiv_by_id(paper.arxiv_id)

        if paper.title and not result:
            searched = search_arxiv(f'"{paper.title}"', max_results=1)
            result = searched[0] if searched else None

        if not result:
            print(f'[!] Could not find arxiv result for "{paper.title}" [{paper.url}]')
            continue

        paper.title = result.title
        paper.url = result.entry_id
        paper.arxiv_id = convert_arxiv_url_to_id(result.entry_id)
        paper.abstract = result.summary
        paper.authors = [a.name for a in result.authors]
        paper.published = result.published

    return papers
