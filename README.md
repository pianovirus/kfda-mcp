# 🇰🇷 KFDA MCP Server

MCP (Model Context Protocol) server for Korean Ministry of Food and Drug Safety (식약처) public OpenAPI.

LLM agents (Claude, ChatGPT, etc.) can autonomously query Korean drug master, DUR (Drug Utilization Review) safety rules, and health supplement databases through the standard MCP protocol.

[![MCP](https://img.shields.io/badge/MCP-Anthropic-8b5cf6?style=for-the-badge)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Healthcare](https://img.shields.io/badge/Domain-Healthcare%20AI-ec4899?style=for-the-badge)](https://www.mfds.go.kr)

---

## 🎯 Why this exists

The Korean healthcare AI ecosystem lacks an open MCP server for MFDS (식약처) public APIs. Global MCP servers like BioMCP focus on US data (FDA, PubMed). For Korean healthcare AI applications — pharmacy systems, telemedicine, drug interaction checkers — direct access to KFDA/MFDS APIs is essential but each team has to write their own wrapper.

This project provides a standard MCP server so any LLM agent can query Korean drug safety data without bespoke integration code.

---

## ✨ Features

| Tool | Description | KFDA OpenAPI |
|---|---|---|
| `search_drug` | 의약품 마스터 검색 (제품명·성분·제조사·ATC 코드) | 의약품 제품 허가정보 |
| `check_dur_interaction` | 두 약물의 병용금기·연령금기·임부금기 확인 | 의약품 안전사용서비스 (DUR) |
| `search_supplement` | 건강기능식품 인허가 정보 검색 | 식품안전나라 건기식 OpenAPI |
| `get_drug_easy_info` | e약은요 (환자용 쉬운 약물 정보) 조회 | e약은요 |
| `lookup_atc_code` | ATC 코드 → 약물군 분류 정보 | 내장 매핑 |

---

## 🚀 Quick Start

### 1. Install

```bash
pip install kfda-mcp
# or from source
git clone https://github.com/pianovirus/kfda-mcp
cd kfda-mcp
pip install -e .
```

### 2. Get your MFDS API key

Apply for a free API key at [data.go.kr](https://www.data.go.kr) (공공데이터포털) — select 식약처 OpenAPI services.

### 3. Configure

Create `.env`:

```
MFDS_API_KEY=your_api_key_here
```

### 4. Run as MCP server

```bash
kfda-mcp
```

### 5. Connect from Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json` (or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "kfda": {
      "command": "kfda-mcp",
      "env": {
        "MFDS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. Now Claude can call Korean drug safety tools autonomously.

---

## 💡 Example Usage

Ask Claude (or any MCP-compatible LLM):

> "환자가 와파린을 복용 중인데 자몽 추출 영양제를 같이 먹어도 되는지 확인해줘"

Claude will autonomously:
1. Call `search_drug("와파린")` → get warfarin info + ATC code
2. Call `check_dur_interaction("warfarin", "grapefruit_extract")` → DUR check
3. Synthesize a safety recommendation grounded in MFDS data

---

## 🏗 Architecture

```
LLM Agent (Claude / GPT / etc.)
    │
    │ MCP Protocol (stdio / SSE)
    │
    ▼
KFDA MCP Server (this project)
    │
    │ HTTP requests
    │
    ▼
MFDS Public APIs
  - 의약품 제품 허가정보 OpenAPI
  - 의약품 안전사용서비스 (DUR)
  - 식품안전나라 건기식 OpenAPI
  - e약은요
```

---

## 📋 Tool Reference

### `search_drug(name: str, limit: int = 10)`

Search Korean drug master by product name, generic name, or manufacturer.

**Returns**: List of drugs with `product_name`, `generic_name`, `manufacturer`, `atc_code`, `kor_indication`, `dosage_form`.

### `check_dur_interaction(drug_a: str, drug_b: str)`

Check DUR safety rules between two drugs (병용금기·연령금기·임부금기 등).

**Returns**: List of warnings with `rule_type`, `severity`, `description_kor`.

### `search_supplement(ingredient: str | None = None, product: str | None = None)`

Search 식약처 건강기능식품 (functional health food) registrations.

**Returns**: List of supplements with `product_name`, `manufacturer`, `main_ingredient`, `approved_function`.

### `get_drug_easy_info(drug_name: str)`

Get patient-friendly drug information from e약은요 (consumer-facing drug guide).

**Returns**: `purpose`, `dosage`, `side_effects`, `warnings` in Korean.

### `lookup_atc_code(atc_code: str)`

Look up ATC (Anatomical Therapeutic Chemical) classification by code.

**Returns**: `level1` ~ `level5` Korean & English names, drug examples.

---

## 🛣 Roadmap

- [x] Project scaffold + MCP SDK setup
- [x] `search_drug` — 의약품 마스터 ✅ live verified (타이레놀 → ATC N02BE01)
- [x] `check_dur_interaction` — DUR 병용금기 ✅ live verified (아스피린+와파린 → 50건)
- [x] `search_supplement` — 건기식 ✅ live verified (식품안전나라 C003, 비타민 검색 OK)
- [x] `get_drug_easy_info` — e약은요 ✅ live verified (타이레놀 효능·용법·부작용 반환)
- [ ] `lookup_atc_code` — ATC 매핑 (planned)
- [ ] Local cache layer (reduce API calls) — planned
- [ ] Async batch query support — planned
- [ ] Multilingual responses (한/영) — planned

**현재 상태: 4/4 핵심 tool 모두 live 검증 완료, production-ready**
- [ ] Local cache layer (reduce API calls)
- [ ] Async batch query support
- [ ] Multilingual responses (한/영)

---

## 🤝 Contributing

Korean healthcare AI engineers — contributions welcome! Please open an issue or PR.

This project aims to be the de facto MCP server for MFDS public APIs.

---

## 📜 License

MIT © 2026 Myunghee Kim · pianovirus@naver.com

---

## 🙏 Acknowledgments

- [Anthropic MCP](https://modelcontextprotocol.io) — Standard protocol for LLM-tool communication
- [식품의약품안전처 (MFDS)](https://www.mfds.go.kr) — Public health data API provider
- [공공데이터포털](https://www.data.go.kr) — Korean government open data platform

---

## 한국어 요약

식약처(MFDS)의 공공 OpenAPI를 MCP 프로토콜로 감싼 서버입니다. Claude, GPT 같은 LLM 에이전트가 한국 의약품 마스터·DUR 안전성·건강기능식품 정보를 자율적으로 조회할 수 있습니다.

한국 헬스 AI 개발자들이 매번 식약처 API wrapper를 직접 만들 필요 없이, 이 MCP 서버 하나로 표준화된 도구 접근을 제공하는 것이 목표입니다.

기여 환영합니다. 🌱
