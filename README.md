# 에스테틱 법률·안전 자문 AI 챗봇

공중위생관리법 · 화장품법 · 의료법 기반 RAG(Retrieval-Augmented Generation) 챗봇.
에스테틱 샵 원장님이 마케팅 문구, 시술 행위, 화장품 광고의 법적 기준을 쉽게 확인할 수 있도록 설계.

---

## 주요 기능

- 법령 조문 기반 질문 응답 (RAG)
- 식약처 회수·판매중지/사용제한 원료 기반 안전 정보 질문 응답 (법령 검색과 통합, LLM 호출 1회)
- BM25 + kNN 하이브리드 검색 (OpenSearch)
- BGE-M3 임베딩 + Gemma4:e4b 답변 생성 (Ollama)
- 질문-답변 시맨틱 캐시 (OpenSearch 유사도 검색 + Redis, 비슷한 질문 재요청 시 RAG 재실행 없이 즉시 응답)
- sector 필터링 (위생관리 / 화장품규제 / 의료행위)
- 채팅 UI (Spring MVC JSP)
- Swagger UI (FastAPI 5000)

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| **LLM** | Gemma4:e4b (Ollama) |
| **임베딩** | BGE-M3 (Ollama, 1024차원) |
| **벡터 검색** | OpenSearch 3.7.0 (lucene kNN) |
| **RAG 서버** | Python · FastAPI · uvicorn |
| **웹 서버** | Java 17 · Spring Legacy MVC 5.3 · Tomcat 9 |
| **ORM** | MyBatis 3.5 |
| **DB** | PostgreSQL (수집 로그·메타) |
| **캐시** | Redis (질문-답변 payload) + OpenSearch (질문 임베딩 유사도 검색) |
| **데이터** | 법제처 Open API (국가법령정보) |

---

## 프로젝트 구조

```
RAG_Mazelone/
├── scripts/
│   ├── common/
│   │   └── mazel_common.py   # 공통 유틸 (설정, DB, OpenSearch 클라이언트)
│   ├── collect/               # 데이터 수집 (ETL)
│   │   ├── explore_api.py    # API 응답 구조 탐색
│   │   ├── collect_law.py    # 법제처 법령 수집 → OpenSearch 인덱싱
│   │   ├── collect_hazard.py # 식약처 회수·사용제한원료 수집 → OpenSearch 인덱싱
│   │   └── init_db.sql       # PostgreSQL 메타 테이블 DDL
│   ├── rag/                   # 임베딩 · 검색 · RAG 서빙
│   │   ├── embed_index.py    # BGE-M3 임베딩 → knn_vector 적재
│   │   ├── search_hybrid.py  # BM25+kNN 하이브리드 검색 (법령+안전정보)
│   │   ├── rag_pipeline.py   # RAG 전체 파이프라인 (검색→프롬프트→LLM)
│   │   ├── qa_cache.py       # 질문-답변 시맨틱 캐시 (Redis+OpenSearch)
│   │   ├── warm_cache.py     # 캐시 워밍업 스크립트
│   │   └── rag_server.py     # FastAPI RAG 서버 (포트 5000)
│   └── systemd/               # 법령 갱신 자동화 (systemd timer)
│       ├── collect-law-run.sh # 수집→재임베딩→캐시삭제 실행 순서
│       ├── collect-law.service # 위 스크립트 1회 실행 유닛
│       ├── collect-law.timer  # 월 1회 트리거 (Persistent=true)
│       └── opensearch.service # OpenSearch systemd 기동 (선택)
├── SPRING/                   # Spring Legacy MVC (mazelcode)
│   ├── pom.xml               # Maven (Spring MVC, MyBatis, HikariCP)
│   └── src/main/
│       ├── java/com/mazel/esthetic/
│       │   ├── controller/   # ChatController, PageController
│       │   ├── service/      # RagService (FastAPI HTTP 호출)
│       │   ├── mapper/       # CollectionLogMapper (MyBatis)
│       │   ├── dto/          # ChatRequest, ChatResponse, CollectionLogDto
│       │   └── config/       # JacksonConfig
│       ├── resources/
│       │   ├── config/       # SqlMapConfig.xml, datasource.properties.example
│       │   ├── mappers/      # CollectionLogMapper.xml
│       │   └── spring/       # datasource.xml (HikariCP, MyBatis)
│       └── webapp/WEB-INF/
│           ├── spring/       # servlet-context.xml
│           ├── views/        # chat.jsp
│           └── web.xml
├── .env.example              # 환경변수 템플릿
└── .gitignore
```

---

## 빠른 시작

### 1. 환경 준비

```bash
git clone https://github.com/jynlee/Aesthetic_chatbot.git
cd Aesthetic_chatbot

# Python 가상환경
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 및 DB 정보 입력

# Spring datasource 설정
cp SPRING/src/main/resources/config/datasource.properties.example \
   SPRING/src/main/resources/config/datasource.properties
```

### 2. 데이터 수집 & 인덱싱

```bash
# 법령 수집 (공중위생관리법·화장품법·의료법 773항)
python scripts/collect/collect_law.py

# BGE-M3 임베딩 적재
python scripts/rag/embed_index.py
```

### 3. 서버 기동

```bash
# Redis (질문-답변 캐시, 포트 6379)
redis-server --daemonize yes

# FastAPI RAG 서버 (포트 5000)
python scripts/rag/rag_server.py &

# Spring MVC (포트 8080) — WAR 빌드 후 Tomcat 9 배포
cd SPRING
~/apache-maven-3.9.6/bin/mvn clean package -DskipTests
cp target/mazelcode.war ~/apache-tomcat-9.0.119/webapps/ROOT.war
~/apache-tomcat-9.0.119/bin/catalina.sh start
```

### 4. 접속

| URL | 설명 |
|---|---|
| http://localhost:8080 | 채팅 UI |
| http://localhost:5000/docs | RAG 서버 직접 테스트 (Swagger UI) |

---

## 서버 기동 순서

```
OpenSearch → Ollama → PostgreSQL → Redis → FastAPI → Spring MVC
```

---

## 수집 법령 현황

| 법령명 | MST ID | 조문 수 |
|---|---|---|
| 공중위생관리법 | 259521 | 103항 |
| 화장품법 | 270323 | 152항 |
| 의료법 | 285327 | 518항 |
| **합계** | | **773항** |

## 수집 위해상품/원료 현황

| 구분 | 건수 |
|---|---|
| 회수·판매중지 (recall) | 31건 |
| 사용제한 원료 (ingredient) | 4,079건 |
| **합계** | **4,110건** |

---

