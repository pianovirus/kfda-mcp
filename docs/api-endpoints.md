# MFDS Public OpenAPI — Endpoint Reference

식약처 공공 OpenAPI 정확한 엔드포인트 정리. kfda-mcp가 사용하는 API와 신청 방법.

---

## 🔑 신청 방법 (공공데이터포털)

1. https://www.data.go.kr 회원가입 (본인 명의)
2. 아래 각 API 검색 → **활용신청** → 즉시 승인
3. 마이페이지 → **데이터 활용 → 활용신청 현황** → 인증키 확인
4. `.env` 에 `MFDS_API_KEY=<발급키>` 저장

⚠️ **회사 계정 키와 분리**: 오픈소스 프로젝트용 키는 본인 명의로 별도 발급.

---

## 📋 사용 중인 API 목록

### 1. 식품의약품안전처_의약품 제품 허가정보

**Base service**: `DrugPrdtPrmsnInfoService07`
**Base URL**: `https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService07`

**세부 endpoint (3종)**:

| # | 기능 | Endpoint | 일일 트래픽 |
|---|---|---|---|
| 1 | 의약품 제품 허가 목록 (검색·조회) | `/getDrugPrdtPrmsnInq07` | 10,000 |
| 2 | 의약품 제품 허가 상세정보 | `/getDrugPrdtPrmsnDtlInq06` | 10,000 |
| 3 | 의약품 제품 주성분 상세정보 | `/getDrugPrdtMcpnDtlInq07` | 10,000 |

**kfda-mcp tool**: `search_drug` → 현재 `getDrugPrdtPrmsnDtlInq06` 사용

**주요 응답 필드**:
- `ITEM_NAME` — 제품명 (한글)
- `MAIN_ITEM_INGR` — 주성분
- `ENTP_NAME` — 제조사
- `ATC_CODE` — ATC 분류 코드
- `EE_DOC_DATA` — 효능·효과
- `CHART` — 제형

---

### 2. 식품의약품안전처_의약품안전사용서비스(DUR) 품목정보

**Base service**: `DURPrdlstInfoService03`
**Base URL**: `https://apis.data.go.kr/1471000/DURPrdlstInfoService03`

**세부 endpoint (7종 — DUR 룰 종류별)**:

| # | DUR 룰 종류 | Endpoint | 일일 트래픽 |
|---|---|---|---|
| 1 | 병용금기 (concurrent) | `/getUsjntTabooInfoList03` | 10,000 |
| 2 | 임부금기 (pregnancy) | `/getPwnmTabooInfoList03` | 10,000 |
| 3 | 노인주의 (elderly) | `/getOdsnAtentInfoList03` | 10,000 |
| 4 | 효능군 중복 (duplicate efficacy) | `/getEfcyDplctInfoList03` | 10,000 |
| 5 | 용량주의 (dosage) | `/getCpctyAtentInfoList03` | 10,000 |
| 6 | 투여기간주의 (duration) | `/getMdctnPdAtentInfoList03` | 10,000 |
| 7 | 특정연령대금기 (age-specific) | `/getSpcifyAgrdeTabooInfoList03` | 10,000 |

**kfda-mcp tool**: `check_dur_interaction` → 현재 `getUsjntTabooInfoList03` (병용금기) 사용

**주요 응답 필드**:
- `TYPE_NAME` — DUR 룰 타입명
- `PROHBT_CONTENT` — 금기 내용 (한글 설명)
- `REMARK` — 비고

---

### 3. 식품의약품안전처_의약품개요정보 (e약은요)

**Base URL**: `https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList`

**일일 트래픽**: 10,000

**kfda-mcp tool**: `get_drug_easy_info`

**주요 응답 필드 (환자용 쉬운 설명)**:
- `itemName` — 약품명
- `efcyQesitm` — 효능·효과 (한글, 환자 친화)
- `useMethodQesitm` — 용법·용량
- `seQesitm` — 부작용
- `atpnQesitm` — 주의사항
- `depositMethodQesitm` — 보관법

---

### 4. (보류) 건강기능식품 OpenAPI

**상태**: WIP (Work In Progress)

**이유**: 공공데이터포털에서 활용신청 가능한 건기식 API 대부분 **LINK 타입**이라 외부 사이트(식품안전나라)로 이동해서 별도 키 발급 필요.

**대안 검토 중**:
- 식품안전나라 OpenAPI 직접 신청: https://www.foodsafetykorea.go.kr
- 또는 공공데이터포털에서 "건강기능식품 품목제조신고" 등 검색

**kfda-mcp tool**: `search_supplement` → 현재 코드는 있지만 미작동

---

## 🔐 API 키 사용 규칙

```python
# 모든 endpoint는 같은 인증키 사용
params = {
    "serviceKey": MFDS_API_KEY,   # Decoding 키 사용 (URL-encode는 httpx가 자동)
    "type": "json",
    "numOfRows": 10,
    "pageNo": 1,
    # ... API별 추가 파라미터
}
```

**Encoding vs Decoding 키**:
- **Decoding 키 사용 권장** (httpx, requests 등 라이브러리가 자동 URL-encode)
- Encoding 키는 raw HTTP URL에 직접 박을 때만

---

## 📊 응답 구조 공통 패턴

```json
{
  "header": {
    "resultCode": "00",
    "resultMsg": "NORMAL SERVICE."
  },
  "body": {
    "items": [
      { /* 실제 데이터 객체들 */ }
    ],
    "numOfRows": 10,
    "pageNo": 1,
    "totalCount": 123
  }
}
```

⚠️ `items` 가 단일 객체로 반환되는 경우 있음 (배열 X) — 코드에서 type check 필요.

---

## 🧪 호출 테스트 (Python)

```python
import asyncio
import sys
sys.path.insert(0, 'src')
from kfda_mcp.server import search_drug, check_dur_interaction, get_drug_easy_info

# 1. 의약품 마스터
result = asyncio.run(search_drug("타이레놀", limit=2))
print(result)

# 2. DUR 병용금기
result = asyncio.run(check_dur_interaction("아스피린", "와파린"))
print(result)

# 3. e약은요
result = asyncio.run(get_drug_easy_info("타이레놀"))
print(result)
```

---

## 📚 공공데이터포털 API 페이지 직링크

- 의약품 제품 허가정보: https://www.data.go.kr (검색: "식품의약품안전처 의약품 제품 허가정보")
- DUR 품목정보: 검색 "식품의약품안전처 DUR"
- e약은요: 검색 "식품의약품안전처 e약은요" 또는 "의약품개요정보"
- 건기식: https://www.foodsafetykorea.go.kr (별도)

---

## 🛠 Endpoint 확장 시 참고

서비스 버전이 올라가면 endpoint 번호도 올라감 (예: `Service06` → `Service07`).
404 발생 시 공공데이터포털 → 해당 API → "참고문서" → 최신 명세서 확인.

마지막 업데이트: 2026-06-30
