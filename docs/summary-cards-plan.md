# 진행 상황 카드 v2 — 기획서 (fable, 2026-09-26)

블로그/X용 공유 이미지 두 번째 세트. 첫 세트(`docs/media/summary/01–05`, 2026-09-24 저녁, 발사 20회 시점)는
그대로 두고(블로그 "첫날" 절에 쓴다), 새 세트는 별도 번호로 만든다. 구현은 opus, 검수는 fable.

**절대 규칙**
- 게임에 손대지 않는다: `uv run ksp …`, `shoot_crafts.py`, `shoot_portraits.py`, `extract_save.py`, KSP 재시작 금지.
  사진은 `docs/media/`와 `docs/media/summary/{crafts,crew}/`에 있는 것만 쓴다. 없는 사진은 자리표시자(§5.3).
- 숫자는 전부 `docs/record/career.json`에서 읽는다. career.json에 없는 숫자는 먼저 §4의 표대로 career.json에
  넣고(각 값의 출처 LOG 줄 번호가 §4에 있다), 스크립트는 그것만 읽는다. 스크립트 안에 숫자를 쓰지 않는다.
- 커밋하지 않는다.

---

## 1. 감사: 옛 세트에서 무엇이 낡았나

| 카드 | 상태 | 문제 |
|---|---|---|
| 01 scoreboard | 낡음 | 20회/9·8·3, 자금 최고 1.30M, 과학 750.5, 기술 16, 시설 6×Lv2, "Duna NEXT". 지금은 44회, 자금 최고 2.84M, 기술 36, R&D Lv3, Duna·Eve 도달, Jool 이동 중. `funds_timeline`이 #20에서 끝남. |
| 02 crafts | 낡음 | 12 career + 4 sandbox. 지금 커리어 기체 28종(슬러그 기준), 그중 발사대 사진이 있는 건 13종뿐. 샌드박스 리허설은 09-25에 금지돼 "sandbox" 절 자체가 옛 이야기. |
| 03 timeline | 낡음 | #1–#20 하드코딩 레이아웃(`DETAIL` dict). 결과 코드가 ok/rev/dead 3종뿐인데 career.json에는 `partial`, `failed`, `in progress`, `en route`가 생겼다(`RESULT_CODE`에 없어 지금 img1/img3는 KeyError로 죽는다). |
| 04 science | 낡음 | `science_by_body`(89.9/538.6/122)와 바이옴별 표는 09-24 세이브(`career-save.json`) 기준. 지금 세이브는 못 읽으므로(규칙) 이 카드 형식은 재현 불가. |
| 05 crew | 낡음 | 4명. 지금 명단 10명(구조 6명), Jeb은 Eve 궤도, Valentina는 Duna에서 귀환 중, Bob·Gwenbro는 정거장. `career-save.json`의 assert에 묶여 있음. |

새로 생긴 이야기(카드에 꼭 들어가야 함): Duna 착륙·이륙·귀환 중(Valentina, 600일 대기), Eve 궤도(Jeb, 과학 ~1017 탑재),
Jool 탐사선 발사(핵엔진, 도착 5년 뒤), Minmus 과학 정거장, 중계위성 4기, 구조 6명, Bob 고립 → 궤도 급유 구조,
Klaw 5번 실패 → 우리 버그, 저장 NRE, R&D Lv3, 실제 3일 동안 게임 시간 2년 9개월.

---

## 2. 카드 세트 (10장, 1080×1350 @2x, 옛 세트와 같은 시각 언어)

언어 규칙: 카드마다 **한국어 헤드라인 한 줄**(3초 메시지)과 한국어 짧은 라벨. 고유명사(Kerbin, Mun, Minmus, Duna, Eve,
Jool, 기체 이름, 커발 이름)와 범례/축의 마이크로 라벨은 옛 세트처럼 영어 그대로. 문장은 쓰지 않는다
(헤드라인 제외, 헤드라인은 18자 이내). 숫자는 JetBrains Mono, 본문은 Space Grotesk + **Noto Sans KR**(한글 폴백, §5.1).

공통 크롬: 왼쪽 위 kicker(영문 섹션명), 오른쪽 위 날짜 칩 `2026-09-26 · day 3`, 아래 footer
`KSP 1.12 · career · flown by Claude` + 점 인디케이터(10개). 별 배경 `stars(seed)`는 카드마다 다른 seed.

