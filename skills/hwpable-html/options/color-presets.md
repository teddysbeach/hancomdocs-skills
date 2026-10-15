# 테이블 컬러 프리셋

스킬 실행 시 유저에게 아래 프리셋 중 하나를 선택하게 한다. 선택된 프리셋의 값을 `templates/base.html`의 플레이스홀더에 대입한다.

## 플레이스홀더 매핑

| 플레이스홀더 | 용도 |
|-------------|------|
| `{{TH_BG}}` | th 배경색 |
| `{{TH_COLOR}}` | th 글자색 |
| `{{TD_BG}}` | td 배경색 |
| `{{BORDER_COLOR}}` | 테두리색 |

## 프리셋 목록

### 1. 기본 (회색) — 기본값
```
TH_BG: #EEEEEE
TH_COLOR: #000000
TD_BG: #FFFFFF
BORDER_COLOR: black
```

### 2. 블루
```
TH_BG: #D6E4F0
TH_COLOR: #000000
TD_BG: #F5F9FF
BORDER_COLOR: #4472C4
```

### 3. 네이비
```
TH_BG: #2B3A67
TH_COLOR: #FFFFFF
TD_BG: #F0F2F8
BORDER_COLOR: #2B3A67
```

### 4. 그린
```
TH_BG: #D9E8D0
TH_COLOR: #000000
TD_BG: #F5FAF2
BORDER_COLOR: #548235
```

### 5. 다크
```
TH_BG: #333333
TH_COLOR: #FFFFFF
TD_BG: #F9F9F9
BORDER_COLOR: #333333
```

### 6. 커스텀
유저가 직접 HEX 코드를 제공하면 그대로 적용한다.
