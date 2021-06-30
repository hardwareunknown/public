/*
 * ArduinoNunchuk library by Gabriel Bianconi
 * Copyright 2011-2013 Gabriel Bianconi, http://www.gabrielbianconi.com/
 * Source code: https://github.com/GabrielBianconi/arduino-nunchuk/tree/master/ArduinoNunchuk
 *
 * quad-cannon-nunchuk by Hardware Unknown (https://www.youtube.com/hardwareunknown)
 */


// In low power mode, automatically re-arms between individual shots

#include <Wire.h>
#include <ArduinoNunchuk.h>

// SCL ("Clk" on Nunchuky breakout) is connected to A5
// SDA ("Data" on Nunchuky breakout) is connected to A4
// +3.3V connected to +
// GND connected to -

const int redLed = 6;
const int yellowLed3 = 8;
const int yellowLed2 = 9;
const int yellowLed1 = 10;
const int greenLed = 11;
const int solenoid1 = 5;
const int solenoid2 = 4;
const int solenoid3 = 3;
const int solenoid4 = 7;

const int modeSwitch = A2;
//const int reset = 12;

const int leds[] = {greenLed,yellowLed1,yellowLed2,yellowLed3,redLed};

int brightness = 0;    // how bright the red led is
int fadeAmount = 5;    // how many points to fade the red led by
unsigned long fadeStart = 0; // time when previous fade cycle began
int fadeInterval = 10; // # ms between fade cycles (decrease for faster fade)
int currentBarrel = 1; // begin selected individual barrel at barrel 1

int powerMode; // store state of power mode switch

unsigned long blinkMillis = 0; // track last blink time
int blinkInterval = 50; // ms between blinks of arming leds during solenoid activation
int ledState = LOW; // track if the red led is lit or not during firing

unsigned long solenoidStart = 0; // time when solenoid was last opened
unsigned long solenoidInterval = 1000; // # ms solenoid remains open for

bool deviceArmed = false; 

unsigned long currentMillis = 0;
unsigned long armStart = 0; // start of the arming sequence

ArduinoNunchuk nunchuk = ArduinoNunchuk();

void setup()
{
//  digitalWrite(reset, HIGH);
//  delay(200); // wait to ensure reset pin is held high before assigning as output
//  pinMode(reset, OUTPUT); 
  
  for (int i=0; i<5; i++){ // set all leds as outputs
    pinMode(leds[i], OUTPUT);
  }
  pinMode(solenoid1, OUTPUT);
  pinMode(solenoid2, OUTPUT);
  pinMode(solenoid3, OUTPUT);
  pinMode(solenoid4, OUTPUT);

  pinMode(modeSwitch, INPUT_PULLUP);
  
  nunchuk.init(); // start the connection with the nunchuk
  
  digitalWrite(greenLed, HIGH); // indicate that the device is powered on

  Serial.begin(19200);
}

