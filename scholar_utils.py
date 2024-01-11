from semanticscholar import SemanticScholar  # type: ignore

from _types import Paper

client = SemanticScholar()


def get_recommended_arxiv_ids_from_semantic_scholar(
    papers: list[Paper], max_results: int = 10, min_year: int = 2018
) -> list[Paper]:
    results: list[dict] = []
    for paper in papers:
        if not paper.url:
            continue

        if not paper.arxiv_id:
            continue

        try:
            results.extend(
                client.get_recommended_papers(
                    f"arXiv:{paper.arxiv_id}", limit=max_results * 2
                )
            )
            paper.explored = True
        except Exception as e:
            print(f"[!] {e}]")
            pass

    filtered: list[dict] = []
    for result in results:
        if "ArXiv" not in result["externalIds"]:
            continue

        arxiv_id = result["externalIds"]["ArXiv"]
        if arxiv_id in [f["externalIds"]["ArXiv"] for f in filtered]:
            continue

        if result["title"] in [p.title for p in papers]:
            continue

        if result["year"] < min_year:
            continue

        filtered.append(result)

    # TODO: Sort by something important

    recommended_papers: list[Paper] = []
    for result in filtered:
        recommended_papers.append(
            Paper(
                title=result["title"],
                url=f'https://arxiv.org/abs/{result["externalIds"]["ArXiv"]}',
                abstract=result["abstract"],
            )
        )

    return recommended_papers[:max_results]
