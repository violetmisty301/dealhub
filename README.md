# DealHub v2
개인용 0원 GitHub Pages + GitHub Actions 핫딜 대시보드.

## 설치
이 저장소의 파일을 기존 `dealhub` 저장소 최상단에 업로드하세요. `.github` 폴더도 반드시 포함해야 합니다.

1. Settings > Pages > Deploy from a branch > main / root
2. Settings > Actions > General > Workflow permissions에서 **Read and write permissions** 선택 후 Save
3. Actions > Collect deals > Run workflow를 한 번 실행
4. 완료 후 `data/deals.json`이 갱신되었는지 확인

이후 워크플로는 매시 17분/47분(약 30분 간격)에 실행을 시도합니다. GitHub Actions 스케줄은 지연될 수 있습니다.

## 가격등급
`관측 역대가`는 DealHub 자체 누적 이력 기준입니다. 인터넷 전체 절대 역대가를 의미하지 않습니다.

## 참고
커뮤니티 HTML 구조나 접근 정책이 바뀌면 해당 수집기가 실패할 수 있습니다. 실패해도 다른 수집기는 계속 동작하도록 구성했습니다.
