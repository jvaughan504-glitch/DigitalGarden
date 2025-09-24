#include <WiFi.h>
#include "BluetoothSerial.h"

// ---------- Wi-Fi ----------
const char* ssid = "WIFILampV1";
const char* password = "12345678";
WiFiServer server(80);

// ---------- Bluetooth ----------
BluetoothSerial SerialBT;

// ---------- LED states ----------
String redState   = "off";
String greenState = "off";
String blueState  = "off";
String whiteState = "off";

// ---------- GPIO ----------
const int redLED   = 26;
const int greenLED = 27;
const int blueLED  = 12;
const int whiteLED = 13;

// ---------- PWM ----------
const int redCh   = 0;
const int greenCh = 1;
const int blueCh  = 2;
const int whiteCh = 3;

// ---------- Flower LEDs ----------
const int flowerPins[] = {23, 22, 21, 19, 18, 5, 25, 33, 32, 35};
const int flowerCount = sizeof(flowerPins)/sizeof(flowerPins[0]);
int flowerCh[flowerCount];
float flowerPhase[flowerCount];
int twinkleSpeed = 50;   // 1 = slow, 100 = fast twinkle

// ---------- Modes ----------
enum Mode { MANUAL, CHASE, BLINK, FADE, RAINBOW };
Mode currentMode = MANUAL;

// ---------- Tunables ----------
int blinkInterval  = 500;
int chaseInterval  = 300;
int fadeStep       = 5;
int rainbowSpeed   = 30;

