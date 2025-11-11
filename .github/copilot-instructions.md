# GitHub Copilot Instructions

## 다른 프로젝트에서 이 지시사항 사용하기
이 지시사항 시스템을 다른 프로젝트에서도 사용하려면:
1. 이 프로젝트의 `.github/copilot-instructions.md` 파일을 새 프로젝트의 `.github/` 폴더로 복사
2. `.github/.prompt.txt` 파일도 함께 복사
3. 세션 관리 시스템을 사용하려면:
   - `.github/session-manager.md` 복사
   - `.github/current-session.md` 빈 내용으로 복사
   - `.github/project-context.md` 빈 내용으로 복사
   - `.github/work-history.md` 빈 내용으로 복사
   - `.github/sessions/` 폴더 구조 생성
4. 프로젝트별 특성에 맞게 내용 수정

---

git message 는 한국어로 생성해야 합니다.
생각 내용도 한국어로 생성해야 합니다.

지시한 사항을 묻지 않고 ./.github/.prompt.txt 에 업데이트 합니다.
매 작업을 시작할 때마다 ./.github/.prompt.txt 를 읽고 내용을 따릅니다.

모르는 내용이 있으면 사용자에게 ChatGPT에게 물어보라고 요청합니다.

## 작업 환경 식별 (최우선!)

### 세션 시작 시 필수 확인 절차
**새 작업/세션을 시작할 때마다 다음 순서를 반드시 따릅니다:**

1. **Git 동기화**
   ```bash
   git pull
   ```

2. **현재 장비 IP 확인** (필수!)
   - IP 주소로 현재 작업 중인 장비 식별
   - Linux: `ip addr show` 또는 `hostname -I`
   - Windows: `ipconfig`
   - `.github/development-environment.md`의 Hosts 정보와 대조

3. **접속 방식 확인** (MiniPC만 해당)
   - MiniPC는 두 가지 방식으로 접속 가능:
     - **집에서**: MainPC(192.168.50.102)에서 SSH Remote 접속
       - `$SSH_CLIENT` 환경 변수로 확인: `192.168.50.102`
       - VSCode Remote SSH 사용
     - **회사에서**: Guacamole을 통한 xRDP 로컬 GUI 접속
       - `$XRDP_SESSION` 환경 변수 존재 (값: `1`)
       - `$DISPLAY` 환경 변수 높은 번호 (예: `:10.0`)
       - VSCode 직접 실행 (로컬 GUI)
   - 확인 명령어:
     ```bash
     # SSH 접속 확인
     echo $SSH_CLIENT  # 값 있으면 Remote SSH (예: 192.168.50.102)
     
     # Guacamole (xRDP) 접속 확인
     echo $XRDP_SESSION  # 값이 "1"이면 Guacamole
     
     # 종합 판단
     if [ -n "$XRDP_SESSION" ]; then
         echo "Guacamole 접속 (회사)"
     elif [ -n "$SSH_CLIENT" ]; then
         echo "SSH Remote 접속 (집)"
     else
         echo "로컬 터미널"
     fi
     ```
   
   - **Guacamole 접속 시 추가 환경 변수**:
     - `XRDP_SESSION=1`
     - `XRDP_SOCKET_PATH=/run/xrdp/sockdir`
     - `PULSE_SCRIPT=/etc/xrdp/pulse/default.pa`
     - `XRDP_PULSE_SINK_SOCKET`, `XRDP_PULSE_SOURCE_SOCKET` (오디오)
   
4. **장비별 특성 안내**
   - **MiniPC (192.168.50.196)**: 
     - Docker 사용 가능
     - Linux 환경 (Node.js 20.19.1, Python 3.12.3)
     - 집 네트워크 (공인 IP: 110.13.119.7)
     - 접속 방식: SSH Remote (집) 또는 Guacamole (회사)
   - **DESKTOP-HOME (192.168.50.102)**:
     - Windows 11 Pro
     - Node.js 22.20.0, Python 3.11.8
     - 집 네트워크 (공인 IP: 110.13.119.7)
   - **Spark (172.21.113.31)**:
     - 회사 LLM 서버 (ARM64)
     - 외부 네트워크 제한 있음
     - FRP 연결 시 주의 필요

