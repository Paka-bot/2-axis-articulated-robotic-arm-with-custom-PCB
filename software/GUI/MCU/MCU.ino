void setup() {
  Serial.begin(115200);
  
  delay(1000); 
  Serial.println("ESP32 Communication Ready(115200 bps)");
}

void loop() {
  if (Serial.available() > 0) {
    String receivedData = Serial.readStringUntil('\n');
    
    Serial.print("ESP32 DATA received : ");
    Serial.println(receivedData);
  }
}