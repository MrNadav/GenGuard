#include <ESP32Servo.h>
#include <WiFi.h>
#include <WebServer.h>
#include <FirebaseESP32.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128  // OLED display width, in pixels
#define SCREEN_HEIGHT 32  // OLED display height, in pixels


#define FIREBASE_HOST ""  // Replace with your Firebase RTDB host
#define FIREBASE_AUTH ""               // Replace with your Firebase RTDB secret
FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

// Define your pins and other constants
#define BuzzerPin 23
#define RedLED 21
#define BlueLED 18
#define GreenLED 19
#define YellowLED 22
#define ServoPin1 12
#define ServoPin2 13
#define NOTE_CS2 554  // Approximate frequency for C#2 note
#define Solonoied 26

#define area1 15

const int touchThreshold = 40;
bool area1AlarmTriggered = false;
bool area2AlarmTriggered = false;
bool area3AlarmTriggered = false;
bool globalAlarmState = false;
unsigned long previousMillis = 0;
const long interval = 500;  // Interval at which to blink/change tone (milliseconds)


Servo servo1;
Servo servo2;
Servo servoX;
Servo servoY;


const char* ssid = "";          // Replace with your SSID
const char* password = "";  // Replace with your Password
unsigned long doorOpenedTime = 0;
bool doorOpened = false;

// Buzzer control variables
unsigned long previousToneMicros = 0;
long toneDuration = 1000000;  // Duration to play the tone in microseconds (1 second)
long toneInterval;            // Interval in microseconds to toggle the buzzer
bool isTonePlaying = false;   // Is the tone currently playing?
long toneFrequency = 554;
WebServer server(80);
String ESPIP = "";  // Variable to store camera IP

void setup() {
  Serial.begin(115200);
  pinMode(RedLED, OUTPUT);
  pinMode(YellowLED, OUTPUT);
  pinMode(GreenLED, OUTPUT);
  pinMode(BlueLED, OUTPUT);
  digitalWrite(BlueLED, HIGH);
  digitalWrite(RedLED, HIGH);
  digitalWrite(GreenLED, HIGH);
  digitalWrite(YellowLED, HIGH);
  pinMode(BuzzerPin, OUTPUT);
  pinMode(Solonoied, OUTPUT);
  // Initialize WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  ESPIP = "http://" + WiFi.localIP().toString();  // Example, replace with actual camera IP obtaining method
  firebaseInit();

  // Attach servos
  servo1.attach(ServoPin1);
  servo2.attach(ServoPin2);
  servoX.attach(33); // Pin number for servo X
  servoY.attach(32); // Pin number for servo Y
  servoX.write(90);
  servoY.write(90);
  servo1.write(180);
  servo2.write(0);
  digitalWrite(BlueLED, LOW);
  digitalWrite(RedLED, LOW);
  digitalWrite(GreenLED, LOW);
  digitalWrite(YellowLED, LOW);

  // Calculate the toggle interval for the specified frequency
  toneInterval = 1000000 / (2 * NOTE_CS2);


  server.on("/resetAlarm", HTTP_GET, []() {
    resetAlarm();
    server.send(200, "text/plain", "Alarm reset.");
  });

  server.on("/accessGranted", HTTP_GET, []() {
    turnOffAllLEDs();
    indicateAccessGranted();
    server.send(200, "text/plain", "Access Granted. Doors are open.");
    openDoors();  // Consider non-blocking implementation
    // Schedule to close doors after a delay
    doorOpenedTime = millis();
    doorOpened = true;
  });
  server.on("/idle", HTTP_GET, [&]() {
    turnOffAllLEDs();
    indicateIdle();
    server.send(200, "text/plain", "System is idle.");
  });

  server.on("/scanning", HTTP_GET, [&]() {
    turnOffAllLEDs();
    indicateScanning();
    server.send(200, "text/plain", "Scanning in progress.");
  });

  server.on("/accessDenied", HTTP_GET, [&]() {
    turnOffAllLEDs();
    indicateAccessDenied();
    server.send(200, "text/plain", "Access Denied.");
  });


  //test
  server.on("/moveLeft", HTTP_GET, []() {
        int currentX = servoX.read();
        for (int pos = currentX; pos >= max(0, currentX - 5); pos -= 1) {
            servoX.write(pos);
            delay(10);
        }
        server.send(200, "text/plain", "Moved Left");
    });

    server.on("/moveRight", HTTP_GET, []() {
        int currentX = servoX.read();
        for (int pos = currentX; pos <= min(180, currentX + 5); pos += 1) {
            servoX.write(pos);
            delay(10);
        }
        server.send(200, "text/plain", "Moved Right");
    });

    server.on("/moveUp", HTTP_GET, []() {
        int currentY = servoY.read();
        for (int pos = currentY; pos <= min(180, currentY + 5); pos += 1) {
            servoY.write(pos);
            delay(10);
        }
        server.send(200, "text/plain", "Moved Up");
    });

    server.on("/moveDown", HTTP_GET, []() {
        int currentY = servoY.read();
        for (int pos = currentY; pos >= max(0, currentY - 5); pos -= 1) {
            servoY.write(pos);
            delay(10);
        }
        server.send(200, "text/plain", "Moved Down");
    });

    server.on("/center", HTTP_GET, []() {
        servoX.write(90);
        servoY.write(90);
        server.send(200, "text/plain", "Centered");
    });

  //test


  server.begin();
}
// Global variable to track the last time Firebase was checked
unsigned long lastFirebaseCheck = 0;
const long firebaseCheckInterval = 2000; // Check every 2000 milliseconds (2 seconds)
bool alarmStateUpdated = false;