5. **서버 간 메시지 확인**
   - `.github/inter-session-messages.md` 파일 확인
   - MiniPC와 Spark 간 작업 정보 공유
   - 응답 필요 시 메시지 추가 후 Git 커밋/푸시

**예시 출력:**
```
✅ Git pull 완료
✅ 현재 장비: MiniPC (192.168.50.196)
   📍 접속 방식: 집에서 MainPC Remote SSH (192.168.50.102)
   - Docker 사용 가능
   - Linux 환경 (Node.js 20.19.1, Python 3.12.3)
   - 집 네트워크 (공인 IP: 110.13.119.7)
✅ 서버 간 메시지: 없음
```

또는

```
✅ Git pull 완료
✅ 현재 장비: MiniPC (192.168.50.196)
   📍 접속 방식: 회사에서 Guacamole (xRDP) 로컬 GUI
   - Docker 사용 가능
   - Linux 환경 (Node.js 20.19.1, Python 3.12.3)
   - 집 네트워크 (공인 IP: 110.13.119.7)
✅ 서버 간 메시지: 없음
```

## 개발 환경 정보 (필수 참고!)

### 작업 전 개발 환경 확인
**모든 작업을 시작하기 전에 `.github/development-environment.md` 파일을 참고하여 현재 개발 환경을 파악합니다.**

이 파일에는 다음 내용이 포함되어 있습니다:
- **Hosts**: 개발 PC (Windows/Linux) 및 서버 정보
- **Runtime Environments**: Node.js, Python, Docker 등 설치된 도구 버전
- **Development Tools Configuration**: npm, pip, gradle, maven 등 경로 및 설정
- **Network**: 라우터, LAN 구성, 보안 정보
- **LLM Configuration**: OpenAI API 키 및 엔드포인트 정보

**주요 활용 시나리오**:
- 스크립트 작성 시 올바른 Node.js/Python 버전 참조
- 경로 설정 시 실제 설치된 도구 경로 확인
- Docker 사용 가능 여부 확인 (MiniPC만 가능)
- API 엔드포인트 설정 시 LLM Configuration 참조

## 프로젝트 목표 및 컨텍스트 (최우선!)

### 작업 시작 전 필수 확인
**모든 작업을 시작하기 전에 반드시 `.github/project-goal.md` 파일을 먼저 읽고 참고해야 합니다.**

이 파일에는 다음 내용이 포함되어 있습니다:
- 프로젝트 개요 및 목표
- VSCode Cline → Eclipse 포팅 전략
- 기술 스택 및 아키텍처
- 개발 단계별 체크리스트
- LLM 엔드포인트 및 설정 정보

작업 시작 시:
1. `.github/development-environment.md` 읽기 → 개발 환경 확인
2. `.github/project-goal.md` 읽기 → 프로젝트 목표 확인
3. 현재 작업이 프로젝트 목표와 부합하는지 확인
4. 필요한 기술 스택 및 설정 정보 파악
5. 작업 진행

## 코드 품질 관리 및 에러 검증

### 코드 변경 후 반드시 에러 확인 (중요!)
**모든 코드 변경 작업 완료 후 반드시 `get_errors` 도구로 문법 오류 확인:**

1. **VSCode Workspace 통합의 장점**
   - Eclipse 없이도 VSCode에서 Java 문법 오류 파악 가능
   - Eclipse 플러그인 코드 수정 시 즉시 에러 확인
   - 실시간 피드백으로 빠른 수정

2. **에러 확인 및 수정 절차**
   ```
   1. 코드 수정 완료
   2. get_errors 도구 실행하여 컴파일 에러 확인
   3. 에러 발견 시 즉시 수정
      - import 누락: 필요한 import 문 추가
      - 타입 불일치: 올바른 타입으로 수정
      - 메서드 시그니처 오류: 정확한 파라미터/리턴 타입 사용
   4. 다시 get_errors로 검증
   5. 에러 없을 때까지 반복
   ```

