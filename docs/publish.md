# 독립 레포로 분리하기

이 디렉터리는 **자체 완결된 레포 레이아웃**이다 (`.claude-plugin/`,
`LICENSE`, `.gitignore`, `README.md`를 자체적으로 갖고 있다).
현재는 `claude-forge` 안의 하위 디렉터리로 들어와 있는데, 이는
세션 토큰에 레포 생성 권한(`Resource not accessible by integration`)이
없어서 GitHub API로 새 레포를 못 만들었기 때문이다.

아래 순서로 독립 레포로 뗀다.

## 1. GitHub에서 빈 레포 생성

https://github.com/new 에서:

- Repository name: `math-video-agent`
- Public / Private: 취향. 플러그인 마켓플레이스로 설치하려면
  **Public**이어야 한다.
- **README / .gitignore / License는 추가하지 않는다** (이미 있다)

## 2. 히스토리를 보존해서 떼기 (권장)

`git subtree split`으로 이 디렉터리만의 커밋 히스토리를 뽑는다.

```bash
cd /path/to/claude-forge
git subtree split --prefix=math-video-agent -b math-video-standalone

git clone . /tmp/math-video-agent --branch math-video-standalone --single-branch
cd /tmp/math-video-agent
git remote set-url origin https://github.com/juvilan/math-video-agent.git
git branch -M main
git push -u origin main
```

## 3. 히스토리 없이 간단히 (대안)

```bash
cp -r /path/to/claude-forge/math-video-agent /tmp/math-video-agent
cd /tmp/math-video-agent
git init -b main
git add -A
git commit -m "init: manim 수학 영상 제작 플러그인"
git remote add origin https://github.com/juvilan/math-video-agent.git
git push -u origin main
```

## 4. claude-forge에서 제거 (선택)

독립 레포가 정상 동작하는 걸 확인한 뒤에만:

```bash
cd /path/to/claude-forge
git rm -r math-video-agent
git commit -m "chore: math-video-agent를 별도 레포로 분리"
```

`claude-forge`에서도 계속 쓰고 싶으면 서브모듈로 다시 붙일 수 있다:

```bash
git submodule add https://github.com/juvilan/math-video-agent.git math-video-agent
```

## 5. 플러그인 설치 확인

```
/plugin marketplace add juvilan/math-video-agent
/plugin install math-video-agent
```

Private 레포면 마켓플레이스 설치가 안 될 수 있다. 그 경우
로컬 경로로 등록하거나 레포를 Public으로 바꾼다.
