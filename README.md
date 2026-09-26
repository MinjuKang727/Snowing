# 🌸 LiveBg (Desktop Seasons Widget)
> 지친 일상 속 데스크톱에 작은 힐링을 더해주는 **가벼운 파이썬 기반 사계절 라이브 배경화면 위젯**입니다.  
> 시스템 리소스를 최소화하면서도 부드러운 애니메이션을 제공하도록 설계되었습니다.  

<br><br>

## 💡 개발 동기
블로그 포스팅용 트리 만들기를 진행하면서 컴퓨터 화면 최상단에 항상 위치하는 위젯 구현에 관심을 갖게 되었습니다.  
구글 Gemini를 통해 파이썬으로 관련 기능을 구현할 수 있음을 알게 된 후,  
"컴퓨터 화면에 직접 눈이 오게 만들 수 있을까?" 하는 호기심에서 이번 프로젝트를 시작하게 되었습니다.  
이후 개발이 거듭되어 눈만 내리는 배경화면 위젯 `Snowing.exe`를  
여러 테마를 선택할 수 있는 라이브 배경화면으로 업그레이드하였습니다.

<br><br>

## ✨ Key Features (주요 기능)

* **6가지 감성 테마 지원**
  * 🌸 **봄**: 부드럽게 흩날리는 벚꽃 잎사귀
  * 🌿 **여름**: 싱그러운 초록 잎사귀와 자연스러운 바람결
  * ✨ **반딧불이**: 신비로운 밤숲 속 오비탈 웨이브 곡선 유영 및 점멸 효과
  * 🍁 **가을**: 낭만적인 단풍잎 낙하
  * ❄️ **겨울**: 은은하게 내리는 눈송이
  * 🌧️ **비**: 차분한 빗방울과 바닥 물결 파문 효과
* **항상 위 오버레이 (Always on Top)**
  * 다른 창이나 폴더를 띄워도 애니메이션이 뒤로 숨지 않고 항상 최상단에서 부드럽게 유지
* **시스템 트레이 지원**
  * 작업표시줄 트레이 아이콘 호버 시 프로그램 이름("LiveBg") 툴팁 제공
  * `QSharedMemory`를 활용한 중복 실행 방지

### 📺 시연 영상

<img width="1280" height="720" alt="VibeCoding-PythonLiveBg--ezgif com-video-to-gif-converter" src="https://github.com/user-attachments/assets/d97d8819-c656-40e8-b396-38f52bfd673d" />

<br><Br>

## 🛠️ Tech Stack (기술 스택)

* **Language**: Python 3.x
* **GUI Framework**: PyQt5 (`QPainter`, `QTimer`, `QWidget`, `QSystemTrayIcon`)
* **Packaging**: PyInstaller

<br><Br>

## 최신 버전 다운로드(사용자용)
👉 [최신 버전 다운로드 링크](https://github.com/MinjuKang727/Snowing/releases)

<br><br>
## 🚀 Getting Started & Installation (설치 및 실행)
1. **저장소 클론 및 이동**
   ```bash
   git clone [https://github.com/MinjuKang727/Snowing.git](https://github.com/MinjuKang727/Snowing.git)
   cd Snowing
   ```
2. **필수 라이브러리 설치**
   ```bash
   pip install -r requirements.txt
   ```
3. **프로그램 실행**
   ```bash
   python livebg.py
   ```

<br><Br>

## 📦 Building Executable (배포하기, .exe)
> PyInstaller를 이용해 단일 실행 파일로 빌드할 수 있습니다:

- onefile 배포
```Bash
pyinstaller --clean --noconsole --onefile --icon=livebg2.ico livebg.py
```

- onedir 배포
```Bash
pyinstaller --clean --noconsole --onedir --icon=livebg2.ico livebg.py
```

<br><Br>

## 📄 License
> This project is licensed under the [MIT License](https://github.com/MinjuKang727/Snowing/blob/79cf9c656a30301c8c49ed851d2fb41095f623a7/LICENSE).

<br><Br>

## 개발 버전 별 업그레이드 요약
<table style="border:none;">
  <tr>
    <td style="text-align:center; font-weight: bold;"> v1.0.0: 동그란 눈송이</td>
    <td style="text-align:center; font-weight: bold;"> v2.0.0: 섬세한 눈 결정</td>
    <td style="text-align:center; font-weight: bold;"> v2.1.0: 눈 결정 크기 축소</td>
    <td style="text-align:center; font-weight: bold;"> v2.2.0: 눈 결정 크기 더 축소</td>
  </tr>
  <tr>
    <td><img width="1917" height="1105" alt="image" src="https://github.com/user-attachments/assets/b0992250-acf0-4d9c-82de-f91619205a7f" />
</td>
    <td><img width="1917" height="1103" alt="image" src="https://github.com/user-attachments/assets/ed787129-3814-4cf8-b6b4-b21c5a7bcba9" />
</td>
    <td><img width="1917" height="1105" alt="image" src="https://github.com/user-attachments/assets/483a51af-e47e-4b6d-8962-1bfb1f938baa" />
</td>
    <td><img width="1917" height="1103" alt="image" src="https://github.com/user-attachments/assets/3b2f1e73-1987-4051-baa8-a2726e661292" />
</td>
  </tr>
</table>

- **v2.3.0**: 마우스 반경 눈송이 퍼뜨리기
- **v2.4.0**: 마우스 반경 눈송이 녹이기(페이드 아웃)
- **v2.5.0**: 중복 실행 방지 기능 추가
- **v3.0.0**: `Snowing.exe` 업그레이드 -> `LiveBg.exe` (6가지 테마의 라이브 배경화면)
- **v3.1.0**
  - 기본 테마 변경: 겨울 -> 봄
  - 시스템 트레이 UX 개선: 아이콘 `LiveBg` 툴팁 추가
  - 오버레이 레이어 안정성 확보: 사용 중 배경화면이 최상단에서 내려오던 버그 개선
