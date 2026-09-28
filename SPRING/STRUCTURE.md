# SPRING 폴더 구조

Spring Legacy MVC (mazelcode) 프로젝트의 디렉터리 구조입니다.
`target/`은 `mvn package` 실행 시 생성되는 빌드 산출물(gitignore 대상)이라 트리에서 제외했습니다.

```
SPRING
├── src
│   └── main
│       ├── java
│       │   └── com
│       │       └── mazel
│       │           └── esthetic
│       │               ├── config
│       │               │   ├── JacksonConfig.java          # Jackson(JSON) 직렬화 설정
│       │               │   └── SwaggerConfig.java           # Swagger/OpenAPI 설정
│       │               ├── controller
│       │               │   ├── ApiDocsController.java       # OpenAPI JSON 문서 제공
│       │               │   ├── ChatController.java          # POST /api/chat 엔드포인트
│       │               │   └── PageController.java          # 채팅 UI 페이지 라우팅
│       │               ├── dto
│       │               │   ├── ChatRequest.java             # 채팅 요청 DTO
│       │               │   ├── ChatResponse.java            # 채팅 응답 DTO
│       │               │   └── CollectionLogDto.java        # 수집 로그 DTO
│       │               ├── mapper
│       │               │   └── CollectionLogMapper.java     # MyBatis 매퍼 인터페이스
│       │               └── service
│       │                   └── RagService.java               # FastAPI RAG 서버 HTTP 호출
│       ├── resources
│       │   ├── config
│       │   │   ├── SqlMapConfig.xml                  # MyBatis 설정
│       │   │   ├── datasource.properties             # DB 접속 정보 (gitignore, 미커밋)
│       │   │   └── datasource.properties.example      # DB 접속 정보 템플릿
│       │   ├── mappers
│       │   │   └── CollectionLogMapper.xml            # MyBatis SQL 매핑
│       │   └── spring
│       │       └── datasource.xml                     # HikariCP + MyBatis 빈 설정
│       └── webapp
│           ├── WEB-INF
│           │   ├── spring
│           │   │   └── servlet-context.xml            # Spring MVC 서블릿 설정
│           │   ├── views
│           │   │   └── chat.jsp                       # 채팅 UI 화면
│           │   └── web.xml                            # 서블릿 컨테이너 설정
│           └── static
│               ├── css                                 # 스타일시트
│               └── js                                  # 클라이언트 스크립트
└── pom.xml                                             # Maven 프로젝트/의존성 정의

23 directories, 19 files
```