void loop() {

    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        int splitIndexX = command.indexOf("ServoX");
        int splitIndexY = command.indexOf("ServoY");
        
        if (splitIndexX != -1 && splitIndexY != -1) {
            int targetX = command.substring(splitIndexX + 6, splitIndexY).toInt();
            int targetY = command.substring(splitIndexY + 6).toInt();
            
            moveSmoothly(servoX, targetX);
            moveSmoothly(servoY, targetY);
        }
    }


  server.handleClient();  // Handle client requests

  // Handle the tone in a non-blocking manner
  handleTone();

  if (globalAlarmState) {
    blinkLEDsAndSoundBuzzer();

    // Periodically check Firebase for the alarm state, no need to set "True" here
    if (millis() - lastFirebaseCheck >= firebaseCheckInterval) {
      checkFirebaseAlarmState();
      lastFirebaseCheck = millis();
    }
  } else {
    // Non-blocking door close control
    if (doorOpened && millis() - doorOpenedTime > 3000) {
      Serial.println("Closing doors after delay");
      closeDoors();
      doorOpened = false;
    }
    
    // Check touch sensors if their alarm has not been triggered
    checkArea(area1, &area1AlarmTriggered, "ALARM 1");
    // checkArea(area2, &area2AlarmTriggered, "ALARM 2");
    // checkArea(area3, &area3AlarmTriggered, "ALARM 3");
  }

 if (millis() - lastFirebaseCheck >= firebaseCheckInterval) {
      checkstate();
      lastFirebaseCheck = millis();
    }


  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconnecting to WiFi...");
    WiFi.reconnect();
  }

  if (!Firebase.ready()) {
    Serial.println("Reconnecting to Firebase...");
    Firebase.begin(&config, &auth);
  }

}
void moveSmoothly(Servo &servo, int targetPos) {
    int startPos = servo.read(); // Current position of the servo
    int step = (startPos < targetPos) ? 1 : -1; // Determine the direction of movement

    for (int pos = startPos; pos != targetPos; pos += step) {
        servo.write(pos); // Move to next position
        delay(15); // Short delay to allow the servo to reach the position
    }
    servo.write(targetPos); // Ensure servo gets to final target position
}
void checkstate(){
    if (Firebase.getString(firebaseData, "/Alarm/alarmState")) {
    String alarmState = firebaseData.stringData();
    if (alarmState == "true") {
      closeDoors();
      globalAlarmState = true;
    } 
  } else {
    Serial.println("Failed to get AlarmState from Firebase");
    Serial.println("REASON: " + firebaseData.errorReason());
  }
}

