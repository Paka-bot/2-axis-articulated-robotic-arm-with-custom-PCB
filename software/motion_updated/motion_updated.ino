#include <math.h>

#define M1_STEP 18
#define M1_DIR  19
#define M2_STEP 21
#define M2_DIR  22
#define M_EN    5

const float STEPS_PER_REV = 1600.0; 
const int SPEED_DELAY = 3000; 

long current_step1 = 0; 
long current_step2 = 0;

void setup() {
  Serial.begin(115200);
  pinMode(M1_STEP, OUTPUT); pinMode(M1_DIR, OUTPUT);
  pinMode(M2_STEP, OUTPUT); pinMode(M2_DIR, OUTPUT);
  pinMode(M_EN, OUTPUT);
  digitalWrite(M_EN, LOW);
  Serial.println("Ready");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim(); cmd.toUpperCase();
    
    if (cmd == "M2") { digitalWrite(M_EN, HIGH); Serial.println("OFF"); return; }
    if (cmd == "M6") { digitalWrite(M_EN, LOW); Serial.println("ON"); return; }
    
    if (cmd.indexOf("M1") != -1 && cmd.indexOf("M2") != -1) {
      float v1 = parseVal(cmd, "M1");
      float v2 = parseVal(cmd, "M2");
      moveSimultaneous(v1, v2);
    }
  }
}

float parseVal(String cmd, String key) {
  int idx = cmd.indexOf(key);
  int next = cmd.indexOf(' ', idx + 3);
  return cmd.substring(idx + 3, next == -1 ? cmd.length() : next).toFloat();
}

void moveSimultaneous(float angle1, float angle2) {
  long target1 = current_step1 + round(angle1 * (STEPS_PER_REV / 360.0));
  long target2 = current_step2 + round(angle2 * (STEPS_PER_REV / 360.0));
  
  long d1 = target1 - current_step1;
  long d2 = target2 - current_step2;
  
  int dir1 = d1 > 0 ? HIGH : LOW;
  int dir2 = d2 > 0 ? LOW : HIGH;

  digitalWrite(M1_DIR, dir1);
  digitalWrite(M2_DIR, dir2);
  
  d1 = abs(d1); d2 = abs(d2);
  long max_steps = max(d1, d2);
  long c1 = max_steps / 2;
  long c2 = max_steps / 2;
  
  for(long i=0; i<max_steps; i++) {
    if (Serial.available() > 0) {
      String check = Serial.readStringUntil('\n');
      check.trim(); check.toUpperCase();
      if (check == "M2") { 
        digitalWrite(M_EN, HIGH);
        Serial.println("OFF");
        return;
      }
    }

    c1 -= d1;
    if(c1 < 0) { 
      digitalWrite(M1_STEP, HIGH); delayMicroseconds(2); digitalWrite(M1_STEP, LOW); 
      c1 += max_steps; 
    }
    c2 -= d2;
    if(c2 < 0) { 
      digitalWrite(M2_STEP, HIGH); delayMicroseconds(2); digitalWrite(M2_STEP, LOW); 
      c2 += max_steps; 
    }
    delayMicroseconds(SPEED_DELAY);
  }
  current_step1 = target1;
  current_step2 = target2;
  Serial.println("OK");
}