#include <WiFi.h>
#include <WiFiUdp.h>
#include <SPIFFS.h>
#include <FS.h>
#include "camera_wrap.h"

// #define DEBUG
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

const int RECVLENGTH = 8;
byte packetBuffer[RECVLENGTH];

unsigned long previousMillis = 0;
unsigned long previousMillisServo = 0;
const unsigned long interval = 30;
const unsigned long intervalServo = 100;

bool bStream = false;
const char strFinish[] = {'D','o','n','e'};

int debugCnt=0;

bool reqLeft = false;
bool reqRight = false;
bool reqFw = false;
bool reqBw = false;

const int PIN_SERVO_YAW   = 12;
const int PIN_SERVO_PITCH = 2;
const int LED_BUILTIN = 4;
int ledState = LOW;

int posYaw = 90;
int posPitch = 30;
int delta = 1;

void setup(void) {
  Serial.begin(115200);
  Serial.print("\n");
  Serial.setDebugOutput(true);

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

  ledcSetup(4, 50, 16);//channel, freq, resolution
  ledcAttachPin(PIN_SERVO_YAW, 4);// pin, channel

  ledcSetup(2, 50, 16);//channel, freq, resolution
  ledcAttachPin(PIN_SERVO_PITCH, 2);// pin, channel

#ifdef SAVE_IMG
  if (!SPIFFS.begin(true)) {
    Serial.println("An Error has occurred while mounting SPIFFS");
    ESP.restart();
  }
  else {
    delay(500);
    Serial.println("SPIFFS mounted successfully");
  }
#endif

}

void loop(void) {

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    processData();
    stream();
  }
  if (currentMillis - previousMillisServo >= intervalServo) {
    previousMillisServo = currentMillis;
    controlServos();
  }
}

void processData(){
  int cb = UDPServer.parsePacket();
  if (cb) {
    UDPServer.read(packetBuffer, RECVLENGTH);
    addrRemote = UDPServer.remoteIP();
    portRemote = UDPServer.remotePort();

#ifdef DEBUG
    Serial.print("receive: ");
    String strPackage = String((const char*)packetBuffer);
    // for (int y = 0; y < RECVLENGTH; y++){
    //   Serial.print(packetBuffer[y]);
    //   Serial.print("\n");
    // }
    Serial.print(strPackage);
    Serial.print(" from: ");
    Serial.println(addrRemote);
#endif
    if(  packetBuffer[0]=='s' 
      && packetBuffer[1]=='t' 
      && packetBuffer[2]=='r' 
      && packetBuffer[3]=='e'
      && packetBuffer[4]=='a'
      && packetBuffer[5]=='m'){
        bStream = true;
        if(!tcpClient.connected()){
          if (!tcpClient.connect(addrRemote, 6868)) {
            Serial.println("connection failed");
          }
        }
    }else if(  packetBuffer[0]=='s' 
              && packetBuffer[1]=='t' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='p'){
        bStream = false;
        tcpClient.stop();
    }else if(  packetBuffer[0]=='f' 
              && packetBuffer[1]=='w' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='n'
            ){
        reqFw = true;
    }else if(  packetBuffer[0]=='b' 
              && packetBuffer[1]=='w'
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='n'
              ){
        reqBw = true;
    }else if(  packetBuffer[0]=='l' 
              && packetBuffer[1]=='e' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='n'){
        reqLeft = true;
    }else if(  packetBuffer[0]=='r' 
              && packetBuffer[1]=='i' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='n'){
        reqRight = true;
    }else if(  packetBuffer[0]=='f' 
              && packetBuffer[1]=='w' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='f'
              && packetBuffer[4]=='f'
            ){
        reqFw = false;
    }else if(  packetBuffer[0]=='b' 
              && packetBuffer[1]=='w'
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='f'
              && packetBuffer[4]=='f'
              ){
        reqBw = false;
    }else if(  packetBuffer[0]=='l' 
              && packetBuffer[1]=='e' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='f'
              && packetBuffer[4]=='f'){
        reqLeft = false;
    }else if(  packetBuffer[0]=='r' 
              && packetBuffer[1]=='i' 
              && packetBuffer[2]=='o' 
              && packetBuffer[3]=='f'
              && packetBuffer[4]=='f'){
        reqRight = false;
    }
  }
  memset(packetBuffer, 0, RECVLENGTH);
}

void stream(){
  // Serial.print("bStream: ");
  // Serial.println(bStream);
  if(bStream){
    if (grabImage(jpgLength, jpgBuff) == ESP_OK){

#ifdef SAVE_IMG
      if(debugCnt>=20){
        debugCnt=0;
      }
      String FILE_PHOTO = "/photo_" + String(debugCnt++) + ".jpg";
      File file = SPIFFS.open(FILE_PHOTO.c_str(), FILE_WRITE);

      // Insert the data in the photo file
      if (!file) {
        Serial.println("Failed to open file in writing mode");
      }
      else {
        file.write(jpgBuff, jpgLength); // payload (image), payload length
        Serial.print("The picture has been saved in ");
        Serial.print(FILE_PHOTO);
        Serial.print(" - Size: ");
        Serial.print(file.size());
        Serial.println(" bytes");
      }
      // Close the file
      file.close();
#endif

#ifdef DEBUG
      Serial.printf("Image length %d\n", jpgLength);
#endif
      sendImageTcp();
      sendLenghtTcp();
    }
    delay(50);
  }
}

void servoWrite(uint8_t channel, uint32_t value, uint32_t valueMax = 180) {
  // calculate duty, 8191 from 2 ^ 13 - 1
  uint32_t duty = (8191 / valueMax) * min(value, valueMax);
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
  
  servoWrite(2,posPitch,60);
  servoWrite(4,posYaw);
}


void sendImageTcp(){
  tcpClient.write(jpgBuff, jpgLength);
}

void sendLenghtTcp(){
  String strlength = String(jpgLength);
  int len = strlength.length();
  while(len++ < 6){
    strlength = String("0") + strlength;
  }
  strlength = String("len:") + strlength;
  tcpClient.write((const uint8_t* )strlength.c_str(), strlength.length());
}

void sendImageUdp(){
  uint8_t* ptr = jpgBuff;
  int jpgLengthTmp = jpgLength;
  while(jpgLengthTmp>1024){
    UDPServer.beginPacket(addrRemote, portRemote);
    UDPServer.write(ptr, 1024);
    UDPServer.endPacket();
    jpgLengthTmp-=1024;
    ptr+=1024;
  }
  if(jpgLengthTmp>0){
    UDPServer.beginPacket(addrRemote, portRemote);
    UDPServer.write(ptr, jpgLengthTmp);
    UDPServer.endPacket();
  }
}

void sendLengthUdp(){
  String strlength = String(jpgLength);
  int len = strlength.length();
  while(len++ < 6){
    strlength = String("0") + strlength;
  }
  strlength = String("length:")+strlength;
  UDPServer.beginPacket(addrRemote, portRemote);
  UDPServer.write((const uint8_t*)strlength.c_str(), strlength.length());
  UDPServer.endPacket();
}

