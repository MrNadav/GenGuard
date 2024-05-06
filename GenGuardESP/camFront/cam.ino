#include "esp_camera.h"
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include <WebSocketsServer.h> // Include WebSocket Server
#include <FirebaseESP32.h>

#define FIREBASE_HOST ""
#define FIREBASE_AUTH ""
FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

const char* ssid = "";
const char* password = "";

#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22
#define ledpin 4

AsyncWebServer server(80);
WebSocketsServer webSocket = WebSocketsServer(81); // WebSocket Server on port 81

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
  AwsFrameInfo *info = (AwsFrameInfo*)arg;
  if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
    data[len] = 0;
    Serial.printf("%s\n", data);
  }
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.printf("[%u] Disconnected!\n", num);
            break;
        case WStype_CONNECTED:
            {
                IPAddress ip = webSocket.remoteIP(num);
                Serial.printf("[%u] Connection from %d.%d.%d.%d\n", num, ip[0], ip[1], ip[2], ip[3]);
            }
            break;
        case WStype_TEXT:
            Serial.printf("[%u] Text: %s\n", num, payload);
            // Handle text messages from client
            break;
        case WStype_BIN:
            // Handle binary messages from client
            Serial.printf("[%u] Binary message received\n", num);
            break;
    }
}


void startCameraServer() {
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send(200, "text/plain", "ESP32-CAM WebSocket Server");
    });

    server.on("/toggle-led", HTTP_GET, [](AsyncWebServerRequest *request) {
        digitalWrite(ledpin, !digitalRead(ledpin)); // Toggle LED state
        request->send(200, "text/plain", "LED Toggled");
    });

    server.begin();
    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
}

void setup() {
    Serial.begin(115200);
    pinMode(ledpin, OUTPUT);
    digitalWrite(ledpin, LOW);

      camera_config_t camera_config = {
        .pin_pwdn = PWDN_GPIO_NUM,
        .pin_reset = RESET_GPIO_NUM,
        .pin_xclk = XCLK_GPIO_NUM,
        .pin_sscb_sda = SIOD_GPIO_NUM,
        .pin_sscb_scl = SIOC_GPIO_NUM,
        .pin_d7 = Y9_GPIO_NUM,
        .pin_d6 = Y8_GPIO_NUM,
        .pin_d5 = Y7_GPIO_NUM,
        .pin_d4 = Y6_GPIO_NUM,
        .pin_d3 = Y5_GPIO_NUM,
        .pin_d2 = Y4_GPIO_NUM,
        .pin_d1 = Y3_GPIO_NUM,
        .pin_d0 = Y2_GPIO_NUM,
        .pin_vsync = VSYNC_GPIO_NUM,
        .pin_href = HREF_GPIO_NUM,
        .pin_pclk = PCLK_GPIO_NUM,
        .xclk_freq_hz = 20000000,
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = FRAMESIZE_SVGA,
        .jpeg_quality = 12,
        .fb_count = 1
    };

    // Initialize the camera
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x", err);
        return;
    }

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.print("WiFi connected. IP address: ");
    Serial.println(WiFi.localIP());

    firebaseInit();
    startCameraServer();
}

void loop() {
  
    webSocket.loop();

    static unsigned long lastFrameTime = 0;
    if (millis() - lastFrameTime > 100) { // Aim to send frames every 100 ms
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            return;
        }

        // Broadcast the frame to all connected WebSocket clients
        webSocket.broadcastBIN(fb->buf, fb->len);
        esp_camera_fb_return(fb); // Release the frame buffer to be used again
        lastFrameTime = millis();
    }
}


void firebaseInit() {
    config.host = FIREBASE_HOST;
    config.api_key = FIREBASE_AUTH;
    auth.user.email = "@gmail.com";
    auth.user.password = "";

    Firebase.begin(&config, &auth);
    Firebase.reconnectWiFi(true);

    String CAMIP = "http://"+ WiFi.localIP().toString();
    if (Firebase.setString(firebaseData, "/esp/CAMIP", CAMIP)) {
        Serial.println("Stored IP Address in Firebase successfully");
    } else {
        Serial.println("Failed to store IP Address in Firebase");
        Serial.println("REASON: " + firebaseData.errorReason());
    }
}