3. **Eclipse 프로젝트 특성 이해**
   - Eclipse PDE (Plugin Development Environment) 프로젝트
   - Maven/Gradle이 아닌 Eclipse 고유 빌드 시스템
   - `.classpath` - 클래스패스 설정
   - `MANIFEST.MF` - 플러그인 의존성 관리 (Require-Bundle)
   - Eclipse API 사용 시 반드시 MANIFEST.MF에 번들 추가

4. **주의사항**
   - Eclipse API (org.eclipse.*) import 에러가 가장 흔함
   - MANIFEST.MF의 Require-Bundle 확인
   - Java 버전 호환성 (JavaSE-17)

**예시:**
```
수정한 파일: eclipse-plugin/ai.devops.cline/src/.../SomeClass.java

1. get_errors 실행
   → "import org.eclipse.swt.SWT cannot be resolved" 발견

2. 원인 분석:
   - SWT 라이브러리가 필요
   - MANIFEST.MF에 org.eclipse.swt 번들 누락

3. 수정:
   - MANIFEST.MF의 Require-Bundle에 추가 또는
   - import 문 수정

4. 다시 get_errors로 확인
   → 에러 없음 ✅
```

## Eclipse 플러그인 버전 관리 (필수!)

### 매 빌드마다 버전 번호 업데이트 (중요!)

**⚠️ Eclipse F11로 빌드할 때마다 반드시 버전 번호를 올려야 합니다!**

**이유:**
- **플러그인 재빌드 즉시 확인** - Welcome 화면에서 새 버전 번호를 보고 코드 변경이 반영되었는지 즉시 확인
- Eclipse F11로 플러그인 실행 시 Welcome 화면 제목에 버전 표시
- 코드 변경 내역 추적 용이
- 캐시 문제나 빌드 실패 즉시 감지

**핵심 원칙:**
```
코드 수정 → 버전 업데이트 → Eclipse F11 재빌드 → Welcome 화면에서 새 버전 확인 ✅
```

**버전 업데이트 시점:**
- ✅ **Eclipse F11로 빌드하기 직전마다** - 새 빌드임을 확인하기 위해
- ✅ 코드 수정 직후 (기능 추가/수정, 버그 수정)
- ✅ Git 커밋 전
- ⚠️ **중요**: 코드를 수정하고 Eclipse에서 재빌드할 때마다 버전을 올려야 Welcome 화면에서 즉시 확인 가능

**버전 업데이트 절차:**

1. **ClineView.java 파일 수정**
   ```java
   // 위치: eclipse-plugin/ai.devops.cline/src/ai/devops/cline/views/ClineView.java
   // Line 56 (약)
   
   private static final String VERSION = "2024.11.09.X-description";
   ```

2. **버전 번호 형식**
   - `YYYY.MM.DD.X-description`
   - X: 일자별 순차 번호 (1부터 시작, **매 빌드마다 증가**)
   - description: 변경 내용 간단 요약 (kebab-case)

3. **예시:**
   ```java
   // 첫 번째 빌드
   private static final String VERSION = "2024.11.09.1-fix-button";
   // Eclipse F11 → Welcome 화면 확인: "Welcome to Cline for Eclipse (v2024.11.09.1-fix-button)"
   
   // 추가 수정 후 두 번째 빌드
   private static final String VERSION = "2024.11.09.2-add-feature";
   // Eclipse F11 → Welcome 화면 확인: "Welcome to Cline for Eclipse (v2024.11.09.2-add-feature)"
   
   // 또 수정 후 세 번째 빌드
   private static final String VERSION = "2024.11.09.3-refactor";
   // Eclipse F11 → Welcome 화면 확인: "Welcome to Cline for Eclipse (v2024.11.09.3-refactor)"
   ```

4. **버전 표시 위치**
   - **Welcome 화면 제목**: `Welcome to Cline for Eclipse (v버전)` ← **여기서 즉시 확인!**
   - 대화 메시지: `You (v버전):`

5. **재빌드 확인 방법**
   ```
   1. ClineView.java에서 VERSION 상수 변경
   2. 파일 저장 (Ctrl+S)
   3. Eclipse F11 (Run) 실행
   4. ✅ Welcome 화면 제목에서 새 버전 번호 확인
   5. ❌ 이전 버전이 보이면 → 빌드 실패 또는 캐시 문제
   ```