// ---------- HTML template in PROGMEM ----------
const char MAIN_page[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
body{background:#000;color:#fff;font-family:Helvetica;text-align:center}
h1{font-size:20px;margin:8px 0}
.g{display:grid;grid-template-columns:1fr 1fr;gap:4px}
.b{border:none;color:#fff;padding:6px 12px;font-size:14px;cursor:pointer}
.off{background:#555}.on{background:#4CAF50}.m{background:#2196F3}
p{margin:4px 0;font-size:12px}input[type=range]{width:90%}
</style></head><body><h1>WIFILampV1</h1>
%BUTTONS%
<h2>Modes</h2><div class='g'>
<a href='/mode/manual'><button class='b m'>Manual</button></a>
<a href='/mode/chase'><button class='b m'>Chase</button></a>
<a href='/mode/blink'><button class='b m'>Blink</button></a>
<a href='/mode/fade'><button class='b m'>Fade</button></a>
<a href='/mode/rainbow'><button class='b m'>Rainbow</button></a>
</div>
<h2>Settings</h2>
<p>Blink Speed <input type='range' min='0' max='100' value='%BLINK%' onchange="location='/set?blink='+this.value"></p>
<p>Chase Speed <input type='range' min='0' max='100' value='%CHASE%' onchange="location='/set?chase='+this.value"></p>
<p>Fade Step <input type='range' min='0' max='100' value='%FADE%' onchange="location='/set?fade='+this.value"></p>
<p>Rainbow Speed <input type='range' min='0' max='100' value='%RAINBOW%' onchange="location='/set?rainbow='+this.value"></p>
<p>Twinkle Speed <input type='range' min='0' max='100' value='%TWINKLE%' onchange="location='/set?twinkle='+this.value"></p>
</body></html>
)rawliteral";

// ---------- Helpers ----------
void handleModes();
void applyManual(String color, bool on);
void handleCommand(String cmd);
String buildPage();

void setup() {
  // PWM setup
  ledcSetup(redCh,   5000, 8);
  ledcSetup(greenCh, 5000, 8);
  ledcSetup(blueCh,  5000, 8);
  ledcSetup(whiteCh, 5000, 8);
  ledcAttachPin(redLED,   redCh);
  ledcAttachPin(greenLED, greenCh);
  ledcAttachPin(blueLED,  blueCh);
  ledcAttachPin(whiteLED, whiteCh);

  // Flowers
  for (int i=0; i<flowerCount; i++) {
    flowerCh[i] = 4 + i;
    ledcSetup(flowerCh[i], 5000, 8);
    ledcAttachPin(flowerPins[i], flowerCh[i]);
    flowerPhase[i] = random(0, 628) / 100.0;
  }

  WiFi.softAP(ssid, password);
  server.begin();
  SerialBT.begin("WIFILampV1");
}

void loop() {
  // Bluetooth
  if (SerialBT.available()) {
    String btCmd = SerialBT.readStringUntil('\n');
    btCmd.trim();
    if (btCmd.length()) handleCommand(btCmd);
  }

  // HTTP
  WiFiClient client = server.available();
  if (client) {
    String header="";
    String currentLine="";
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        header += c;
        if (c == '\n') {
          if (currentLine.length() == 0) {
            // --- routes ---
            if (header.indexOf("GET /red/on")    >= 0) handleCommand("RED ON");
            if (header.indexOf("GET /red/off")   >= 0) handleCommand("RED OFF");
            if (header.indexOf("GET /green/on")  >= 0) handleCommand("GREEN ON");
            if (header.indexOf("GET /green/off") >= 0) handleCommand("GREEN OFF");
            if (header.indexOf("GET /blue/on")   >= 0) handleCommand("BLUE ON");
            if (header.indexOf("GET /blue/off")  >= 0) handleCommand("BLUE OFF");
            if (header.indexOf("GET /white/on")  >= 0) handleCommand("WHITE ON");
            if (header.indexOf("GET /white/off") >= 0) handleCommand("WHITE OFF");

            if (header.indexOf("GET /mode/manual")  >= 0) handleCommand("MODE MANUAL");
            if (header.indexOf("GET /mode/chase")   >= 0) handleCommand("MODE CHASE");
            if (header.indexOf("GET /mode/blink")   >= 0) handleCommand("MODE BLINK");
            if (header.indexOf("GET /mode/fade")    >= 0) handleCommand("MODE FADE");
            if (header.indexOf("GET /mode/rainbow") >= 0) handleCommand("MODE RAINBOW");

            if (header.indexOf("GET /set?blink=") >= 0) blinkInterval = map(header.substring(header.indexOf("blink=")+6).toInt(), 0,100,2000,50);
            if (header.indexOf("GET /set?chase=") >= 0) chaseInterval = map(header.substring(header.indexOf("chase=")+6).toInt(), 0,100,2000,50);
            if (header.indexOf("GET /set?fade=") >= 0)  fadeStep = constrain(map(header.substring(header.indexOf("fade=")+5).toInt(),0,100,1,20),1,20);
            if (header.indexOf("GET /set?rainbow=")>=0) rainbowSpeed = map(header.substring(header.indexOf("rainbow=")+8).toInt(),0,100,200,10);
            if (header.indexOf("GET /set?twinkle=")>=0) twinkleSpeed = constrain(header.substring(header.indexOf("twinkle=")+8).toInt(),1,100);

            // --- serve page ---
            client.println(F("HTTP/1.1 200 OK"));
            client.println(F("Content-type:text/html"));
            client.println(F("Connection: close"));
            client.println();
            client.print(buildPage());
            client.println();
            break;
          } else currentLine="";
        } else if (c!='\r') currentLine+=c;
      }
    }
    client.stop();
  }

  handleModes();
}

// ---------- Helpers ----------
void applyManual(String color, bool on) {
  int duty = on ? 255 : 0;
  if (color=="RED")   { ledcWrite(redCh,duty);   redState=on?"on":"off"; }
  if (color=="GREEN") { ledcWrite(greenCh,duty); greenState=on?"on":"off"; }
  if (color=="BLUE")  { ledcWrite(blueCh,duty);  blueState=on?"on":"off"; }
  if (color=="WHITE") { ledcWrite(whiteCh,duty); whiteState=on?"on":"off"; }
}

void handleCommand(String cmd) {
  cmd.trim(); cmd.toUpperCase();
  if (cmd=="RED ON")    { applyManual("RED",true); return; }
  if (cmd=="RED OFF")   { applyManual("RED",false); return; }
  if (cmd=="GREEN ON")  { applyManual("GREEN",true); return; }
  if (cmd=="GREEN OFF") { applyManual("GREEN",false); return; }
  if (cmd=="BLUE ON")   { applyManual("BLUE",true); return; }
  if (cmd=="BLUE OFF")  { applyManual("BLUE",false); return; }
  if (cmd=="WHITE ON")  { applyManual("WHITE",true); return; }
  if (cmd=="WHITE OFF") { applyManual("WHITE",false); return; }
  if (cmd.startsWith("MODE ")) {
    String m=cmd.substring(5);
    if (m=="MANUAL") currentMode=MANUAL;
    else if (m=="CHASE") currentMode=CHASE;
    else if (m=="BLINK") currentMode=BLINK;
    else if (m=="FADE") currentMode=FADE;
    else if (m=="RAINBOW") currentMode=RAINBOW;
    return;
  }
  if (cmd.startsWith("SET ")) {
    int sp1=cmd.indexOf(' '); int sp2=cmd.indexOf(' ',sp1+1);
    if (sp2>0) {
      String key=cmd.substring(sp1+1,sp2);
      int val=cmd.substring(sp2+1).toInt();
      if (key=="BLINK") blinkInterval=constrain(val,50,2000);
      else if (key=="CHASE") chaseInterval=constrain(val,50,2000);
      else if (key=="FADE") fadeStep=constrain(val,1,20);
      else if (key=="RAINBOW") rainbowSpeed=constrain(val,10,200);
      else if (key=="TWINKLE") twinkleSpeed=constrain(val,1,100);
    }
  }
}

String buildPage(){
  String page=MAIN_page;
  page.replace("%BLINK%",String(map(blinkInterval,2000,50,0,100)));
  page.replace("%CHASE%",String(map(chaseInterval,2000,50,0,100)));
  page.replace("%FADE%",String(map(fadeStep,1,20,0,100)));
  page.replace("%RAINBOW%",String(map(rainbowSpeed,200,10,0,100)));
  page.replace("%TWINKLE%",String(twinkleSpeed));
  // LED buttons
  String btns="<div class='g'>";
  btns+="<div><p>Red-"+redState+"</p><a href='/red/"+(redState=="off"?"on":"off")+"'><button class='b "+(redState=="off"?"off":"on")+"'>"+(redState=="off"?"ON":"OFF")+"</button></a></div>";
  btns+="<div><p>Green-"+greenState+"</p><a href='/green/"+(greenState=="off"?"on":"off")+"'><button class='b "+(greenState=="off"?"off":"on")+"'>"+(greenState=="off"?"ON":"OFF")+"</button></a></div>";
  btns+="<div><p>Blue-"+blueState+"</p><a href='/blue/"+(blueState=="off"?"on":"off")+"'><button class='b "+(blueState=="off"?"off":"on")+"'>"+(blueState=="off"?"ON":"OFF")+"</button></a></div>";
  btns+="<div><p>White-"+whiteState+"</p><a href='/white/"+(whiteState=="off"?"on":"off")+"'><button class='b "+(whiteState=="off"?"off":"on")+"'>"+(whiteState=="off"?"ON":"OFF")+"</button></a></div>";
  btns+="</div>";
  page.replace("%BUTTONS%",btns);
  return page;
}

// ---------- Effect engine ----------
void handleModes(){
  static unsigned long lastMillis=0;
  static int chaseIndex=0;
  static bool blinkOn=false;
  static int redVal=0, redDir=5;
  static int greenVal=64, greenDir=4;
  static int blueVal=128, blueDir=3;
  static int whiteVal=192, whiteDir=2;
  static float angle=0.0;
  unsigned long now=millis();

  if(currentMode==CHASE && now-lastMillis>=chaseInterval){
    lastMillis=now;
    ledcWrite(redCh,0);ledcWrite(greenCh,0);ledcWrite(blueCh,0);ledcWrite(whiteCh,0);
    switch(chaseIndex){case 0:ledcWrite(redCh,255);break;case 1:ledcWrite(greenCh,255);break;case 2:ledcWrite(blueCh,255);break;case 3:ledcWrite(whiteCh,255);break;}
    chaseIndex=(chaseIndex+1)%4;
  }
  else if(currentMode==BLINK && now-lastMillis>=blinkInterval){
    lastMillis=now; blinkOn=!blinkOn;
    int val=blinkOn?255:0;
    ledcWrite(redCh,val);ledcWrite(greenCh,val);ledcWrite(blueCh,val);ledcWrite(whiteCh,val);
  }
  else if(currentMode==FADE && now-lastMillis>=40){
    lastMillis=now;
    redVal+=redDir;if(redVal>=255||redVal<=0)redDir=-redDir;
    greenVal+=greenDir;if(greenVal>=255||greenVal<=0)greenDir=-greenDir;
    blueVal+=blueDir;if(blueVal>=255||blueVal<=0)blueDir=-blueDir;
    whiteVal+=whiteDir;if(whiteVal>=255||whiteVal<=0)whiteDir=-whiteDir;
    ledcWrite(redCh,redVal);ledcWrite(greenCh,greenVal);ledcWrite(blueCh,blueVal);ledcWrite(whiteCh,whiteVal);
  }
  else if(currentMode==RAINBOW && now-lastMillis>=rainbowSpeed){
    lastMillis=now;
    angle+=0.05f;if(angle>6.28318f)angle=0.0f;
    int r=(sin(angle)+1.0f)*127.0f;
    int g=(sin(angle+2.0944f)+1.0f)*127.0f;
    int b=(sin(angle+4.1888f)+1.0f)*127.0f;
    ledcWrite(redCh,r);ledcWrite(greenCh,g);ledcWrite(blueCh,b);ledcWrite(whiteCh,0);
  }

  // Flowers twinkle always
  static unsigned long lastTwinkle=0;
  if(now-lastTwinkle>=30){
    lastTwinkle=now;
    for(int i=0;i<flowerCount;i++){
      flowerPhase[i]+=0.02*(twinkleSpeed/50.0);
      if(flowerPhase[i]>6.28)flowerPhase[i]-=6.28;
      int brightness=(sin(flowerPhase[i])+1.0)*127;
      ledcWrite(flowerCh[i],brightness);
    }
  }
}
