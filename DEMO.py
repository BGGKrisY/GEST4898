#include <Wire.h>
#include <VL53L1X.h>
#include <ESP8266WiFi.h>
VL53L1X sensor;
const int COMPUTER_DISTANCE = 500;
const int TABLET_DISTANCE = 400;
const int SMARTPHONE_DISTANCE = 300;
const char* ssid = "LovelyYeung";
const char* password = "60375468";
WiFiServer server(80);
const int buzzerPin = D3; 
String output5State = "off";
uint16_t currentDistance = 0;
uint8_t currentRiskLevel = 0;
String riskMessage = "";
bool buzzerEnabled = true;
unsigned long lastBuzzerTime = 0;
bool isBuzzing = false;
void setup() {
  Serial.begin(115200);
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);
  Wire.begin(D2, D1);
  Wire.setClock(400000);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
  if (!sensor.init()) {
    while(1);
  }
  sensor.setDistanceMode(VL53L1X::Short);
  sensor.setMeasurementTimingBudget(20000);
  sensor.startContinuous(10);
}
uint8_t calculateRiskLevel(uint16_t distance_mm) {
  if (distance_mm <= SMARTPHONE_DISTANCE) return 2;
  if (distance_mm <= TABLET_DISTANCE) return 1;
  if (distance_mm <= COMPUTER_DISTANCE) return 0;
  return 0;
}
String getRiskMessage(uint8_t risk_level) {
  switch(risk_level) {
    case 0: return "Safe";
    case 1: return "Warning";
    case 2: return "High Risk";
    default: return "Unknown";
  }
}
void controlBuzzer() {
  if (!buzzerEnabled) {
    digitalWrite(buzzerPin, LOW);
    return;
  }
  unsigned long currentTime = millis();
  switch(currentRiskLevel) {
    case 2:
      if (currentTime - lastBuzzerTime >= 500) {
        lastBuzzerTime = currentTime;
        isBuzzing = !isBuzzing;
        digitalWrite(buzzerPin, isBuzzing ? HIGH : LOW);
      }
      break;
    case 1:
      if (currentTime - lastBuzzerTime >= 1500) {
        lastBuzzerTime = currentTime;
        isBuzzing = !isBuzzing;
        digitalWrite(buzzerPin, isBuzzing ? HIGH : LOW);
      }
      break;
    case 0:
    default:
      digitalWrite(buzzerPin, LOW);
      isBuzzing = false;
      break;
  }
}
void playBeep(int duration) {
  digitalWrite(buzzerPin, HIGH);
  delay(duration);
  digitalWrite(buzzerPin, LOW);
}
void handleWebClient() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("New Client.");
    String currentLine = "";
    String header = "";
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        header += c;
        if (c == '\n') {
          if (currentLine.length() == 0) {
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html;charset=utf-8");
            client.println("Connection: close");
            client.println();
            client.println("<!DOCTYPE html><html>");
            client.println("<head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
            client.println("<meta http-equiv=\"refresh\" content=\"1\">");
            client.println("<link rel=\"icon\" href=\"data:,\">");
            client.println("<style>html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}");
            client.println(".button { background-color: #195B6A; border: none; color: white; padding: 16px 40px;");
            client.println("text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}");
            client.println(".button2 {background-color: #77878A;}");
            client.println(".buzzer-btn {background-color: #FF6B6B; padding: 10px 20px; font-size: 20px;}");
            client.println(".buzzer-btn2 {background-color: #4ECDC4;}");
            client.println(".safe {color: green;}");
            client.println(".warning {color: orange;}");
            client.println(".danger {color: red; font-weight: bold;}");
            client.println("</style></head>");
            client.println("<body><h1>Smart Glasses For Myopia Risk Evaluation</h1>");
            client.println("<h2>Real-time Monitoring Data</h2>");
            client.print("<p>Current Distance: <strong>");
            client.print(currentDistance);
            client.println(" mm</strong></p>");
            client.print("<p>Risk Level: <strong class=\"");
            switch(currentRiskLevel) {
              case 0: client.print("safe"); break;
              case 1: client.print("warning"); break;
              case 2: client.print("danger"); break;
            }
            client.print("\">");
            client.print(getRiskMessage(currentRiskLevel));
            client.println("</strong></p>");           
            if (currentRiskLevel == 2) {
              client.println("<p style=\"color:red; font-weight:bold;\">Reminder: Please maintain proper viewing distance!</p>");
            }
            client.println("<h2>Buzzer Control</h2>");
            client.print("<p>Buzzer Status: <strong>");
            client.print(buzzerEnabled ? "Enabled" : "Disabled");
            client.println("</strong></p>");
            if (buzzerEnabled) {
              client.println("<p><a href=\"/buzzer/off\"><button class=\"button buzzer-btn\">Turn Off Buzzer</button></a></p>");
              client.println("<p><a href=\"/testbeep\"><button class=\"button\">Test Buzzer</button></a></p>");
            } else {
              client.println("<p><a href=\"/buzzer/on\"><button class=\"button buzzer-btn2\">Turn On Buzzer</button></a></p>");
            }
            client.println("<h2>Eye Health Suggestions</h2>");
            client.println("<ul style=\"text-align: left; display: inline-block;\">");
            client.println("<li>Maintain computer screen distance: Above 50cm</li>");
            client.println("<li>Maintain tablet distance: Above 40cm</li>");
            client.println("<li>Maintain smartphone distance: Above 30cm</li>");
            client.println("<li>Look at something 20 feet away for 20 seconds every 20 minutes</li>");
            client.println("</ul>");
            client.println("</body></html>");
            client.println();
            break;
          } else {
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }
        if (currentLine.endsWith("GET /buzzer/on")) {
          buzzerEnabled = true;
        } else if (currentLine.endsWith("GET /buzzer/off")) {
          buzzerEnabled = false;
          digitalWrite(buzzerPin, LOW);
        } else if (currentLine.endsWith("GET /testbeep")) {
          playBeep(500); 
        }
      }
    }
    header = "";
    client.stop();
    Serial.println("Client disconnected.");
  }
}
void loop() {
  uint16_t distance_mm = sensor.read();
  if (!sensor.timeoutOccurred() && distance_mm < 2000) {
    currentDistance = distance_mm+40;
    currentRiskLevel = calculateRiskLevel(currentDistance);
  }
  controlBuzzer();
  handleWebClient();
  delay(100);
}
