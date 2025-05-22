const int redPins[3] = {3, 6, 9};
const int greenPins[3] = {4, 7, 10};
const int bluePins[3] = {5, 8, 11};

const int sensorPins[3] = {A0, A1, A2};
const int buzzerPin = 12;

const int startStopSensorPin = A3; 
const int threshold = 700;

int currentTarget = -1;
bool gameRunning = false;

void setup() {
  for (int i = 0; i < 3; i++) {
    pinMode(redPins[i], OUTPUT);
    pinMode(greenPins[i], OUTPUT);
    pinMode(bluePins[i], OUTPUT);
  }
  pinMode(buzzerPin, OUTPUT);
  Serial.begin(9600);

  randomSeed(analogRead(startStopSensorPin));
  turnOffAll();
}

void loop() {
  int startStopVal = analogRead(startStopSensorPin);

  if (startStopVal < threshold) {
    delay(200); // debounce
    while (analogRead(startStopSensorPin) < threshold) {
      delay(50);
    }
    gameRunning = !gameRunning; 
  Serial.print("Start/Stop Değeri: ");
  Serial.println(startStopVal);


    if (gameRunning) {
      Serial.println("GAME START");
      selectNewTarget();
    } else {
      Serial.println("GAME STOP");
      turnOffAll();
    }
  }

  if (gameRunning) {
    
    setColor(currentTarget, LOW, HIGH, HIGH); 

    unsigned long startTime = millis();
    bool lazerGeldi = false;

    while (millis() - startTime < 5000) { 
      int val = analogRead(sensorPins[currentTarget]);

      if (val < threshold) {
        lazerGeldi = true;
        break;
      }
      delay(50);

      
      int stopVal = analogRead(startStopSensorPin);
      if (stopVal < threshold) {
        gameRunning = false;
        turnOffAll();
        Serial.println("GAME STOP");
        while (analogRead(startStopSensorPin) < threshold) {
          delay(50);
        }
        break;
      }
    }

    if (!gameRunning) return; 

    if (lazerGeldi) {
      Serial.println("HIT");
     
      setColor(currentTarget, HIGH, LOW, HIGH);
      tone(buzzerPin, 1000);
      delay(1000);
      noTone(buzzerPin);
    } else {
      Serial.println("MISS");
      
      setColor(currentTarget, HIGH, HIGH, LOW);
      delay(1000);
    }

    
    turnOff(currentTarget);

    
    selectNewTarget();
  } else {
    delay(100);
  }
}

void setColor(int target, int redState, int greenState, int blueState) {
  digitalWrite(redPins[target], redState);
  digitalWrite(greenPins[target], greenState);
  digitalWrite(bluePins[target], blueState);
}

void turnOff(int target) {
  digitalWrite(redPins[target], HIGH);
  digitalWrite(greenPins[target], HIGH);
  digitalWrite(bluePins[target], HIGH);
}

void turnOffAll() {
  for (int i = 0; i < 3; i++) {
    turnOff(i);
  }
}

void selectNewTarget() {
  int newTarget;
  do {
    newTarget = random(0, 3);
  } while (newTarget == currentTarget);
  currentTarget = newTarget;
}
