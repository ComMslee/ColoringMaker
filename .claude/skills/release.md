---
name: release
description: "ColoringMaker 릴리즈 자동화. 버전 올리고, 커밋, 태그 생성, GitHub에 푸시하여 Actions가 exe를 빌드하고 Release를 생성하도록 트리거한다. 사용자가 '릴리즈', 'release', '버전 올려', '새 버전', '배포' 등을 언급할 때 이 스킬을 사용한다."
---

# Release - ColoringMaker 릴리즈

이 스킬은 ColoringMaker의 릴리즈 프로세스를 자동화한다.
VERSION 파일 업데이트 → git commit → git tag → push → GitHub Actions 자동 빌드 → Release 생성.

## 사전 조건

- git remote `origin`이 설정되어 있어야 한다
- GitHub CLI (`gh`)가 설치되어 있어야 한다
- push 권한이 있어야 한다

## 릴리즈 절차

### 1. 버전 확인

현재 버전을 `VERSION` 파일에서 읽어 사용자에게 보여준다.
사용자에게 새 버전 번호를 물어본다 (예: `1.1.0`).
만약 사용자가 이미 버전을 지정했으면 그 버전을 사용한다.

### 2. VERSION 파일 업데이트

`VERSION` 파일의 내용을 새 버전 번호로 교체한다. 줄바꿈 포함.

### 3. 커밋되지 않은 변경사항 확인

`git status`로 확인하여, 스테이징되지 않은 변경사항이 있으면 사용자에게 알린다.
VERSION 파일 변경과 함께 모든 관련 변경사항을 스테이징한다.

### 4. 커밋

```
git commit -m "Release v{version}"
```

### 5. 태그 생성

```
git tag v{version}
```

### 6. 푸시

```
git push origin main
git push origin v{version}
```

태그가 푸시되면 `.github/workflows/release.yml`이 자동으로 트리거된다.

### 7. Actions 모니터링

`gh run list --limit 1`로 새 빌드 확인 후, `gh run watch {run_id}`로 진행 상황을 모니터링한다.

### 8. 결과 보고

빌드가 완료되면:
- 성공 시: Release URL을 보여준다 (`gh release view v{version}`)
- 실패 시: 실패 원인을 보여주고 (`gh run view {run_id} --log-failed`) 수정 방안을 제안한다

## 주의사항

- 이미 존재하는 태그를 덮어쓰지 않는다. 태그가 이미 있으면 사용자에게 알린다.
- `main` 브랜치에서만 릴리즈한다.
- push 전에 반드시 사용자에게 확인을 받는다.