void turnOffAllLEDs() {
  digitalWrite(RedLED, LOW);
  digitalWrite(BlueLED, LOW);
  digitalWrite(GreenLED, LOW);
  digitalWrite(YellowLED, LOW);
}

void indicateAccessDenied() {
  turnOffAllLEDs();
  digitalWrite(RedLED, HIGH);
  startTone(440, 500000);  // Start a 0.5-second tone at 440 Hz for Access Denied
}

void indicateAccessGranted() {
  turnOffAllLEDs();
  digitalWrite(GreenLED, HIGH);
  startTone(554, 1000000);  // Start a 1-second tone at 554 Hz for Access Granted
}

void indicateIdle() {
  turnOffAllLEDs();
  digitalWrite(BlueLED, HIGH);
}

void indicateScanning() {
  turnOffAllLEDs();
  digitalWrite(YellowLED, HIGH);
}

void openDoors() {
  Serial.println("Opening doors");
  // digitalWrite(Solonoied, HIGH);
  for(int i=0; i<=90 ; i++)
  {
    servo1.write(180 - i);
    servo2.write(i);
    delay(15);
  }
  // servo1.write(90);
  // servo2.write(90);
  // Consider implementing non-blocking incremental movement
}

void closeDoors() {
  Serial.println("Closing doors - Stepwise");
  servo1.write(178);
  servo2.write(5);
  // Consider implementing non-blocking incremental movement
  delay(500);
  // digitalWrite(Solonoied, LOW);
}


void startTone(int frequency, long duration) {
  toneFrequency = frequency;                     // Set the new frequency
  toneDuration = duration;                       // Set the new duration
  toneInterval = 1000000 / (2 * toneFrequency);  // Recalculate the interval
  previousToneMicros = micros();                 // Reset the tone timer
  isTonePlaying = true;
}

void handleTone() {
  if (isTonePlaying) {
    unsigned long currentMicros = micros();
    if (currentMicros - previousToneMicros < toneDuration) {
      if ((currentMicros - previousToneMicros) % toneInterval < (toneInterval / 2)) {
        digitalWrite(BuzzerPin, HIGH);
      } else {
        digitalWrite(BuzzerPin, LOW);
      }
    } else {
      digitalWrite(BuzzerPin, LOW);
      isTonePlaying = false;
    }
  }
}

void checkArea(int area, bool* alarmTriggered, const char* message) {
  if (touchRead(area) < 5 && !*alarmTriggered) {
    Serial.println(message);
    Serial.println(touchRead(area));
    *alarmTriggered = true;
    globalAlarmState = true;
    turnOffAllLEDs();
    closeDoors();
    updateFirebaseAlarmState("true", area);
  }
}
void updateFirebaseAlarmState(String state, int area) {
  // Update the general alarm state
  if (Firebase.setString(firebaseData, "/Alarm/alarmState", state)) {
    Serial.print("AlarmState updated in Firebase successfully: ");
    Serial.println(state);
  } else {
    Serial.println("Failed to update AlarmState in Firebase");
    Serial.println("REASON: " + firebaseData.errorReason());
    return; // Exit if failed to set alarm state
  }

  // Only update the area if the alarm is being set to True
  if (state == "true") {
    if (Firebase.setInt(firebaseData, "/Alarm/alarmZone", area)) {
      Serial.print("Alarm area updated in Firebase successfully: Area ");
      Serial.println(area);
      closeDoors();

    } else {
      Serial.println("Failed to update Alarm area in Firebase");
      Serial.println("REASON: " + firebaseData.errorReason());
    }
  }
}




