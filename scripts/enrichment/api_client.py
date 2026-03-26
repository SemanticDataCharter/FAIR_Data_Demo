"""
Async HTTP client for SDCStudio API.

Handles authentication, rate limiting, pagination, and retry logic.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Component type → API endpoint slug
# API returns lowercase type names (e.g., "xdstring"), so we map both forms.
TYPE_ENDPOINT_MAP: dict[str, str] = {
    "XdString": "xd-strings",
    "XdToken": "xd-tokens",
    "XdCount": "xd-counts",
    "XdQuantity": "xd-quantities",
    "XdBoolean": "xd-booleans",
    "XdOrdinal": "xd-ordinals",
    "XdTemporal": "xd-temporals",
    "XdFloat": "xd-floats",
    "XdDouble": "xd-doubles",
    "Units": "units",
    "Cluster": "clusters",
    # Lowercase variants (as returned by the components list API)
    "xdstring": "xd-strings",
    "xdtoken": "xd-tokens",
    "xdcount": "xd-counts",
    "xdquantity": "xd-quantities",
    "xdboolean": "xd-booleans",
    "xdordinal": "xd-ordinals",
    "xdtemporal": "xd-temporals",
    "xdfloat": "xd-floats",
    "xddouble": "xd-doubles",
    "units": "units",
    "cluster": "clusters",
}

# Normalize type name to canonical form (PascalCase)
TYPE_NORMALIZE: dict[str, str] = {
    "xdstring": "XdString",
    "xdtoken": "XdToken",
    "xdcount": "XdCount",
    "xdquantity": "XdQuantity",
    "xdboolean": "XdBoolean",
    "xdordinal": "XdOrdinal",
    "xdtemporal": "XdTemporal",
    "xdfloat": "XdFloat",
    "xddouble": "XdDouble",
    "units": "Units",
    "cluster": "Cluster",
}


class SDCStudioClient:
    """Async client for SDCStudio REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        rate_limit_delay: float = 0.2,
        max_retries: int = 3,
    ):
        load_dotenv()
        self.base_url = (base_url or os.environ["SDCSTUDIO_URL"]).rstrip("/")
        self.api_key = api_key or os.environ["SDC_API_KEY"]
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(1)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SDCStudioClient":
        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api/v1/dmgen",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a rate-limited request with retry on 429/5xx."""
        assert self._client is not None, "Use as async context manager"
        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    resp = await self._client.request(method, path, **kwargs)
                    if resp.status_code == 429 or resp.status_code >= 500:
                        wait = (2 ** attempt) * 1.0
                        logger.warning(
                            "HTTP %d on %s %s — retry %d in %.1fs",
                            resp.status_code, method, path, attempt + 1, wait,
                        )
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    return resp
                except httpx.HTTPStatusError:
                    raise
                except httpx.HTTPError as e:
                    if attempt == self.max_retries - 1:
                        raise
                    wait = (2 ** attempt) * 1.0
                    logger.warning("HTTP error %s — retry %d in %.1fs", e, attempt + 1, wait)
                    await asyncio.sleep(wait)
            # Should not reach here, but just in case
            raise RuntimeError(f"Max retries exceeded for {method} {path}")
            # Rate limiting delay between calls
        await asyncio.sleep(self.rate_limit_delay)

    async def _paginate(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Fetch all pages from a paginated endpoint."""
        results: list[dict] = []
        params = dict(params or {})
        params.setdefault("page_size", 200)
        while True:
            resp = await self._request("GET", path, params=params)
            data = resp.json()
            if isinstance(data, list):
                results.extend(data)
                break
            results.extend(data.get("results", []))
            next_url = data.get("next")
            if not next_url:
                break
            # Extract page number from next URL
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(next_url)
            qs = parse_qs(parsed.query)
            if "page" in qs:
                params["page"] = qs["page"][0]
            else:
                break
        return results

    # ── List endpoints ──────────────────────────────────────────────

    async def list_components(
        self,
        project_ct_id: str,
        published: bool | None = None,
    ) -> list[dict]:
        """List all components for a project, optionally filtered by published status."""
        params: dict[str, Any] = {"project": project_ct_id}
        if published is not None:
            params["published"] = str(published).lower()
        return await self._paginate("/components/", params)

    async def list_namespaces(self) -> list[dict]:
        return await self._paginate("/namespaces/")

    async def list_predicates(self) -> list[dict]:
        return await self._paginate("/predicates/")

    async def list_predobjs(self, project_ct_id: str) -> list[dict]:
        """List all pred-objs, filtered to a specific project ct_id."""
        all_pos = await self._paginate("/pred-objs/")
        return [po for po in all_pos if po.get("project") == project_ct_id]

    # ── Mutation endpoints ──────────────────────────────────────────

    async def patch_component(
        self,
        component_type: str,
        ct_id: str,
        payload: dict[str, Any],
    ) -> dict:
        """PATCH a component with enrichment data."""
        endpoint = TYPE_ENDPOINT_MAP.get(component_type)
        if not endpoint:
            raise ValueError(f"Unknown component type: {component_type}")
        resp = await self._request("PATCH", f"/{endpoint}/{ct_id}/", json=payload)
        return resp.json()

    async def create_namespace(self, abbrev: str, uri: str) -> dict:
        resp = await self._request("POST", "/namespaces/", json={"abbrev": abbrev, "uri": uri})
        return resp.json()

    async def create_predicate(self, ns_id: int, class_name: str) -> dict:
        """Create a predicate. Expects namespace ID (pk) and class_name."""
        resp = await self._request(
            "POST", "/predicates/",
            json={"ns_abbrev": ns_id, "class_name": class_name},
        )
        return resp.json()

    async def create_predobj(
        self,
        predicate_id: int,
        object_uri: str,
        po_name: str,
        project_ct_id: str,
    ) -> dict:
        resp = await self._request(
            "POST", "/pred-objs/",
            json={
                "predicate": predicate_id,
                "object_uri": object_uri,
                "po_name": po_name,
                "project": project_ct_id,
            },
        )
        return resp.json()

    async def get_component(self, component_type: str, ct_id: str) -> dict:
        """GET a single component by type and ct_id."""
        endpoint = TYPE_ENDPOINT_MAP.get(component_type)
        if not endpoint:
            raise ValueError(f"Unknown component type: {component_type}")
        resp = await self._request("GET", f"/{endpoint}/{ct_id}/")
        return resp.json()
