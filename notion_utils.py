import asyncio
import typing as t
from datetime import datetime

from notion_client import AsyncClient
from notion_client.helpers import async_collect_paginated_api
from tqdm import tqdm  # type: ignore

from _types import AttackType, Paper, Focus

NotionClient = AsyncClient


def get_notion_client(token: str) -> NotionClient:
    return NotionClient(auth=token)


async def get_papers_from_notion(client: NotionClient, database_id: str, *, max: int | None = None) -> list[Paper]:
    if max:
        results = await client.databases.query(database_id=database_id, page_size=max)
        results = results['results']
    else:
        results = await async_collect_paginated_api(
            client.databases.query, database_id=database_id
        )

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
        attack_type = properties["Attack Type"]["select"]
        attack_type = AttackType(attack_type["name"]) if attack_type else None
        explored = properties["Explored"]["checkbox"]

        if not any([url, title]):
            continue

        papers.append(
            Paper(
                page_id=page_id,
                title=title,
                url=url,
                focus=focus,
                attack_type=attack_type,
                summary=summary,
                authors=authors,
                published=published,
                explored=explored,
                track_changes=True,
            )
        )

    return papers


async def write_papers_to_notion(
    client: NotionClient, database_id: str, papers: list[Paper]
) -> None:
    for paper in tqdm(papers):
        properties: dict[str, t.Any] = {}
        if paper.title and paper._original_state["title"] != paper.title:
            properties["Title"] = {"title": [{"text": {"content": paper.title}}]}
        if paper.url and paper._original_state["url"] != paper.url:
            properties["URL"] = {"url": paper.url}
        if paper.summary and paper._original_state["summary"] != paper.summary:
            properties["Summary"] = {
                "rich_text": [{"text": {"content": paper.summary}}]
            }
        if paper.authors and paper._original_state["authors"] != paper.authors:
            properties["Authors"] = {
                "multi_select": [{"name": author} for author in paper.authors[:5]] # Limit to 5 authors
            }
        if paper.published and paper._original_state["published"] != paper.published:
            properties["Published"] = {"date": {"start": paper.published.isoformat()}}
        if paper.focus and paper._original_state["focus"] != paper.focus:
            properties["Focus"] = {"select": {"name": paper.focus.value}}
        if paper.attack_type and paper._original_state["attack_type"] != paper.attack_type:
            properties["Attack Type"] = {"select": {"name": paper.attack_type.value}}
        if paper.explored and paper._original_state["explored"] != paper.explored:
            properties["Explored"] = {"checkbox": paper.explored}

        if paper.page_id:
            await client.pages.update(paper.page_id, properties=properties)
        else:
            await client.pages.create(
                parent={"database_id": database_id}, properties=properties
            )

    return None