void checkFirebaseAlarmState() {
  if (Firebase.getString(firebaseData, "/Alarm/alarmState")) {
    String alarmState = firebaseData.stringData();
    if (alarmState == "true") {
      globalAlarmState = true;
    } else if (alarmState == "false") {
      globalAlarmState = false;
      // Turn off the alarm immediately if Firebase indicates it's off
      resetAlarm();
    }
  } else {
    Serial.println("Failed to get AlarmState from Firebase");
    Serial.println("REASON: " + firebaseData.errorReason());
  }
}

void resetAlarm() {
  area1AlarmTriggered = false;
  area2AlarmTriggered = false;
  area3AlarmTriggered = false;
  globalAlarmState = false;
  noTone(BuzzerPin);  // Ensure the buzzer is turned off
  isTonePlaying = false;
  turnOffAllLEDs();
  updateFirebaseAlarmState("False", -1);
  closeDoors();  // Explicitly close doors to ensure they're in the correct state
  alarmStateUpdated = false; // Reset the flag to allow future updates

}

unsigned long lastAlarmToneMicros = 0;  // Variable to track the last time the alarm tone was played
const unsigned long alarmToneInterval = 500000; // Interval between alarm tones (500ms or 0.5 seconds)

void blinkLEDsAndSoundBuzzer() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // Toggle LEDs
    digitalWrite(RedLED, !digitalRead(RedLED));
    digitalWrite(BlueLED, !digitalRead(BlueLED));
    digitalWrite(GreenLED, !digitalRead(GreenLED));
    digitalWrite(YellowLED, !digitalRead(YellowLED));

    // Control buzzer based on the alarm state
    // if (globalAlarmState) {
    //   unsigned long currentMicros = micros();
    //   if (currentMicros - lastAlarmToneMicros >= alarmToneInterval) {
    //     tone(BuzzerPin, 5000, 100); // Play a 100ms tone at 5kHz
    //     lastAlarmToneMicros = currentMicros;
    //   }
    // } else if (isTonePlaying) {
    //   noTone(BuzzerPin);
    //   isTonePlaying = false;
    // }
  }
}

void firebaseInit() {
  config.host = FIREBASE_HOST;
  config.api_key = FIREBASE_AUTH;
  auth.user.email = "@gmail.com"; // Use your Firebase authentication email
  auth.user.password = ""; // Use your Firebase authentication password

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  // Optional: Store the ESP's IP address in Firebase for reference
  if (Firebase.setString(firebaseData, "/esp/ESPIP", ESPIP)) {
    Serial.println("Stored IP Address in Firebase successfully");
  } else {
    Serial.println("Failed to store IP Address in Firebase");
    Serial.println("REASON: " + firebaseData.errorReason());
  }

  // Initiate the stream from Firebase
  startFirebaseStream();
}


void startFirebaseStream() {
  if (Firebase.beginStream(firebaseData, "/Alarm/alarmState")) {
    Serial.println("Started stream with Firebase");
    Firebase.setStreamCallback(firebaseData, streamCallback, streamTimeoutCallback);
  } else {
    Serial.println("Failed to start stream. Reason: " + firebaseData.errorReason());
  }
}


void streamCallback(StreamData data) {
  String path = data.streamPath();
  String dataValue = data.stringData();

  Serial.println("Stream data received. Path: " + path + ", Value: " + dataValue);

  if (path == "/Alarm/alarmState") {
    if (dataValue == "true") {
      globalAlarmState = true;
      blinkLEDsAndSoundBuzzer(); // Activate the alarm
    } else {
      globalAlarmState = false;
      resetAlarm(); // Deactivate the alarm
    }
  }
}




void streamTimeoutCallback(bool timeout) {
  if (timeout) {
    Serial.println("Firebase stream timeout, attempting to reconnect...");
    startFirebaseStream();
  }
}


