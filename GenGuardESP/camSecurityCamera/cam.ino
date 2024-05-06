#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <FirebaseESP32.h>
#define FIREBASE_HOST ""  // Replace with your Firebase RTDB host
#define FIREBASE_AUTH ""  // Replace with your Firebase RTDB secret
FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

// Replace with your network credentials
const char* ssid = "";
const char* password = "";

// Camera Pin Configuration
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22
WebServer server(80);
String CAMIP = "";  // Variable to store camera IP
void startCameraServer() {
  server.on("/", HTTP_GET, []() {
    server.sendHeader("Location", "/stream");
    server.send(302, "text/plain", "");
  });
  server.on("/stream", HTTP_GET, []() {
    server.sendContent("HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");
    camera_fb_t * fb = NULL;
    while (true) {
      fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("Camera capture failed");
        return;
      }
      server.sendContent("--frame\r\nContent-Type: image/jpeg\r\n\r\n");
      server.sendContent_P((char *)fb->buf, fb->len);
      server.sendContent("\r\n");
      esp_camera_fb_return(fb);
      if (!server.client().connected()) {
        break;
      }
    }
  });
  server.begin();
}
void setup() {
  Serial.begin(115200);
  // Camera configuration
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 15000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA; //svga
  config.jpeg_quality = 15;
  config.fb_count = 4;
  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected. IP address: ");
  Serial.println(WiFi.localIP());
  CAMIP = "http://"+ WiFi.localIP().toString() + "/stream"; // Example, replace with actual camera IP obtaining method
  firebaseInit();
  // Start the server
  startCameraServer();
}
void loop() {
  server.handleClient();
}
void firebaseInit() 
  {
    config.host = FIREBASE_HOST;
    config.api_key = FIREBASE_AUTH;
    auth.user.email = "@gmail.com";
    auth.user.password = "";
    Firebase.begin(&config, &auth);
    Firebase.reconnectWiFi(true);
    // Here you set the camera's IP under the specified path
    if (Firebase.setString(firebaseData, "/esp/CAMIP", CAMIP)) {
      Serial.println("Stored IP Address in Firebase successfully");
    } else {
      Serial.println("Failed to store IP Address in Firebase");
      Serial.println("REASON: " + firebaseData.errorReason());
    }
  }