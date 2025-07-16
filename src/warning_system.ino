// warning_system.ino

const int ledPin = 8;     // LED가 연결될 핀 번호
const int buzzerPin = 9;  // 부저가 연결될 핀 번호

void setup() {
  Serial.begin(9600);     // 라즈베리파이와 통신 시작
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
}

void loop() {
  // 시리얼 통신으로 데이터가 들어왔는지 확인
  if (Serial.available() > 0) {
    char signal = Serial.read();

    // 만약 들어온 신호가 'G'이면 (Gorani)
    if (signal == 'G') {
      trigger_warning();
    }
  }
}

// 경고를 울리는 함수
void trigger_warning() {
  // 0.5초 동안 LED와 부저를 켰다가 끄는 것을 3번 반복
  for (int i = 0; i < 3; i++) {
    digitalWrite(ledPin, HIGH);
    tone(buzzerPin, 1000); // 1000Hz 소리 내기
    delay(500); // 0.5초 대기
    digitalWrite(ledPin, LOW);
    noTone(buzzerPin);
    delay(500);
  }
}