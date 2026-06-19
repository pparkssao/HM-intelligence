# HM Intelligence 📊

**키워드 기반 제약/바이오 뉴스 × 파이프라인 연결 → 경쟁사 R&D 동향 자동 분석 플랫폼**

> 뉴스는 많지만 내 업무와 관련된 것만 보기 힘들고, 파이프라인까지 연결이 안 되는 문제를 해결합니다.  
> **"정보 → 연결 → 해석 → 전달" 자동화**

---

## 🚀 시스템 흐름

```
사용자 입력 (키워드 + 기간 + 이메일)
    ↓
① 뉴스 수집 (10개 제약/바이오 RSS 피드)
    ↓
② AI 엔티티 추출 (GPT-4o-mini)
   - 회사명 / 약물명 / 질환 / 임상단계 / 딜 유형
    ↓
③ 파이프라인 DB 매칭
   - 뉴스 속 회사·약물 ↔ 내부 파이프라인 DB 자동 연결
    ↓
④ 경쟁 인텔리전스 인사이트 생성 (GPT-4o-mini)
   - Executive Summary / 핵심 인사이트 / 기회·리스크 / 권고 액션
    ↓
⑤ HTML 이메일 리포트 자동 발송
```

---

## 📁 프로젝트 구조

```
HM-intelligence/
├── streamlit_app.py          # Streamlit 웹 프론트엔드 (메인 진입점)
├── config.py                 # 환경 설정
├── requirements.txt
├── .env.example              # 환경변수 예시
│
├── app/
│   ├── news_collector.py     # RSS 뉴스 수집
│   ├── entity_extractor.py   # AI 엔티티 추출 (OpenAI)
│   ├── pipeline_matcher.py   # 파이프라인 DB 매칭
│   ├── insight_generator.py  # AI 인사이트 생성 (OpenAI)
│   ├── email_sender.py       # HTML 이메일 발송 (SMTP)
│   └── main.py               # 전체 파이프라인 오케스트레이션
│
├── data/
│   └── pipeline_db.csv       # 파이프라인 데이터베이스 (56개 항목)
│
└── templates/
    └── email_report.html     # HTML 이메일 템플릿 (Jinja2)
```

---

## ⚡ 빠른 시작

### 1. 환경 설정

```bash
# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 OPENAI_API_KEY, SMTP 설정 입력
```

### 2. 앱 실행

```bash
streamlit run streamlit_app.py
```

브라우저에서 `http://localhost:8501` 접속

### 3. 사용 방법

1. **키워드 입력**: `Alzheimer`, `GLP-1, obesity`, `EGFR NSCLC` 등
2. **기간 설정**: 최근 1~30일
3. **이메일 입력** (선택): 결과 리포트 수신 주소
4. **🚀 분석 시작** 클릭

---

## 🔧 환경변수 설명

| 변수 | 필수 | 설명 |
|------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API 키 |
| `SMTP_HOST` | 이메일 발송 시 | SMTP 서버 (기본: smtp.gmail.com) |
| `SMTP_PORT` | 이메일 발송 시 | SMTP 포트 (기본: 587) |
| `SMTP_USER` | 이메일 발송 시 | 발송 이메일 계정 |
| `SMTP_PASSWORD` | 이메일 발송 시 | 앱 비밀번호 (Gmail 앱 비밀번호 권장) |

> Gmail 사용 시: [Google 계정 > 보안 > 앱 비밀번호](https://myaccount.google.com/apppasswords)에서 앱 비밀번호 생성

---

## 🧬 파이프라인 DB

`data/pipeline_db.csv`에 56개 항목 포함:

- **글로벌 Big Pharma**: Biogen, Eli Lilly, Roche, Pfizer, Novartis, AstraZeneca, Roche, BMS, Merck, Sanofi, Gilead, AbbVie, Amgen, Vertex, Regeneron, Moderna, BioNTech, Alnylam, Intellia
- **국내 제약사**: 한미, 유한, 대웅, 일동, 보령, OliX, 삼성바이오에피스
- **치료 분야**: 알츠하이머, 종양, 당뇨/비만, 면역, 심혈관, 희귀질환 등

파이프라인 항목 추가/수정: `data/pipeline_db.csv`를 직접 편집하세요.

---

## 📧 이메일 리포트 구성

| 섹션 | 내용 |
|------|------|
| Executive Summary | 2-3문장 핵심 요약 |
| 핵심 인사이트 | 긴급도(HIGH/MED/LOW) 포함 인사이트 카드 |
| 관련 뉴스 | 출처·날짜·엔티티 태그 포함 |
| 파이프라인 현황 | 매칭된 경쟁사 약물 테이블 |
| 경쟁 환경 분석 | AI 생성 치료 분야 경쟁 지형 |
| 기회/리스크/권고 | 한미 관점 전략적 시사점 |

---

## 🛠️ 파이프라인 DB 확장

```csv
# data/pipeline_db.csv 에 행 추가
company,drug_name,indication,phase,mechanism,modality,status,region,last_updated
MyCompany,Drug-001,Parkinson's Disease,Phase 2,Alpha-synuclein inhibitor,Small Molecule,Phase 2,Global,2025-01-01
```

---

## 📌 기술 스택

| 구성요소 | 기술 |
|----------|------|
| 프론트엔드 | Streamlit |
| AI/NLP | OpenAI GPT-4o-mini |
| 뉴스 수집 | feedparser + requests |
| 이메일 | smtplib + Jinja2 HTML 템플릿 |
| 데이터 처리 | pandas |
| 파이프라인 DB | CSV (확장 가능: PostgreSQL, SQLite) |