### 01 `scoreboard` — 스코어보드 (옛 01의 갱신)
- 3초 메시지: **"발사 44번, 3일 만에 Kerbin에서 Jool까지"** (헤드라인).
- 레이아웃(옛 01 그대로, 아래만 바꿈):
  - 큰 숫자 `44 LAUNCHES`; 결과 막대 5분할: ✓ 성공 / ↩ revert / ☠ 사망 / ✕ 실패·부분 / ● 진행 중(파랑). 개수는
    `career_launches[].result`를 `RESULT_CODE`(§5.1)로 접어 센다.
  - 번호 스트립 1–44를 두 줄(1–22, 23–44)로. FIRST(§4.3 `firsts[].n`)는 금테.
  - 자금 차트: `career_now.funds_timeline`(§4.1로 교체) 전체. y축 최대 3M. 시설 마커는 `funds_timeline[].facility`
    로 표기(옛 `funds_timeline_facility_markers` 삭제). 라벨 있는 점만 숫자 표시.
  - 타일 4개: `TECH 36 · R&D Lv.3`(`research` 길이, `career_now.facilities`) / `KERBALS ☠3 · 구조 6`
    (`kerbals.deaths_that_stood` 길이, `kerbals.rescued` 길이) / `REP 438`(`career_now.reputation`) /
    `GAME TIME 2y 273d ↔ real 3 days`(`career_now.ut`를 21600 s/일, 426일/년으로 환산; `career_now.real_days`).
  - 천체 줄 6개: Kerbin(궤도 #4) · Minmus(★ #10 Bill) · Mun(★ #16 Bob) · Duna(★ #30 Valentina, 착륙) ·
    Eve(궤도 #37 Jeb) · Jool(점선, `EN ROUTE #44`). 각 배지는 `firsts[]`에서 body별 최초 항목을 고른다.

### 02 `journey` — 어디까지 갔나 (신규, 세트의 대표 이미지)
- 3초 메시지: **"달 둘·행성 하나에 내렸고, 셋이 더 밖에 있다"**.
- 레이아웃: 위 2/3는 도식적 태양계(동심 궤도: Eve · Kerbin(+Mun, Minmus) · Duna(+Ike) · Jool; 축척 무시, 궤도 반지름은
  보기 좋게). 천체마다 `planet()` 디스크와 상태 배지:
  - Kerbin: 위성 4(`live_missions[]` type satellite 개수). Minmus: 착륙 미션 6 · 정거장 1(Bob, Gwenbro).
    Mun: 착륙 미션 2 · 급유 구조 1. 착륙 미션 수는 `landings_by_body`(§4.6).
  - Duna: 착륙 1 → 귀환 중(Valentina), Kerbin 쪽 화살표. Eve: 궤도(Jeb, 과학 ~1017 탑재, 대기 중).
  - Jool: 점선 궤도 + 이동 중 탐사선 아이콘, `arrival 5y`(`live_missions[]` jool-1 `next_ut` 환산).
- 아래 1/3: "지금 날고 있는 것" 4행(`live_missions[]` type probe/crewed/station): 기체 · 승무원 · 어디 · 다음 일(UT를
  "d+N일"로 환산). 썸네일: `2026-09-26_jool-1_pad.png`(크롭), `2026-09-25_duna-1_landed.png`,
  `2026-09-26_eve-1_eve-pass.png`, `2026-09-26_minmus-lab-1_orbit.png`.

### 03 `how` — 어떻게 하나 (신규, KSP를 모르는 독자용)
- 3초 메시지: **"화면을 안 본다 — 명령 하나가 비행 단계 하나"**.
- 레이아웃: 세로 파이프라인 도식 4단(`how.stack`): `Claude Code (WSL 터미널)` → `uv run ksp ascent / transfer / land …` →
  `kRPC + KspBot 모드 (C#)` → `KSP 1.12.5`. 오른쪽에 터미널 창 모양 패널: 한 미션분 명령 시퀀스(`how.commands`).
- 하단 규칙 칩 4개(`how.rules_ko`).
- 숫자 없음.

### 04 `launches-a` — 발사 #1–#22 / 05 `launches-b` — 발사 #23–#44 (옛 03의 갱신·분할)
- 3초 메시지: 04 **"첫 이틀: 달 두 개, 사망 3"**, 05 **"둘째 날부터: 구조·행성·정거장"**.
- 레이아웃: 옛 03 카드 그대로(4열 × 6행, 마지막 행 남는 2칸은 범례/빈칸). 카드 하나 = 썸네일 + `#n` + 결과 배지 +
  목적지 행성 + `stat` + 승무원. FIRST는 금테 + 배지. 결과 코드 5종(§5.1), `live`는 파란 테두리 + 점.
- 데이터: `career_launches[]`의 `n, slug, dest, stat, crew, result, revert_death_count, diverted_to`. `DETAIL` dict 같은
  번호별 하드코딩 금지: 표시는 규칙으로 — `stat`이 있으면 mono, `crew`가 있으면 kerbal 칩(`-`는 무인, 표시 안 함),
  `result == crew lost`면 해골 + 이름, `revert_death_count`면 흐린 해골 n개, `diverted_to`면 화살표 + 행성,
  `stat`에 `t=0`이 들어가면 boom 아이콘.
- `dest` 값에 `kerbin-orbit`, `minmus-orbit`, `eve`, `jool`이 새로 있다: `BODY` 매핑에 추가(`kerbin-orbit` → Kerbin +
  orbit 아이콘, `minmus-orbit` → Minmus + orbit 아이콘).
- 썸네일: §5.3 표. 사진이 없는 기체는 자리표시자.

### 06 `crafts` — 기체의 진화 (옛 02 대체)
- 3초 메시지: **"호퍼에서 핵엔진 탐사선까지"**.
- 레이아웃: 가로 6칸, 왼쪽에서 오른쪽으로 커지는 느낌(사진 높이를 질량에 비례해 살짝 다르게, 최소 60 %):
  Hopper 1(#1) · Orbiter 1(#4) · Minmus Lander 1(#10) · Mun Lander 3(#16) · Duna 1(#30) · Jool 1(#44).
  칸마다 이름, 첫 발사 #, 있는 값만: `parts / t / funds`. 아래에 한 줄 결과(`firsts[]`의 `label_ko`).
- 데이터: `crafts[]`(§4.7). 값이 없으면 칸을 비운다(Hopper 1, Orbiter 1의 부품 수·질량은 기록에 없음 → 표시 안 함).
- 사진: `summary/crafts/{hopper-1,orbiter-1,minmus-lander-1,mun-lander-3,duna-1}.jpg` + `jool-1` 크롭(§5.3).

### 07 `science` — 과학은 어디서 왔나 (옛 04 대체)
- 3초 메시지: **"착륙 없이 1,600점 — 과학 수확 6번"**.
- 레이아웃: 위: 가로 막대 6개(`science_hauls[]`): 기체 · 방법(회수/전송) · +점수. 옆에 작은 썸네일
  (있는 것만: minmus-science-1 midlands, minmus-lab-1 orbit). 중간: "싣고 있는 과학" 칩 3개(`science_aboard[]`).
  아래: 기술 트리 36개 아이콘 그리드(옛 04 스타일, 6×6) + `R&D Lv.3` 배지. 노드 표시명은 `research_names`(§4.5).
- 총 획득 과학은 **표시하지 않는다**(연구 지출과 섞여 기록에서 정확히 복원 불가). "큰 수확 6번 합계 4,246"은
  `science_hauls`의 합으로 계산해 표시해도 된다.

### 08 `crew` — 승무원 (옛 05의 갱신)
- 3초 메시지: **"셋을 잃었고(확정), 여섯을 구했다"**.
- 레이아웃: 위 2×2 큰 카드(Jebediah, Valentina, Bob, Bill: `summary/crew/*.png` 초상). 각: 이름·직종·**지금 어디**
  (`status_ko`) · 방문 천체 아이콘(`flights[]`의 dest를 career_launches에서 조인) · 해골(확정 빨강 / revert 흐림, `#n`).
  아래: "구조된 6명" 한 줄(`kerbals.rescued[]`): img5.py의 `kerbal()` SVG 얼굴(초상 없음) + 이름 + 직종 + `#n`.
  오른쪽 위 집계 `☠ 3 · ☠(revert) 11 · ↻ 3`(`deaths_that_stood` 길이, `deaths_undone_by_revert_count`, respawn = 확정 사망 수).
- 사진 2장 유지: `crafts/photo-pad-explosion.jpg`(t=0) · `2026-09-26_rescue-3_grabbed.png`(Klaw 구조).
  옛 `career-save.json` assert는 쓰지 않는다.

### 09 `failures` — 무엇이 잘못됐나 (신규)
- 3초 메시지: **"실패 목록이 곧 개발 일지"**.
- 레이아웃: 세로 리스트 10행(`incidents[]` 중 `hidden`이 아닌 것): 아이콘(boom/skull/wrench/bug) · `#n` · 한국어 한 줄
  (≤ 28자) · 원인 태그(`설계` / `조종` / `우리 코드` / `게임`). 오른쪽 위에 원인 태그별 개수 작은 막대.
- 사진 없음(밀도 우선).

### 10 `time` — 실제 3일, 게임 속 2년 273일 (신규)
- 3초 메시지: **"3일 동안 게임 시간 2년 넘게 — Jool은 3년 더"**.
- 레이아웃: 가로 축 = 게임 시간(Kerbin 일, 0 → 2,450). 위쪽 스트라이프 3개 = 실제 날짜(day 1: #1–#20, day 2: #21–#34,
  day 3: #35–#44, `career_launches[].date`로 계산). 축 위 마커 = `ut_anchors.past`; 축 오른쪽 점선 구간 =
  `ut_anchors.future`(Ike 창, Duna 1 도착, Eve 1 출발, Jool 도착). 라벨은 `label_ko`.
- 환산: 1일 = 21,600 s, 1년 = 426일(`kspbot/flight.py`와 같은 상수). "2y 273d"는 `career_now.ut`에서 계산.

(선택) 00 `cover` 1200×675: 02의 태양계 도식 + 헤드라인 "Claude가 KSP 커리어를 혼자 플레이하면". X 링크 미리보기용.
시간이 남을 때만.

---

## 3. 옛 카드와의 관계
- `docs/media/summary/0N-*` 5장은 그대로 둔다(첫날 기록). `tools/summary/img1–5.py`는 손대지 않는다
  (img1·img3는 지금 career.json으로는 KeyError — README에 "day-1 스냅샷, 재생성 불가" 한 줄 적는다).
- 새 세트: `docs/media/summary/v2/NN-slug.html|png`, 스크립트 `tools/summary/v2/`.

---

## 4. career.json에 먼저 넣을 데이터 (값과 출처)

모두 `docs/record/career.json`에 추가/교체. 출처는 `LOG.md` 줄 번호(L), `docs/writeup.ko.md`(W §).

### 4.1 `career_now` 교체
```
funds 2190000 (L596, Rescue 6 회수 후; Jool 1 발사비 83.6k 차감 전 — note에 적음)
funds_peak 2840000 (L300)   funds_start 25000
science 330 (L578, Jool 연구 후)   reputation 438 (L574)
ut 24293116 (Jool 1 창 UT, L576 — 실제 UT는 이보다 조금 뒤; 카드에는 "≥"/"~")   real_days 3   date "2026-09-26"
facilities {VAB 2, LaunchPad 2, MissionControl 2, TrackingStation 2, AstronautComplex 2, "R&D": 3} (L431)
funds_timeline (tick, funds, label, facility?):
  start 25000 "25k" · #1 110000 · #2 136000 · #4 212000 "212k" · facility(TS2+Pad2) 13700 "13.7k" (L12) ·
  #5 121800 · #10 385300 "385k" (L22) · facility(VAB2, −225k) (L24, 잔액 미기록 → 점 없이 마커만) ·
  #16 342800 (L34) · #18 609000 "609k" (L41) · facility(AC2) 마커만 (L43) · #20 1300000 "1.30M" (L54) ·
  facility(R&D2, −451k) 849000 "849k" (L55) · #22 913000 (L81) · #24 965000 (L112) · #25 1308000 "1.31M" (L123) ·
  #27 1720000 (L135) · #29 1700000 (L144) · #30 2030000 "2.03M" (L180) · #32 2360000 (L199) · #35 2520000 (L274) ·
  #36 2840000 "2.84M" (L300) · facility(R&D3, −1.69M) 1260000 "1.26M" (L431) · #40 1440000 (L449) ·
  #42 1810000 (L506) · #43 2190000 "2.19M" (L573)
science_by_body, funds_timeline_facility_markers, science_earned_total: 삭제 (재현 불가·낡음)
```

### 4.2 `career_launches[]`에 `date` 추가
`#1–#20: "2026-09-24"` (L5 절), `#21–#34: "2026-09-25"` (L78–L226), `#35–#44: "2026-09-26"` (L244–).
`#30` `result` `"in progress"` 유지(귀환 중), `#37` `"in progress"`, `#44` `"en route"`.
`#13`의 `craft` "Minmus Lander 1 (Mun orbit try)"는 그대로 두고 카드에서는 `slug` 기반 짧은 이름을 쓴다.

### 4.3 `firsts` 를 구조화 (문자열 배열 → 객체 배열; 옛 문자열은 `firsts_legacy`로 보존)
```
{n 4,  body kerbin, kind orbit,   who "",        label_ko "첫 궤도"}                      (L11)
{n 5,  body minmus, kind flyby,   who Jeb,       label_ko "첫 달 근접 통과"}              (L14)
{n 10, body minmus, kind landing, who Bill,      label_ko "첫 유인 Minmus 착륙·귀환"}     (L22)
{n 16, body mun,    kind landing, who Bob,       label_ko "첫 유인 Mun 착륙·귀환"}        (L34)
{n 22, body minmus, kind biomes,  who Jeb,       label_ko "Minmus 지표 바이옴 전부"}      (L81)
{n 24, body mun,    kind rendezvous, who "",     label_ko "첫 랑데부·Klaw·궤도 급유"}     (L105–112)
{n 27, body kerbin-orbit, kind relay, who "",    label_ko "첫 중계위성"}                  (L135)
{n 30, body duna,   kind landing, who Valentina, label_ko "첫 행성 착륙"}                 (W §7.8)
{n 31, body kerbin-orbit, kind keo, who "",      label_ko "첫 동기궤도"}                  (L178–)
{n 35, body kerbin-orbit, kind rescue, who Gwenbro, label_ko "첫 구조"}                  (L274; L437: 실제 귀환은 #40)
{n 37, body eve,    kind orbit,   who Jeb,       label_ko "첫 Eve 궤도 · 브로큰플레인 전이"} (W §7.11)
{n 39, body minmus, kind moon-to-moon, who Bob,  label_ko "첫 달→달 전이"}                (W §7.13)
{n 41, body minmus-orbit, kind station, who "Bob, Gwenbro", label_ko "첫 우주정거장"}    (W §7.15)
{n 44, body jool,   kind probe,   who "",        label_ko "첫 행성간 탐사선 · 핵엔진"}    (L576)
```

### 4.4 `ut_anchors` (카드 10)
```
past:   {ut 0, n 1, label_ko "첫 발사"} · {ut 2925382, n 23, label_ko "Bob 귀환(급유 구조)"} (L112) ·
        {ut 4165147, n 29, label_ko "Salvage 2 귀환"} (L144) · {ut 5108742, n 30, label_ko "Duna 1 출발"} (L76) ·
        {ut 11823553, n 37, label_ko "Eve 1 출발"} (L330) · {ut 22850000, n 41, label_ko "정거장 첫 전송"} (L510) ·
        {ut 22895340, n 30, label_ko "Duna 1 이륙"} (L176) · {ut 23456000, n 43, label_ko "Rescue 6"} (L571) ·
        {ut 24293116, n 44, label_ko "Jool 1 출발"} (L576)
future: {ut 25054465, label_ko "Ike 정거장 창"} (L514) · {ut 26854269, label_ko "Duna 1 중간 보정"} (L602) ·
        {ut 29029189, label_ko "Eve 1 출발"} (L455) · {ut 29273095, label_ko "Duna 1 Kerbin 도착"} (L544) ·
        {ut 52787080, label_ko "Jool 도착"} (L592)
```

### 4.5 `research` 보완 + `research_names`
`research`에 빠진 노드 추가: `precisionEngineering`, `advFuelSystems`, `nuclearPropulsion` (L124), `advFlightControl`
(L141), `aviation`, `automation` (L577) → 36개. `research_names`: id → 표시명(옛 04의 영어 표기 그대로; 새 노드는
`Precision Engineering`, `Adv. Fuel Systems`, `Nuclear Propulsion`, `Adv. Flight Control`, `Aviation`, `Automation` 등
KSP 트리 이름). 아이콘은 옛 img4의 매핑을 확장(없으면 `gyro`).

### 4.6 `landings_by_body` (착륙 **미션** 수, 터치다운 수 아님)
`{minmus: [10, 18, 20, 22, 25, 38], mun: [16, 23], duna: [30]}` (career_launches note).

### 4.7 `crafts[]` (카드 06)
```
hopper-1        {name "Hopper 1", first_n 1}                                           (부품·질량 기록 없음)
orbiter-1       {name "Orbiter 1", first_n 4}
minmus-lander-1 {name "Minmus Lander 1", first_n 10, parts 30, funds 12800}           (L17)
mun-lander-3    {name "Mun Lander 3", first_n 16, parts 43, mass_t 93}                (L34)
duna-1          {name "Duna 1", first_n 30, parts 42, mass_t 84.8, funds 42900}       (W §7.8)
jool-1          {name "Jool 1", first_n 44, parts 46, mass_t 87.1, funds 83600}       (L579)
(참고용, 카드에는 안 씀) eve-1 40부품 84.6 t 44.5k (W §7.11) · minmus-science-1 52부품 30.3k (L115) ·
minmus-science-2 85.9 t 56.5k (W §7.12) · ike-station-1 134 t 72k, 미발사 (W §7.17)
```

### 4.8 `how` (카드 03)
`commands: ["ascent --alt 80000","circularize","transfer Minmus --pe 15000","soi","capture","land","science","liftoff","return","reentry"]`,
`stack: ["Claude Code (WSL)","uv run ksp <phase>","kRPC 0.6.0 + KspBot mod (C#)","KSP 1.12.5"]`,
`rules_ko: ["오토파일럿 모드 없음","비행 코드 직접 작성","Normal 난이도, 전부 정상 결제","revert는 게임이 허용하는 만큼"]` (CLAUDE.md).

### 4.9 `incidents[]` (카드 09; `bugs_found_and_fixed_fun`은 그대로 두고 별도 배열)
```
{n 6,  cause design, text_ko "SRB 추력축 0.4° 틀어져 발사 1초부터 회전"}            (L17)
{n 8,  cause code,   text_ko "착륙 15 m/s, 넘어짐 (피드포워드 없음)"}                (L19)
{n 9,  cause design, text_ko "발사대 t=0 분해 ×2, #13에서 ×4 (측면 autostrut)"}       (career.json note)
{n 11, cause pilot,  text_ko "밸러스트로 피치오버 흉내 → 최대 동압에서 뒤집힘", hidden true} (W §7)
{n 17, cause code,   text_ko "Minmus를 겨눴는데 Mun에 포획"}                          (note)
{n 19, cause game,   text_ko "Minmus 지표 EVA, Jeb이 1,400 m/s로 튕김"}              (note)
{n 23, cause pilot,  text_ko "호핑에 1,434 m/s — Bob 고립, 급유선으로 구조"}          (W §7.5)
{n 28, cause code,   text_ko "Klaw 5번 튕김: .craft에 MODULE 노드 없음 (NRE)"}        (W §7.10)
{n 30, cause code,   text_ko "Duna 도착 v_inf 1,364 — 평균 반지름으로 계산"}           (W §7.8)
{n 30, cause code,   text_ko "28 km에서 착륙 스크립트 사망 → 비상 동력 착륙", hidden true} (W §7.8)
{n 32, cause code,   text_ko "match-orbit이 궤도를 역행으로 뒤집음 (1,602 m/s)"}       (W §7.9)
{n 41, cause game,   text_ko "실험실에서 나온 커발이 87 t 로켓을 넘어뜨림", hidden true} (note)
{n 42, cause code,   text_ko "저장 NRE로 엉뚱한 계약(Ike 정거장) 수락", hidden true}    (W §7.16–7.17)
{n 44, cause code,   text_ko "탈출 분사 601 m/s 부족 — 첫 단으로만 시간 계산"}          (L584)
```
카드에는 `hidden`이 아닌 10개만.

### 4.10 `kerbals` 교체
```
deaths_that_stood (유지, 3)  deaths_undone_by_revert (유지) + deaths_undone_by_revert_count 11 (1 + 4 + 6)
roster[]: {name, trait, status_ko, flights[], deaths_stood[], deaths_reverted[], first_n?}
  Jebediah  Pilot     "Eve 궤도 대기"          flights [5,6,11,18,19,20,21,22,25,28,29,37] deaths_stood [6,11] reverted [13,13]
  Valentina Pilot     "Duna → Kerbin 귀환 중"  flights [30] reverted [13]  first_n 30
  Bob       Scientist "Minmus Lab 1"           flights [16,23,38,39,41] reverted [13,41,41,41] first_n 16
  Bill      Engineer  "KSC"                    flights [7,8,10,12] deaths_stood [12] reverted [8] first_n 10
rescued[]: {name, trait, n}: Gwenbro Scientist 40 (#35에서 "구조" 뒤 L437: 아직 궤도, #40에서 귀환) · Mitbro Pilot 36 ·
  Daphrick Scientist 40 · Jedgard Pilot 40 · Elfry Engineer 43 · Barzor (trait 미기록 → "") 43           (L450, L574)
lost_contract: Beafrod (#26, 계약 소실)
```
직종 출처 L450·L574. Barzor의 직종은 기록에 없다 — **지어내지 말고 빈칸**.

### 4.11 `live_missions[]`, `science_hauls[]`, `science_aboard[]`
```
live_missions:
{slug jool-1, n 44, type probe, crew [], where_ko "Jool로 이동 중", next_ko "Jool 도착", next_ut 52787080, dv_left 4540}   (L592)
{slug duna-1, n 30, type crewed, crew [Valentina], where_ko "Duna → Kerbin", next_ko "Kerbin 도착", next_ut 29273095, sci_aboard 378} (L602)
{slug eve-1, n 37, type crewed, crew [Jeb], where_ko "Eve 궤도 142×40,000 km", next_ko "귀환 출발", next_ut 29029189, sci_aboard 1017} (L603)
{slug minmus-lab-1, n 41, type station, crew [Bob, Gwenbro], where_ko "Minmus 극궤도 14 km", next_ko "실험실 방문", sci_per_day 9.3} (L604)
{slug polar-relay-1, type satellite} {slug keo-relay-1, type satellite} {slug keo-relay-2, type satellite} {slug keo-relay-3, type satellite}
{slug ike-station-1, type built, where_ko "발사 대기", next_ut 25054465}                                                  (L606)
science_hauls: {n 25, gain 565, how "회수"} (L123) · {n 38, 1166, "회수"} (L390) · {n 39, 1601, "회수"} (L430) ·
  {n 41, 143, "전송"} (L490) · {n 41, 498, "실험실 전송"} (L510) · {n 41, 273, "실험실 전송"} (L571)
science_aboard: {slug eve-1, sci 1017, approx true} · {slug duna-1, sci 378, approx true} · {slug minmus-lab-1, data "730/750"}
```

---

## 5. 구현 지침 (opus)

### 5.1 구조
- `tools/summary/v2/common2.py`: `sys.path`로 `../common.py`를 임포트해 `ICONS, BASE_CSS, HEAD, page, icon, stars, planet,
  fmt_funds, write` 재사용. 확장:
  - `HEAD`의 Google Fonts 링크에 `Noto+Sans+KR:wght@500;700` 추가, `body{font-family:'Space Grotesk','Noto Sans KR',…}`
    (한글만 폴백으로 떨어진다). `word-break:keep-all`.
  - `planet()`에 `eve`(보라 `#b487d6/#5b2c83/#24102f`), `jool`(초록 줄무늬 `#a8d97a/#4f8a3a/#1e3d17`), `ike`(회색, 작게),
    `kerbol` 추가. 궤도선 도우미 `orbit_ring(r)`.
  - `RESULT_CODE = {success: ok, reverted: rev, "crew lost": dead, failed: fail, partial: fail, "in progress": live, "en route": live}`
    + 색: fail `#8e98b6`, live `#56c8ff`. `legend()`에 `Failed`, `In flight` 추가.
  - `OUT = docs/media/summary/v2/`, `page(..., total=10)`.
  - `ut_to_days(ut)`, `fmt_ydays(days) -> "2y 273d"`(426일/년).
- 카드 스크립트 `tools/summary/v2/card01_scoreboard.py` … `card10_time.py`. 모두 `RECORD`만 읽는다. 스크립트에 숫자·이름
  리터럴이 있으면 안 된다(예외: 레이아웃 치수, 색, 폰트 크기).
- `tools/summary/v2/build.py`: 카드 10개 생성 후 §5.2 렌더 명령을 순서대로 실행, 끝에 PNG 크기(2160×2700)를 확인.
- 이미지: `docs/media/summary/v2/img/`에 §5.3 크롭 결과(jpg). 옛 `crafts/`, `crew/`는 상대 경로로 참조(`../crafts/x.jpg`).

### 5.2 렌더
```
google-chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1080,1350 --virtual-time-budget=8000 --screenshot=OUT.png file://ABS.html
```
(카드 00 cover만 `--window-size=1200,675`). 폰트는 네트워크에서 온다: 오프라인이면 글자가 사라지므로 렌더 뒤 PNG를
Read로 열어 눈으로 확인한다.

### 5.3 사진 크롭 표 (`tools/summary/crop.py` 사용, 새 파일은 `v2/img/`; 좌표는 1280×720 원본 기준, 세로 썸네일은 480×689 비율)
| 용도 | 원본 | 크롭 |
|---|---|---|
| jool-1 (카드 02·05·06) | `2026-09-26_jool-1_pad.png` | HUD 제외: x 560–720, y 80–480 |
| ike-station-1 | `2026-09-26_ike-station-1_pad.png` | x 560–720, y 150–500 |
| eve-1 | `2026-09-26_eve-1_eve-pass.png` | 기체 + Eve 원반: x 400–880, y 0–690 |
| minmus-lab-1 | `2026-09-26_minmus-lab-1_orbit.png` | x 440–840, y 150–560 |
| minmus-science-1 | `2026-09-25_minmus-science-1_midlands.png` | x 420–840, y 120–600 |
| polar-relay-1 | `2026-09-25_polar-relay-1.png` | x 440–840, y 150–560 |
| keo-relay-1/2/3 (같은 설계) | `2026-09-25_keo-relay-1.png` | x 340–880, y 240–520 |
| rescue-1 | `2026-09-25_rescue-1_approach.png` | 기체 중심 |
| rescue-3, rescue-5, rescue-6 (같은 Klaw 포드 계열) | `2026-09-26_rescue-3_grabbed.png` | x 520–760, y 180–640 |
| rescue-4 | `2026-09-26_rescue-4_mitbro.png` | x 360–860, y 250–520 |
| mun-lander-7 (#21–23) | 옛 `crafts/mun-lander-7.jpg` | 그대로 |
| 사진 없음 → 자리표시자 | mun-tanker-1, rescue-2, salvage-1, salvage-2, minmus-science-2, survey-1 | 패널 배경 + `rocket` 아이콘 + 기체명, 흐린 점선 테두리 |
자리표시자 기체는 README의 "다음에 찍을 발사대 사진" 목록에 적는다(메인 세션이 나중에 `shoot_crafts.py`로 찍음).

### 5.4 수용 기준 (fable 검수 항목)
1. 10장 모두 2160×2700 PNG, HTML과 함께 `docs/media/summary/v2/`에 있음. `python tools/summary/v2/build.py` 한 번으로 재생성.
2. 글자 잘림·겹침 없음(카드마다 가장 긴 문자열로 확인), 헤드라인 18자 이내, 한글이 네모(tofu)로 나오지 않음.
3. 폰에서 읽힘: 본문 최소 17px(@1x), 숫자 강조 ≥ 40px, 한 카드에 글자 덩어리 ≤ 60개.
4. **지어낸 사실 없음**: 카드의 모든 숫자·이름은 career.json 키에서 오고, career.json의 새 값은 §4의 출처와 일치.
   기록에 없는 값(Hopper 부품 수, Barzor 직종, 총 획득 과학)은 빈칸. `approx`가 붙는 값과 현재 UT는 카드에도 `~`.
5. 스크립트에 번호별 하드코딩(`DETAIL[13] = …` 류) 없음 — 규칙 기반 렌더링.
6. README 갱신: v2 절(재생성 명령, 데이터 갱신 규칙 = 미션 끝날 때 career.json의 `career_launches`, `career_now`,
   `firsts`, `live_missions`, `ut_anchors`, `science_hauls`, `kerbals.roster/rescued` 갱신), 옛 세트는 day-1 스냅샷 표기,
   찍어야 할 발사대 사진 목록.
7. 게임에 손댄 흔적 없음(`runs/` 새 파일 없음, KSP 재시작 없음).

### 5.5 작업 순서 제안
career.json 갱신(§4) → common2 + card01(스코어보드, 옛 img1을 바탕으로) → 렌더해서 폰트·한글 확인 → 나머지 카드 →
build.py → README → fable 검수.
