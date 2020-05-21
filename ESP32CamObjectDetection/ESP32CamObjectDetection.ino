/*
BSD 2-Clause License

Copyright (c) 2020, longpth
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include <WebSocketsServer.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "camera_wrap.h"

#define DEBUG
// #define SAVE_IMG

const char* ssid = "your_ssid"; //replace with your wifi ssid
const char* password = "your_password"; //replace with your wifi password
//holds the current upload
int cameraInitState = -1;
uint8_t* jpgBuff = new uint8_t[68123];
size_t   jpgLength = 0;
//Creating UDP Listener Object. 
WiFiUDP UDPServer;
unsigned int UDPPort = 6868;
IPAddress addrRemote;
int portRemote;

// Use WiFiClient class to create TCP connections
WiFiClient tcpClient;
bool clientConnected = false;

WebSocketsServer webSocket = WebSocketsServer(86);

const int RECVLENGTH = 8;
byte packetBuffer[RECVLENGTH];

unsigned long previousMillis = 0;
unsigned long previousMillisServo = 0;
const unsigned long interval = 30;
const unsigned long intervalServo = 100;

bool bStream = false;
int debugCnt=0;

bool reqLeft = false;
bool reqRight = false;
bool reqFw = false;
bool reqBw = false;

const int PIN_SERVO_YAW   = 12;
const int PIN_SERVO_PITCH = 2;
const int LED_BUILTIN = 4;
const int SERVO_RESOLUTION    = 16;
int ledState = LOW;

int posYaw = 90;
int posPitch = 30;
int delta = 1;
const int angleMax = 180;
uint8_t camNo = 0;

void processData(){
  int cb = UDPServer.parsePacket();
  if (cb) {
    UDPServer.read(packetBuffer, RECVLENGTH);
    addrRemote = UDPServer.remoteIP();
    portRemote = UDPServer.remotePort();

    String strPackage = String((const char*)packetBuffer);
#ifdef DEBUG
    Serial.print("receive: ");
    // for (int y = 0; y < RECVLENGTH; y++){
    //   Serial.print(packetBuffer[y]);
    //   Serial.print("\n");
    // }
    Serial.print(strPackage);
    Serial.print(" from: ");
    Serial.println(addrRemote);
#endif
    if(strPackage.equals("whoami")){
      UDPServer.beginPacket(addrRemote, portRemote);
      String res = "ESP32-CAM";
      UDPServer.write((const uint8_t*)res.c_str(),res.length());
      UDPServer.endPacket();
      Serial.println("response");
    }else if(strPackage.equals("fwon")){
      reqFw = true;
    }else if(strPackage.equals("bwon")){
      reqBw = true;
    }else if(strPackage.equals("leon")){
      reqLeft = true;
    }else if(strPackage.equals("rion")){
      reqRight = true;
    }else if(strPackage.equals("fwoff")){
      reqFw = false;
    }else if(strPackage.equals("bwoff")){
      reqBw = false;
    }else if(strPackage.equals("leoff")){
      reqLeft = false;
    }else if(strPackage.equals("rioff")){
      reqRight = false;
    }
  }
  memset(packetBuffer, 0, RECVLENGTH);
}

void servoWrite(uint8_t channel, uint8_t angle) {
  // regarding the datasheet of sg90 servo, pwm period is 20 ms and duty is 1->2ms
  uint32_t maxDuty = (pow(2,SERVO_RESOLUTION)-1)/10; 
  uint32_t minDuty = (pow(2,SERVO_RESOLUTION)-1)/20; 
  uint32_t duty = (maxDuty-minDuty)*angle/180 + minDuty;
  ledcWrite(channel, duty);
}

void controlServos(){
  if(reqFw){
    if(posPitch<60){
      posPitch += 1;
    }
  }
  if(reqBw){
    if(posPitch>0){
      posPitch -= 1;
    }
  }
  if(reqLeft){
    if(posYaw<180){
      posYaw += 1;
    }
  }
  if(reqRight){
    if(posYaw>0){
      posYaw -= 1;
    }
  }
  
  servoWrite(2,posPitch);
  servoWrite(4,posYaw);
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {

  switch(type) {
      case WStype_DISCONNECTED:
          Serial.printf("[%u] Disconnected!\n", num);
          camNo = num;
          clientConnected = false;
          break;
      case WStype_CONNECTED:
          Serial.printf("[%u] Connected!\n", num);
          clientConnected = true;
          break;
      case WStype_TEXT:
      case WStype_BIN:
      case WStype_ERROR:
      case WStype_FRAGMENT_TEXT_START:
      case WStype_FRAGMENT_BIN_START:
      case WStype_FRAGMENT:
      case WStype_FRAGMENT_FIN:
          Serial.println(type);
          break;
  }
}

void setup(void) {
  Serial.begin(115200);
  Serial.print("\n");
  #ifdef DEBUG
  Serial.setDebugOutput(true);
  #endif

  cameraInitState = initCamera();

  Serial.printf("camera init state %d\n", cameraInitState);

  // pinMode(LED_BUILTIN, OUTPUT);

  if(cameraInitState != 0){
    // digitalWrite(LED_BUILTIN, HIGH);
    return;
  }

  //WIFI INIT
  Serial.printf("Connecting to %s\n", ssid);
  if (String(WiFi.SSID()) != String(ssid)) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
  }

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    // if the LED is off turn it on and vice-versa:
    if (ledState == LOW) {
      ledState = HIGH;
    } else {
      ledState = LOW;
    }

    // set the LED with the ledState of the variable:
    // digitalWrite(LED_BUILTIN, ledState);
    Serial.print(".");
  }
  // digitalWrite(LED_BUILTIN, LOW);
  Serial.println("");
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  UDPServer.begin(UDPPort); 
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);

  // 1. 50hz ==> period = 20ms (sg90 servo require 20ms pulse, duty cycle is 1->2ms: -90=>90degree)
  // 2. resolution = 16, maximum value is 2^16-1=65535
  // From 1 and 2 => -90=>90 degree or 0=>180degree ~ 3276=>6553
  ledcSetup(4, 50, SERVO_RESOLUTION);//channel, freq, resolution
  ledcAttachPin(PIN_SERVO_YAW, 4);// pin, channel

  ledcSetup(2, 50, SERVO_RESOLUTION);//channel, freq, resolution
  ledcAttachPin(PIN_SERVO_PITCH, 2);// pin, channel
}

void loop(void) {
  webSocket.loop();
  if(clientConnected == true){
    grabImage(jpgLength, jpgBuff);
    webSocket.sendBIN(camNo, jpgBuff, jpgLength);
    // Serial.print("send img: ");
    // Serial.println(jpgLength);
  }
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    processData();
  }
  if (currentMillis - previousMillisServo >= intervalServo) {
    previousMillisServo = currentMillis;
    controlServos();
  }
}
