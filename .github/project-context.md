# 프로젝트 컨텍스트

## 프로젝트 개요
- **이름**: Cline for Eclipse
- **목표**: VSCode Cline을 Eclipse 플러그인으로 포팅
- **타입**: AI 어시스턴트 / Eclipse 플러그인 개발
- **언어**: Java (타겟), TypeScript (원본 분석용)
- **위치**: d:\git\cline-for-eclipse

## 원본 프로젝트 (VSCode Cline)
- **타입**: VS Code 확장
- **언어**: TypeScript, JavaScript, Go
- **핵심 기능**: AI 코드 어시스턴트 (LLM 기반)

## 포팅 목표
### MVP 기능 (1단계)
1. Eclipse 내 Chat View 제공
2. 프롬프트 입력 → LLM 응답 출력
3. 편집기 선택 영역을 컨텍스트로 전송
4. Preferences 페이지로 LLM 설정 관리

### 타겟 환경
- Eclipse 버전: 2024-09 이상
- JDK: 17

#### 회사 환경 (Spark LLM 서버)
- LLM Endpoint: http://172.21.113.31:4000/v1 (LiteLLM → vLLM)
- 모델: Qwen/Qwen3-Coder-30B-A3B-Instruct

#### 집 환경 (Ollama 로컬 서버)
- LLM Endpoint: http://localhost:11434/v1
- API Provider: OpenAI Compatible
- API Key: ollama (아무 문자열 - 인증 불필요)
- **권장 모델**: **qwen3-coder:30b** ✅ 코딩 전문 + Tool Calling 지원

**Ollama 설정 가이드**:
```powershell
# 모델 목록 확인
ollama list

# API 모델 노출 확인
curl http://localhost:11434/v1/models

# 서버 수동 실행 (필요시)
ollama serve

# 권장 모델 다운로드
ollama pull qwen3-coder:30b  # 코딩 전문, RTX 4070 SUPER 최적화
```

**주의사항**:
- Model ID는 `ollama list`로 확인된 전체 이름을 정확히 입력해야 함
- 이름이 일부만 일치하면 "404 model not found" 오류 발생
- Ollama 서버가 실행 중이어야 함 (백그라운드 서비스 또는 수동 실행)

**Ollama 모델별 Tool Calling 지원 현황**:

Cline/Continue 등 OpenAI function_call 기반 환경에서의 실제 Tool Calling 동작 기준:

| 모델명 | Tool Calling 지원 | VRAM (RTX 4070 SUPER 12GB) | 설명 |
|--------|------------------|--------------------------|------|
| **qwen2.5-coder:14b** | ✅ 우수 | ~9GB ✅ | 코딩 전문, Windows 경로 정확 (2025-11-06 추가) |
| `qwen2.5-coder:*-instruct` | ❌ 미지원 | - | 코드 작성 전용, tool schema 미이해 ⚠️ 사용 금지 |
| `qwen2.5:*-instruct` | ⚠️ 제한적 | - | JSON 출력은 하나 OpenAI tool_calls 구조 불안정 |

**RTX 4070 SUPER (VRAM 12GB) 권장 모델**:
- **qwen3-coder:30b** (1순위)
  - 코딩 작업 최적화
  - Windows 경로 인식 정확
  - System Prompt 준수율 높음
  - VRAM: ~9GB (여유 있음)

**❌ 절대 사용하면 안 되는 모델**:
- `qwen2.5-coder:*-instruct` (예: 7b-instruct-q5_K_M)
  - Tool schema를 이해하지 못함
  - read_file, write_to_file 등 Tool 호출 불가
  - 코드 생성만 가능, AI 어시스턴트 기능 동작 안 함

**결론**: 
- OpenAI function_call을 사용하는 Cline에서는 **qwen2.5-coder:14b** 사용
- "-instruct" 계열은 지시 처리에 강하나 tool schema 이해 약함
- Qwen2.5-Coder 사용 시 반드시 일반 버전(14b) 선택, instruct 버전은 Tool 미지원

## VSCode → Eclipse 매핑 전략

