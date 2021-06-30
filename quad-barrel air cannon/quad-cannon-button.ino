/*
 * quad-cannon-button by Hardware Unknown (https://www.youtube.com/hardwareunknown)
 */

const int solenoid1 = 5;
const int solenoid2 = 4;
const int solenoid3 = 3;
const int solenoid4 = 7;
const int button = A3;

unsigned long solenoid1Start = 0; // time when solenoid1 was last opened
unsigned long solenoid2Start = 0; // time when solenoid2 was last opened
unsigned long solenoid3Start = 0; // time when solenoid3 was last opened
unsigned long solenoid4Start = 0; // time when solenoid4 was last opened
unsigned long solenoidWait = 150; // time between cannons firing during rapid fire sequence
unsigned long solenoidInterval = 1000; // # ms solenoid remains open for

unsigned long launcherArmDelay = 1000; // how long until launcher is armed after final rapid fire shot

bool buttonPressed = false; 
bool launcherArmed = true;

unsigned long currentMillis = 0;

void setup()
{  
  pinMode(solenoid1, OUTPUT);
  pinMode(solenoid2, OUTPUT);
  pinMode(solenoid3, OUTPUT);
  pinMode(solenoid4, OUTPUT);
  
  pinMode(button, INPUT_PULLUP);

  delay(1000); // prevents solenoids all simultaneously firing on startup, unsure why this occured before
}

void loop(){
  buttonPressed = !digitalRead(button);
  if (buttonPressed && launcherArmed){ // if button is pressed, enter the while loop
    launcherArmed = false;
    solenoid1Start = millis();
    solenoid2Start = millis() + solenoidWait;
    solenoid3Start = millis() + (2 * solenoidWait);
    solenoid4Start = millis() + (3 * solenoidWait);
  }
  if (millis() - solenoid1Start < solenoidInterval){
    digitalWrite(solenoid1, HIGH); // open the solenoid valve
  }
  else{
    digitalWrite(solenoid1, LOW); // close the solenoid valve
  }
  if (millis() - solenoid2Start < solenoidInterval && millis() >= solenoid2Start){
    digitalWrite(solenoid2, HIGH); // open the solenoid valve
  }
  else{
    digitalWrite(solenoid2, LOW); // close the solenoid valve
  }
  if (millis() - solenoid3Start < solenoidInterval && millis() >= solenoid3Start){
    digitalWrite(solenoid3, HIGH); // open the solenoid valve
  }
  else{
    digitalWrite(solenoid3, LOW); // close the solenoid valve
  }
  if (millis() - solenoid4Start < solenoidInterval && millis() >= solenoid4Start){
    digitalWrite(solenoid4, HIGH); // open the solenoid valve
  }
  else{
    digitalWrite(solenoid4, LOW); // close the solenoid valve
  }
  if (millis() >= solenoid4Start + solenoidInterval + launcherArmDelay){
    launcherArmed = true;
  }
}