void loop(){
  nunchuk.update(); // check for data from nunchuk
  
  /*  The following if condition only occurs when the Arduino has been turned
   *  on and the nunchuk is first paired with it. At this point, the values stay static,
   *  and the Arduino cannot receive further input from the nunchuk. Once the Arduino is 
   *  reset (after having the nunchuk paired), the Arduino will automatically begin to
   *  properly receive input. 
   *  
   *  Thus, this statement will only run once until the Arduino is programmatically reset,
   *  as is done in the if statement.
   */
//  if (nunchuk.analogX == 255 && 
//      nunchuk.analogY == 255 && 
//      nunchuk.accelX == 1023 && 
//      nunchuk.accelY == 1023 && 
//      nunchuk.accelZ == 1023 && 
//      nunchuk.zButton == 0 && 
//      nunchuk.cButton == 0){
//        digitalWrite(reset, LOW);
//  }
  
  if (!deviceArmed){ // if the device is not armed, turn off all arming leds
    for (int i=1; i<5; i++){
      digitalWrite(leds[i], LOW);
    }
  }
  else{ // if device is armed
    fadeRedLed(); // visual indicator of armed device
    powerMode = digitalRead(modeSwitch);
    if (nunchuk.analogY < 20){ // if joystick is moved backward
      deviceArmed = false; 
    }

    if (powerMode){ // If firing mode switch is on, "BOOM", full power, all barrels shot at once
      if (nunchuk.zButton == 1){ // if z button is pressed, enter the while loop
        solenoidStart = millis();
        while (millis() - solenoidStart < solenoidInterval){ // stay in the loop for solenoidInterval
          Serial.println("firing all barrels");
          digitalWrite(solenoid1, HIGH); // open the solenoid valve
          digitalWrite(solenoid2, HIGH); // open the solenoid valve
          digitalWrite(solenoid3, HIGH); // open the solenoid valve
          digitalWrite(solenoid4, HIGH); // open the solenoid valve
  
          // rapidly blink arming leds (visual indicator of firing)
          if (millis() - blinkMillis >= blinkInterval){
            blinkMillis = millis();
            ledState = !ledState;
          }
          for (int i=1; i<5; i++){ 
            digitalWrite(leds[i], ledState);
          }
          
          // rapidly blink arming leds (visual indicator of firing)
          if (millis() - blinkMillis >= blinkInterval){
            blinkMillis = millis();
            ledState = !ledState;
          }
          for (int i=1; i<5; i++){ 
            digitalWrite(leds[i], ledState);
          }
        }
      digitalWrite(solenoid1, LOW); // close the solenoid valve (once the solenoidInterval elapses)
      digitalWrite(solenoid2, LOW);
      digitalWrite(solenoid3, LOW);
      digitalWrite(solenoid4, LOW);
      deviceArmed = false; // disarm device, readying it for re-arming
      Serial.println("device disarmed");
      }
    }
    else{ // If firing mode switch is off, low power, each barrel shot individually
      while (currentBarrel != 5){
        if (nunchuk.zButton == 1){ // if z button is pressed, enter the while loop
          Serial.print("currentBarrel: ");
          Serial.println(currentBarrel);
          solenoidStart = millis();
          while (millis() - solenoidStart < solenoidInterval){ // stay in the loop for solenoidInterval
            if (currentBarrel == 1){
              Serial.println("firing barrel 1");
              digitalWrite(solenoid1, HIGH); // open the solenoid valve
            }
            else if (currentBarrel == 2){
              Serial.println("firing barrel 2");
              digitalWrite(solenoid2, HIGH); // open the solenoid valve
            }
            else if (currentBarrel == 3){
              Serial.println("firing barrel 3");
              digitalWrite(solenoid3, HIGH); // open the solenoid valve
            }
            else{ // currentBarrel == 4
              Serial.println("firing barrel 4");
              digitalWrite(solenoid4, HIGH); // open the solenoid valve
            }
            
            // rapidly blink arming leds (visual indicator of firing)
            if (millis() - blinkMillis >= blinkInterval){
              blinkMillis = millis();
              ledState = !ledState;
            }
            for (int i=1; i<5; i++){ 
              digitalWrite(leds[i], ledState);
            }
          }
          digitalWrite(solenoid1, LOW); // close the solenoid valve (once the solenoidInterval elapses)
          digitalWrite(solenoid2, LOW);
          digitalWrite(solenoid3, LOW);
          digitalWrite(solenoid4, LOW);
          currentBarrel++;
          Serial.print("newBarrel: ");
          Serial.println(currentBarrel);
        }
      }
      currentBarrel = 1;
      Serial.print("newBarrel: ");
      Serial.println(currentBarrel);
      deviceArmed = false; // disarm device, readying it for re-arming
      Serial.println("device disarmed");
    }
  }

  if (nunchuk.analogY > 220 && nunchuk.cButton == 1){ // if joystick held forward and C button pressed
    armStart = millis(); // begin the arming countdown

    /* As long as joystick and button are held, while loop continues.
     * If either the joystick or button are released before the device is armed,
     * the while loop exits and the arming sequence is reset.
     */
    while (!deviceArmed && nunchuk.analogY > 220 && nunchuk.cButton == 1){ // as long as joystick and button are held
      nunchuk.update(); // check for data from nunchuk
      Serial.print("arming"); 
      Serial.print(nunchuk.analogY);
      Serial.print("|  |");
      Serial.println(nunchuk.cButton);
      digitalWrite(yellowLed1, HIGH);
      if (millis() - armStart >= 400){
        digitalWrite(yellowLed2, HIGH);
      }
      if (millis() - armStart >= 800){
        digitalWrite(yellowLed3, HIGH);
      }
      if (millis() - armStart >= 1200){
        Serial.println("Device armed");
        deviceArmed = true; // flag that the device has been armed
      }
    }
  }
}

void fadeRedLed(){
  analogWrite(redLed, brightness);
  if (millis() - fadeStart >= fadeInterval){
    brightness = brightness + fadeAmount;
    if (brightness <= 0 || brightness >= 255) {
      fadeAmount = -fadeAmount;
    }
    fadeStart = millis();
  }
}