**자동화 스크립트 (PowerShell):**
```powershell
# 버전 자동 증가 스크립트
$file = "eclipse-plugin/ai.devops.cline/src/ai/devops/cline/views/ClineView.java"
$content = Get-Content $file -Raw -Encoding UTF8

# 현재 버전 추출
if ($content -match 'VERSION = "(\d{4})\.(\d{2})\.(\d{2})\.(\d+)-(.+)"') {
    $date = Get-Date -Format "yyyy.MM.dd"
    $today = "$($Matches[1]).$($Matches[2]).$($Matches[3])"
    
    if ($date -eq $today) {
        # 같은 날이면 번호만 증가
        $newNum = [int]$Matches[4] + 1
    } else {
        # 다른 날이면 1부터 시작
        $newNum = 1
    }
    
    $desc = Read-Host "변경 내용 (kebab-case)"
    $newVersion = "$date.$newNum-$desc"
    
    $content = $content -replace 'VERSION = ".*"', "VERSION = `"$newVersion`""
    $content | Out-File $file -Encoding UTF8 -NoNewline
    
    Write-Host "✅ 버전 업데이트 완료: $newVersion"
}
```

**주의사항:**
- ✅ **Eclipse F11 빌드 전에 항상 버전 업데이트** → Welcome 화면에서 즉시 확인
- ❌ 버전을 안 올리면 이전 빌드인지 새 빌드인지 구분 불가
- ✅ Welcome 화면에서 새 버전이 안 보이면 빌드 실패 또는 캐시 문제

## MCP Tools 사용 규칙

### 사용 가능한 MCP 서버
VSCode의 `mcp.json`에 다음 MCP 서버들이 등록되어 있습니다:

1. **mcp-websearch** - 웹 검색 및 크롤링
   - Repository: https://github.com/lisyoen/mcp-websearch
   - 설치 경로: `D:\git\mcp-websearch`
   - `mcp_mcp-websearch_web_search` - Bing 검색
   - `mcp_mcp-websearch_web_fetch` - URL 페이지 가져오기
   - `mcp_mcp-websearch_web_scrape` - CSS 선택자로 스크래핑
   - `mcp_mcp-websearch_web_crawl` - BFS 크롤링

2. **mcp-fileops** - 로컬 파일 작업
   - Repository: https://github.com/lisyoen/mcp-fileops
   - 설치 경로: `D:\git\mcp-fileops`
   - `mcp_mcp-fileops_read_file` - 파일 읽기
   - `mcp_mcp-fileops_write_to_file` - 파일 쓰기
   - `mcp_mcp-fileops_append_to_file` - 파일에 추가
   - `mcp_mcp-fileops_list_directory` - 디렉토리 목록
   - `mcp_mcp-fileops_delete_file` - 파일 삭제
   - `mcp_mcp-fileops_open_file_vscode` - VSCode에서 파일 열기

### MCP 서버 자동 설치 및 설정
필요한 MCP 서버가 없는 경우 자동으로 설치합니다:

1. **디렉토리 존재 확인**
   ```powershell
   Test-Path "D:\git\mcp-websearch"
   Test-Path "D:\git\mcp-fileops"
   ```

2. **없으면 Git Clone 및 빌드**
   ```powershell
   # mcp-websearch 설치
   if (!(Test-Path "D:\git\mcp-websearch")) {
       cd D:\git
       git clone https://github.com/lisyoen/mcp-websearch.git
       cd mcp-websearch
       npm install
       npm run build
   }
   
   # mcp-fileops 설치
   if (!(Test-Path "D:\git\mcp-fileops")) {
       cd D:\git
       git clone https://github.com/lisyoen/mcp-fileops.git
       cd mcp-fileops
       npm install
       npm run build
   }
   ```

3. **VSCode MCP 설정 확인**
   - 설정 파일: `$env:APPDATA\Code\User\mcp.json`
   - 필요 시 자동으로 서버 등록 추가

### 파일 작업 도구 사용 우선순위

**원칙: 빌트인 도구 우선, 실패 시에만 MCP 도구 사용**

#### 파일 작업 우선순위

1. **파일 읽기**
   - 1순위: `read_file` (빌트인 도구)
   - 2순위: `mcp_mcp-fileops_read_file` (빌트인 실패 시)

2. **디렉토리 목록**
   - 1순위: `list_dir` (빌트인 도구)
   - 2순위: `mcp_mcp-fileops_list_directory` (빌트인 실패 시)

3. **파일 생성**
   - 1순위: `create_file` (빌트인 도구)
   - 2순위: `mcp_mcp-fileops_write_to_file` (빌트인 실패 시)

4. **파일 수정**
   - 1순위: `replace_string_in_file` (빌트인 도구)
   - 2순위: `mcp_mcp-fileops_write_to_file` (빌트인 실패 시)

5. **파일에 내용 추가**
   - 작업 영역 내: 빌트인 도구 사용 (필요 시 파일 읽기 + 수정)
   - 작업 영역 외: `mcp_mcp-fileops_append_to_file`

6. **파일 삭제**
   - PowerShell 명령 또는 `mcp_mcp-fileops_delete_file`

#### MCP 도구를 사용해야 하는 경우
- ✅ 작업 영역(workspace) 외부 파일 작업
- ✅ 빌트인 도구 실패 시
- ✅ 특수한 파일 시스템 작업

#### 빌트인 도구 사용 시 주의사항
- `replace_string_in_file`: 변경 전후 3-5줄 컨텍스트 포함
- `create_file`: 완전한 파일 내용 제공
- 에러 발생 시 MCP 도구로 대체

## 작업 세션 연속성 관리

### 세션 관리 파일 구조

1. **`.github/current-session.md`** - 현재 활성 세션 정보 (간략)
   - 현재 세션 ID만 표시
   - 상세 내용은 세션 파일 참조

2. **`.github/session-manager.md`** - 최근 10개 세션 목록
   - 최근 작업만 추적
   - 오래된 세션은 work-history.md로 이동

3. **`.github/sessions/session-ID.md`** - 각 세션의 상세 정보
   - 작업 목적, 계획, 진행 상황, 결과
   - 모든 세션 정보는 여기에만 기록

4. **`.github/work-history.md`** - 완료된 옛날 세션 아카이브

5. **`.github/project-context.md`** - 프로젝트 전체 맥락

### 작업 시작 시

1. **Git 동기화 및 세션 확인**
   ```
   git pull
   ```

2. **현재 세션 확인**
   - `.github/current-session.md` 읽기 → 현재 세션 ID 확인
   - `.github/sessions/session-ID.md` 읽기 → 상세 정보 로드
   - `.github/project-goal.md` 읽기 → 프로젝트 목표 확인

3. **새 작업 시작하는 경우**
   - 새 세션 파일 생성 (`.github/sessions/session-ID.md`)
   - current-session.md 업데이트 (새 세션 ID로 변경)
   - session-manager.md에 새 세션 추가
   - TODO 리스트 생성 (manage_todo_list 도구)

### 작업 중

- **세션 파일만 업데이트**: `.github/sessions/session-ID.md`
- 진행 상황, 결정사항, 문제점 등을 지속적으로 기록
- current-session.md와 session-manager.md는 필요 시에만 간단히 업데이트

### 작업 완료 시

1. **세션 파일 완료 처리**
   - `.github/sessions/session-ID.md`: 상태 "완료", 결과 작성
   - 테스트 방법 제시 (중요!)

2. **관리 파일 업데이트**
   - `.github/session-manager.md`: 상태 "완료"로 변경
   - `.github/current-session.md`: 다음 세션 준비 (또는 비우기)

3. **Git 동기화**
   ```
   git add .
   git commit -m "세션 session-ID 완료: [작업 요약]"
   git push
   ```

### 세션 ID 형식

**형식**: `session-YYYYMMDD-XXX-description`
- YYYYMMDD: 날짜 (예: 20251108)
- XXX: 일자별 순차 번호 (001부터)
- description: 간단한 작업 설명 (선택적)

**예시**: `session-20251108-019-recent-tasks`

---

**핵심 원칙**: 
- 상세 정보는 **세션 파일 하나**에만 기록
- 관리 파일들은 **참조용으로만** 사용 (최소한의 정보만)
- 중복 기록 금지
