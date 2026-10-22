<div align="center">

<img src="../../assets/hero.png" alt="dsh-on-android" width="100%">

# dsh-on-android

**Android 폰의 [OpenMinis](https://github.com/OpenMinis/OpenMinis)(Minis) 안에서 DeepSeek Harness를 돌리고, 폰의 파일 디렉터리를 워크스페이스로 마운트합니다.** root 불필요, Termux X11 불필요, Chromium 빌드 불필요 — PRoot + Alpine(musl / aarch64)의 네 가지 함정은 이미 해결했습니다.

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · **한국어**

</div>

---

## 세 줄이면 끝

```bash
git clone https://github.com/maple564/dsh-on-android.git && cd dsh-on-android
sh install.sh                                  # 의존성 → dsh → node-pty 재빌드 → /opt/dsh-harness 고정
export DEEPSEEK_API_KEY=sk-xxxxxxxx            # 또는 ~/.dsh/.env 에 이 한 줄만
dsh-go                                         # http://127.0.0.1:3080 열기
```

웹 UI 첫 진입: 「계속」→ 쓰기 가능한 워크스페이스 선택 → 상단에 `DeepSeek-V4-Flash`가 보이면 연결 완료.

---

## 무엇 위에서 도는가

레퍼런스 환경은 **[OpenMinis](https://github.com/OpenMinis/OpenMinis)(구 Minis, 오픈소스, GPLv3)** 입니다. 폰 안에 완전한 Alpine Linux 샌드박스를 넣는 AI 에이전트 앱이고, 그 샌드박스가 곧 PRoot + musl + aarch64 — 이 저장소가 상대하는 바로 그 환경입니다.

- **OpenMinis 안에서**: 앱 설치 → 아무 세션에서 `sh install.sh` 실행. 샌드박스, `android-*` CLI, 파일 마운트가 이미 준비되어 있습니다(`/var/minis/mounts/...`, `/sdcard/Documents`).
- **다른 환경**: Termux + `proot-distro install alpine`, UserLAnd 등 어떤 PRoot 컨테이너든 가능. `install.sh`는 `apk`, `npm`, `node-gyp`만 필요합니다.

---

## 희소한 지점: 그냥 "돌아가는" 게 아니라, 폰 안의 파일을 직접 다룹니다

노트북에서 dsh를 돌리는 건 누구나 합니다. **폰에서 돌리는 가치는 dsh 자체가 아니라, 사진·다운로드·메신저 첨부 파일 바로 옆에 있다는 점**입니다.

OpenMinis는 폰 저장소를 샌드박스의 고정 경로로 마운트합니다.

| 폰 쪽 | 샌드박스 안 | 주 용도 |
|---|---|---|
| `/sdcard/Documents` | `/var/minis/mounts/Documents/` | 문서, 강의자료, 내려받은 PDF |
| `/sdcard/Download` | `/var/minis/mounts/Download/` | 브라우저 다운로드, 메신저 저장 파일 |
| 세션 간 공유 | `/var/minis/shared/` | 여러 세션이 함께 쓰는 산출물 |

dsh 워크스페이스를 이 경로로 돌리면 **폰을 읽고 쓰는 에이전트**가 됩니다.

- **결과물이 폰에 그대로 남습니다** — `Documents/dsh-workspace/`에 쓴 PPTX / PDF / ICS / 스크립트를 앱을 닫은 뒤 파일 관리자나 오피스 앱에서 바로 엽니다. "다시 폰으로 보내기" 단계가 없습니다.
- **반대 방향도 가능** — `.docx`, 시간표 스크린샷, 영수증 PDF를 Documents에 넣어 두면 세션 안에서 읽고 고치고 다시 내보냅니다.
- **오프라인 + 프라이버시** — 추론은 내 API 키로, 파일은 기기 밖으로 나가지 않습니다.
- **어디서나** — 지하철에서, 침대에서, 여행지에서.

### 핵심 한 단계: 워크스페이스를 마운트 경로로

dsh 기본 워크스페이스는 `/root`인데 PRoot에서 `Operation not permitted`가 나기 쉽고 폰에서는 보이지도 않습니다. 마운트 경로로 바꾸면 끝입니다.

```bash
mkdir -p /var/minis/mounts/Documents/dsh-workspace
cp ~/.dsh/storages/workspace.json ~/.dsh/storages/workspace.json.bak
python3 - <<'PY'
import json, uuid, datetime
p = json.load(open('/root/.dsh/storages/workspace.json'))
new = "/var/minis/mounts/Documents/dsh-workspace"
for ws in p["tables"]["workspaces"].values():
    if ws.get("path") == new:
        raise SystemExit("이미 등록됨")
now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", ".000Z")
wid = "ws-" + uuid.uuid4().hex[:12]
p["tables"]["workspaces"][wid] = {"path": new, "title": "dsh-workspace",
                                  "sessionIds": [], "createdAt": now, "updatedAt": now}
p["global"]["workspaceIds"].append(wid)
json.dump(p, open('/root/.dsh/storages/workspace.json', 'w'), indent=2, ensure_ascii=False)
print("등록 완료", wid)
PY
pkill -f 'dsh/lib/bin.js'; sleep 2; dsh-go
```

**확인**: 새 세션에서 `hello.txt`를 쓰게 하고, 폰 파일 관리자로 `Documents/dsh-workspace/`를 열어 보세요. 파일이 있으면 성공입니다.

---

## 왜 이 저장소가 필요한가

`npx @deepseek-ai/dsh`는 glibc 데스크톱에서는 한 줄입니다. musl에서는 네 개의 벽을 연달아 만나고, **모든 에러 메시지가 원인을 잘못 가리킵니다.**

| # | 보이는 에러 | 흔한 오해 | 실제 원인 | 해결 |
|---|---|---|---|---|
| 1 | `Error loading shared library ld-linux-aarch64.so.1` | 시스템 라이브러리 부족 | node-pty가 **glibc 프리빌드** | `node-gyp rebuild` |
| 2 | `--expose-internals is required for HMR` | 플래그가 안 먹힘 | `NODE_OPTIONS`에서는 **허용되지 않음** | node 명령줄로 전달 |
| 3 | `.env sets DSH_PERMISSION_MODE ... only the launching environment may set` | .env 형식 오류 | **bootstrap 변수** | wrapper에서 `export` |
| 4 | `no sandbox backend is usable` | 권한 부족 | 컨테이너에는 workspace-write 백엔드가 없음 | `DSH_PERMISSION_MODE=danger-full-access` |

---

## 요구 사항

| 항목 | 요구 |
|---|---|
| 호스트 | Android 10+ (Android 16 / aarch64 실측) |
| 컨테이너 | 임의의 PRoot Linux: **OpenMinis / Minis 샌드박스**, `proot-distro`, UserLAnd 등 |
| 배포판 | Alpine 3.20+(musl), glibc 계열은 재빌드 자동 생략 |
| Node | 20 이상 (22.23.2 실측) |
| 디스크 | 약 800 MB |
| root | **불필요** |

---

## 명령

| 명령 | 용도 |
|---|---|
| `dsh --version` | 설치 확인 |
| `dsh-go` | 웹 UI 실행 및 열기 |
| `dsh-go --status` | 실행 중인지 확인 |
| `pkill -f 'dsh/lib/bin.js'` | 중지 |
| `~/.dsh-web.log` | 로그 |

---

## FAQ

**`Cannot find module`** — 디렉터리 구조가 평탄화되었습니다. `/opt/dsh-harness/node_modules/@deepseek-ai/dsh/lib/bin.js` 여야 합니다.

**웹 UI가 하얗게 보임** — ① 브라우저 엔진의 Canvas/WebGL 지원 부족(앱 내 WebView는 하얘도 DOM은 정상, Chrome으로 열기) ② 서버 미기동: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3080/`의 결과가 `000`.

**파일 쓰기에서 `Operation not permitted`** — PRoot 뷰 불일치. 워크스페이스를 마운트 경로로 옮기세요.

**백그라운드로 보내면 죽음** — `nohup`은 SIGHUP만 막습니다. Termux 포그라운드 서비스 + 배터리 최적화 예외가 필요합니다.

---

## 알려진 제한

- **프로세스 수명은 호스트에 종속**: 앱/컨테이너가 죽으면 dsh도 죽습니다. 긴 작업은 잘게 나누세요.
- **긴 세션은 회수됨**: 메모리 부족 시 탭이 파괴되어 연결이 끊깁니다. 새로고침하면 복구됩니다.
- **성능**: PRoot syscall 변환 비용으로 첫 `npm install`이 느립니다.
- **3080을 공개하지 마세요**: 기본이 full-access라 셸을 넘겨주는 것과 같습니다.

## 라이선스

[MIT](../../LICENSE)