### 아키텍처 매핑
| VSCode 요소 | Eclipse 대응 | 구현 클래스 |
|--------------|---------------|--------------|
| extension.ts 명령 | org.eclipse.ui.handlers | ClineCommandHandler.java |
| Webview Panel | ViewPart | ClineView.java |
| Node fetch/axios | java.net.http.HttpClient | ClineHttpClient.java |
| Settings(JSON) | Eclipse Preferences | ClinePreferencePage.java |
| Notifications | MessageDialog | - |
| StatusBar | StatusLineManager | - |

### Eclipse 플러그인 구조
```
ai.devops.cline/
├── META-INF/MANIFEST.MF      # 플러그인 메타데이터
├── plugin.xml                # 확장 포인트 등록
├── build.properties          # 빌드 설정
├── src/ai/devops/cline/
│   ├── Activator.java        # 플러그인 활성화
│   ├── views/
│   │   └── ClineView.java    # Chat UI (SWT)
│   ├── handlers/
│   │   └── ClineCommandHandler.java  # 명령 처리
│   ├── preferences/
│   │   └── ClinePreferencePage.java  # 환경설정
│   └── http/
│       └── ClineHttpClient.java      # LLM API 호출
└── icons/
```

## 프로젝트 구조 이해

### 현재 디렉토리 (VSCode Cline 소스)
- `src/`: TypeScript 소스 코드
  - `core/`: 핵심 AI 어시스턴트 로직 ⭐ 분석 필요
  - `prompts/`: 프롬프트 시스템
  - `exports/`: 외부 API
  - `services/`: 각종 서비스 레이어
- `cli/`: Go 기반 CLI 도구
- `webview-ui/`: React/Vite 기반 UI
- `docs/`: 문서
- `proto/`: Protocol Buffers

### 분석 대상 파일들
- LLM API 호출 로직
- 프롬프트 처리 로직
- 편집기 연동 부분
- 설정 관리 부분

### 생성할 Eclipse 플러그인 디렉토리
```
eclipse-plugin/
└── ai.devops.cline/
    └── (위 구조 참고)
```

### 중요한 파일들과 역할
- `package.json`: 프로젝트 의존성 및 npm 스크립트
- `tsconfig.json`: TypeScript 설정
- `esbuild.mjs`: 빌드 설정
- `src/core/prompts/system-prompt/`: 모듈식 프롬프트 시스템
- `.github/copilot-instructions.md`: Copilot 동작 지시사항

## 개발 환경 설정

### 주요 npm 스크립트
- `watch`: 개발 모드 (프로토버프 + 웹뷰 + TypeScript + esbuild)
- `watch:test`: 테스트 모드
- `compile-standalone`: 독립 실행형 빌드
- `protos`: Protocol Buffers 컴파일

### 빌드 시스템
- esbuild: 빠른 번들링
- TypeScript: 타입 안전성
- Protocol Buffers: 데이터 직렬화
- Vite: 웹뷰 개발 서버

## 코딩 스타일 및 컨벤션
- Java 17 표준 활용
- Eclipse PDE 가이드라인 준수
- SWT/JFace 기반 UI 구현
- 한국어 커밋 메시지 및 문서 작성
- `.github/` 디렉토리를 통한 메타데이터 관리

## 개발 환경 설정

### 필수 도구
- Eclipse IDE 2024-09 이상
- Eclipse PDE (Plugin Development Environment)
- Eclipse LSP4E
- JDK 17
- Git

### VSCode Cline 빌드 (참고용)
- `npm run watch`: 개발 모드
- `npm run protos`: Protocol Buffers 컴파일
- esbuild: 빠른 번들링

## 특이사항
- VSCode Cline의 정교한 프롬프트 시스템 → 단순화 필요
- Protocol Buffers → Java 기본 JSON 처리로 대체
- React UI → SWT 기반 UI로 재구현
- Node.js HTTP 클라이언트 → java.net.http로 대체

## 주요 의사결정 사항
1. **UI 전략**: React WebView 대신 SWT native 위젯 사용
2. **통신 방식**: OpenAI 호환 REST API 유지
3. **설정 관리**: Eclipse Preferences Store 활용
4. **비동기 처리**: Java CompletableFuture 사용
