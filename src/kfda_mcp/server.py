"""KFDA MCP Server entrypoint.

Exposes Korean Ministry of Food and Drug Safety (식약처/MFDS) public OpenAPIs
as MCP tools so LLM agents can autonomously query Korean drug safety data.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

load_dotenv()

MFDS_API_KEY = os.getenv("MFDS_API_KEY", "")

# Public MFDS OpenAPI endpoints (식약처 공공 OpenAPI)
DRUG_MASTER_URL = "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService06/getDrugPrdtPrmsnDtlInq05"
DUR_URL = "https://apis.data.go.kr/1471000/DURPrdlstInfoService03/getUsjntTabooInfoList03"
SUPPLEMENT_URL = "https://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsItem01"
EASY_DRUG_URL = "https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"

server = Server("kfda-mcp")


# ============================================================================
# Tool definitions
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List MCP tools exposed by this server."""
    return [
        Tool(
            name="search_drug",
            description=(
                "식약처 의약품 마스터에서 약품을 검색합니다 (Korean drug master search). "
                "제품명, 성분명, 제조사 등으로 조회 가능. "
                "Returns product_name, generic_name, manufacturer, ATC code, indication."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "검색할 약품명 (한글 또는 영문, 부분 매치 지원)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "반환할 최대 결과 수",
                        "default": 10,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="check_dur_interaction",
            description=(
                "식약처 의약품 안전사용서비스(DUR)에서 두 약물의 병용금기·연령금기 등 안전성 정보를 확인합니다. "
                "Check Korean Drug Utilization Review (DUR) safety rules between two drugs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "drug_a": {
                        "type": "string",
                        "description": "약물 A 이름 또는 성분명",
                    },
                    "drug_b": {
                        "type": "string",
                        "description": "약물 B 이름 또는 성분명",
                    },
                },
                "required": ["drug_a", "drug_b"],
            },
        ),
        Tool(
            name="search_supplement",
            description=(
                "식약처 식품안전나라 건강기능식품 인허가 정보를 검색합니다. "
                "Search Korean functional health food (건기식) registrations by ingredient or product name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ingredient": {
                        "type": "string",
                        "description": "주성분명 (예: 코엔자임Q10, 비타민D)",
                    },
                    "product": {
                        "type": "string",
                        "description": "제품명",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "반환할 최대 결과 수",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="get_drug_easy_info",
            description=(
                "식약처 e약은요 (환자용 쉬운 약물 정보)를 조회합니다. "
                "Get patient-friendly Korean drug information: purpose, dosage, side effects, warnings."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "약품명",
                    },
                },
                "required": ["drug_name"],
            },
        ),
    ]


# ============================================================================
# Tool implementations
# ============================================================================

async def _http_get(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """Common GET request with API key injection and JSON parsing."""
    if not MFDS_API_KEY:
        return {
            "error": "MFDS_API_KEY not configured",
            "hint": "Get a free API key at https://www.data.go.kr and set MFDS_API_KEY env var.",
        }
    params = {**params, "serviceKey": MFDS_API_KEY, "type": "json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e), "url": url}


async def search_drug(name: str, limit: int = 10) -> dict[str, Any]:
    """Search Korean drug master by name."""
    data = await _http_get(
        DRUG_MASTER_URL,
        {"item_name": name, "numOfRows": limit, "pageNo": 1},
    )
    if "error" in data:
        return data
    items = data.get("body", {}).get("items", []) if isinstance(data.get("body"), dict) else []
    return {
        "query": name,
        "count": len(items),
        "results": [
            {
                "product_name": item.get("ITEM_NAME"),
                "generic_name": item.get("MAIN_ITEM_INGR"),
                "manufacturer": item.get("ENTP_NAME"),
                "atc_code": item.get("ATC_CODE"),
                "kor_indication": item.get("EE_DOC_DATA"),
                "dosage_form": item.get("CHART"),
            }
            for item in items
        ],
    }


async def check_dur_interaction(drug_a: str, drug_b: str) -> dict[str, Any]:
    """Check DUR safety rules between two drugs."""
    data = await _http_get(
        DUR_URL,
        {"itemName": drug_a, "mixtureItemName": drug_b, "numOfRows": 50, "pageNo": 1},
    )
    if "error" in data:
        return data
    items = data.get("body", {}).get("items", []) if isinstance(data.get("body"), dict) else []
    return {
        "drug_a": drug_a,
        "drug_b": drug_b,
        "warnings_count": len(items),
        "warnings": [
            {
                "rule_type": item.get("TYPE_NAME"),
                "severity": item.get("PROHBT_CONTENT", "")[:30],
                "description_kor": item.get("PROHBT_CONTENT"),
                "remarks": item.get("REMARK"),
            }
            for item in items
        ],
    }


async def search_supplement(
    ingredient: str | None = None,
    product: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search Korean functional health food registrations."""
    params: dict[str, Any] = {"numOfRows": limit, "pageNo": 1}
    if ingredient:
        params["prdlstNm"] = ingredient
    if product:
        params["bssh_NM"] = product
    data = await _http_get(SUPPLEMENT_URL, params)
    if "error" in data:
        return data
    items = data.get("body", {}).get("items", []) if isinstance(data.get("body"), dict) else []
    return {
        "query": {"ingredient": ingredient, "product": product},
        "count": len(items),
        "results": [
            {
                "product_name": item.get("PRDLST_NM"),
                "manufacturer": item.get("BSSH_NM"),
                "main_ingredient": item.get("PRIMARY_FNCLTY"),
                "approved_function": item.get("FNCLTY_CN"),
                "intake_method": item.get("NTK_MTHD"),
            }
            for item in items
        ],
    }


async def get_drug_easy_info(drug_name: str) -> dict[str, Any]:
    """Get patient-friendly Korean drug information (e약은요)."""
    data = await _http_get(
        EASY_DRUG_URL,
        {"itemName": drug_name, "numOfRows": 5, "pageNo": 1},
    )
    if "error" in data:
        return data
    items = data.get("body", {}).get("items", []) if isinstance(data.get("body"), dict) else []
    if not items:
        return {"query": drug_name, "found": False}
    item = items[0]
    return {
        "query": drug_name,
        "product_name": item.get("itemName"),
        "purpose": item.get("efcyQesitm"),
        "dosage": item.get("useMethodQesitm"),
        "side_effects": item.get("seQesitm"),
        "warnings": item.get("atpnQesitm"),
        "storage": item.get("depositMethodQesitm"),
    }


# ============================================================================
# Tool dispatcher
# ============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch MCP tool calls to implementations."""
    import json

    handlers = {
        "search_drug": search_drug,
        "check_dur_interaction": check_dur_interaction,
        "search_supplement": search_supplement,
        "get_drug_easy_info": get_drug_easy_info,
    }

    handler = handlers.get(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    result = await handler(**arguments)
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


# ============================================================================
# Server entrypoint
# ============================================================================

async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """CLI entrypoint registered in pyproject.toml."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
