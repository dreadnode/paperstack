import typing as t
from datetime import datetime

from notion_client import Client
from notion_client.helpers import collect_paginated_api

from _types import Paper, Focus

NotionClient = Client


def get_notion_client(token: str) -> NotionClient:
    return NotionClient(auth=token)


def get_papers_from_notion(client: NotionClient, database_id: str) -> list[Paper]:
    results = collect_paginated_api(client.databases.query, database_id=database_id)

    papers: list[Paper] = []
    for result in results:
        page_id = result["id"]
        properties = result["properties"]

        title = properties["Title"]["title"]
        title = title[0]["text"]["content"] if title else None
        url = properties["URL"]["url"]
        summary = properties["Summary"]["rich_text"]
        summary = summary[0]["text"]["content"] if summary else None
        authors = [author["name"] for author in properties["Authors"]["multi_select"]]
        published = properties["Published"]["date"]
        published = datetime.fromisoformat(published["start"]) if published else None
        focus = properties["Focus"]["select"]
        focus = Focus(focus["name"]) if focus else None
        explored = properties["Explored"]["checkbox"]

        if not any([url, title]):
            continue

        papers.append(
            Paper(
                page_id=page_id,
                title=title,
                url=url,
                focus=focus,
                summary=summary,
                authors=authors,
                published=published,
                explored=explored,
                track_changes=True,
            )
        )

    return papers


def write_papers_to_notion(
    client: NotionClient, database_id: str, papers: list[Paper]
) -> None:
    for paper in papers:
        properties: dict[str, t.Any] = {}
        if paper.title:
            properties["Title"] = {"title": [{"text": {"content": paper.title}}]}
        if paper.url:
            properties["URL"] = {"url": paper.url}
        if paper.summary:
            properties["Summary"] = {
                "rich_text": [{"text": {"content": paper.summary}}]
            }
        if paper.authors:
            properties["Authors"] = {
                "multi_select": [{"name": author} for author in paper.authors]
            }
        if paper.published:
            properties["Published"] = {"date": {"start": paper.published.isoformat()}}
        if paper.focus:
            properties["Focus"] = {"select": {"name": paper.focus.value}}
        if paper.explored:
            properties["Explored"] = {"checkbox": paper.explored}

        if paper.page_id:
            client.pages.update(paper.page_id, properties=properties)
        else:
            client.pages.create(
                parent={"database_id": database_id}, properties=properties
            )
