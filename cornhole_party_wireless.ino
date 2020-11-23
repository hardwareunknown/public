#include "Arduino.h" //standard library
#include "SPI.h" //allows communication with NRF24L01 via SPI
#include "RF24.h" //NRF24L01 function library
#include "SoftwareSerial.h" //allows pins to be set to serial (UART) communication, for DFPlayerMini
#include "DFRobotDFPlayerMini.h" //DFPlayerMini function library
#include "SimplyAtomic.h" //required for Atomic Blocks (to safely read volatile variables used in ISRs)

// combine celebration LEDperiod and song periods?


const byte vibrPin = 2; //vibration sensor, must be on 2 or 3 for hardware interrupt to work
const byte beamPin = 3; //break beam sensor, must be on 2 or 3 for hardware interrupt to work
const byte dfpRX = 4; //Arduino pin used for operating DFPlayer, connected to TX pin of player
const byte dfpTX = 5; //Arduino pin used for operating DFPlayer, connected to RX pin of player
const byte radioCE = 7; //SPI chip select for NRF24L01 
const byte radioCS = 8; //CE for NRF24L01, used to switch between TX and RX modes
const byte board_select = A2; //auto-sets reading/writing pipes of each board in void setup
const byte ledStrip = A4; //operates ledStrip power MOSFET
const byte ledRing = A5; //operates ledRing power MOSFET
/* celeb flags below are necessary because if the celebration function was placed within
 * a sensor activation if statement, once the program loops around the sensor will no
 * longer be activated for that loop, which causes the celebration to end prematurely. The 
 * celeb flags fix this by remaining constant between loops until the celebration ends.
 * 
 * Similar situation with sound flags.
 */
bool celeb1 = false; //flag for playing celebration sequence 1
bool celeb2 = false; //flag for playing celebration sequence 2
bool celeb3 = false; //flag for playing celebration sequence 3
bool sound1 = false; //flag for playing sound 1
bool sound2 = false; //flag for playing sound 2
bool sound3 = false; //flag for playing sound 3
volatile bool vibrActivated = false; // variable for reading the vibration sensor status
volatile bool beamActivated = false; // variable for reading the breakbeam status
unsigned long vibrWait = 0; //the next time when activation will be available, only used in ISR
unsigned long beamWait = 0; //the next time when activation will be available, only used in ISR
unsigned long vibrWaitDuration = 1000; //min length between activations, only used in ISR
unsigned long beamWaitDuration = 1000; //min length between activations, only used in ISR
unsigned long currentMillis = 0; //only read in ISR, not written to
volatile long vibrActivationMillisISR = 0; //tracks when the sensor was last activated within ISR
volatile long beamActivationMillisISR = 0; //tracks when the sensor was last activated within ISR
unsigned long vibrActivationMillisLoop = 0; //prevents data corruption when referencing activaiton time within void loop
unsigned long beamActivationMillisLoop = 0; //prevents data corruption when referencing activaiton time within void loop
unsigned long stopwatchStart = 0; //used for checking number of cornholes made in a short period
//unsigned long beamDelay = 1500; //length of time to wait for beam activation after vibration is sensed (otherwise, practically, only vibration works)
unsigned long vibrThreshold = 300; //minimum "strength" to allow celebration 1
const unsigned long cornholePeriod = 60000; //length of time for checking number of cornholes before resetting
int numCornholes = 0; //tracks the cornhole count for current period
const byte addresses[][6] = {"00001", "00002"}; //reading and writing pipes for NRF24L01
int sentMessage[1] = {000}; //wireless trigger message
int receivedMessage[1] = {000}; //wireless trigger message

RF24 radio(radioCE, radioCS);//create object called radio. specifying the CE and CSN pins to be used

SoftwareSerial dfSerial(dfpRX, dfpTX); //enable communicaiton with DFPlayerMini
DFRobotDFPlayerMini myDFPlayer; //create DFPlayer object

void setup(){
  delay(1000); //might be needed to fix clone required reset issue, uncomment if board needs to be reset to work after power cycle
  dfSerial.begin(9600);
  Serial.begin(115200);
  delay(1000); 
  Serial.println(F("Initializing DFPlayer ... (May take 3~5 seconds)"));
  if (!myDFPlayer.begin(dfSerial)) {  //Use softwareSerial to communicate with mp3.
    Serial.println(F("Unable to begin:"));
    Serial.println(F("1.Please recheck the connection!"));
    Serial.println(F("2.Please insert the SD card!"));
    while(true);
  }

  //  ----Adjust player settings----
  myDFPlayer.setTimeOut(500); //set serial communictaion time out 500ms
  myDFPlayer.volume(20);  //set volume value (0~30).
  myDFPlayer.EQ(DFPLAYER_EQ_NORMAL); // Default EQ
  myDFPlayer.outputDevice(DFPLAYER_DEVICE_SD);  //Select SD card to pull files from
  myDFPlayer.enableDAC();  //enable On-chip DAC (allows use of amplifier board)
  myDFPlayer.outputSetting(true, 15); //output setting, enable the output and set the gain to 15
  Serial.println(F("DFPlayer Mini online."));
  
  delay(1000);

  pinMode(board_select, INPUT);
  pinMode(vibrPin, INPUT);
  pinMode(beamPin, INPUT);
  pinMode(ledRing, OUTPUT);
  pinMode(ledStrip, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(vibrPin), vibrISR, RISING);
  attachInterrupt(digitalPinToInterrupt(beamPin), beamISR, RISING);
  digitalWrite(ledRing, LOW);
  digitalWrite(ledStrip, LOW);
  digitalWrite(board_select, HIGH); //HIGH to start, pulled low on receiver
  delay(100); //stabilize board_select pin at HIGH
  
  radio.begin();
  if (digitalRead(board_select)){ //if HIGH, evaluates true... selecting board as transmitter
    radio.openWritingPipe(addresses[1]); // 00002
    radio.openReadingPipe(1, addresses[0]); // 00001
  }
  else{ //pulled LOW, evaluates false... selecting board as receiver
    radio.openWritingPipe(addresses[0]); // 00001
    radio.openReadingPipe(1, addresses[1]); // 00002
  }
  
  radio.setPALevel(RF24_PA_MAX); //set RF power output to minimum RF24_PA_MIN (change to RF24_PA_MAX if required)
  radio.setDataRate(RF24_2MBPS); //set datarate to 2mbps
  radio.setChannel(110); //set frequency to channel 110

  radio.startListening();
  Serial.println(F("RF24 online."));
  
  ready_light();
  digitalWrite(ledRing, HIGH); //turn the LED ring constant-on
  digitalWrite(ledStrip, HIGH); //turn the LED strip constant-on
  Serial.println(F("Cornhole board ready."));
}

void loop(){
  currentMillis = millis(); //get the current time in ms
  static long vibrMeasurement = 0; //store most recent value of vibration sensed
  /* Atomic Block used in order to ensure the ISR millis value of either sensor
   * is not corrupted when trying to read it in the loop. After testing, this seems very 
   * unlikely to happen. However, it is theoretically possible. Likely it would correct 
   * itself on the next sensor activation, but this was left in for good practice.
   */
   
  ATOMIC(){ //transfer volatile value to safe variable for later reference
  vibrActivationMillisLoop = vibrActivationMillisISR;
  beamActivationMillisLoop = beamActivationMillisISR;
  }
  
  if (vibrActivated){ //if vibration sensor was activated (the bag hit the board)
    vibrMeasurement = vibration();
    Serial.println(vibrMeasurement);
    if (vibrMeasurement >= vibrThreshold){
      vibrActivated = false; //reset sensor for next activation
      celeb1 = true; //flag to begin the celebration sequence
      sentMessage[0] = 111; //trigger to play sound 1
      radio.stopListening();
      radio.write(&sentMessage, sizeof(sentMessage)); //send message
      radio.startListening();
//      Serial.println("Sent 111");
    }
    else{
      vibrActivated = false; //reset sensor for next activation
    }
  }
  if (beamActivated){ //if beam was activated (the bag went through the hole)
    vibrActivated = false; //reset sensor for next activation
    beamActivated = false; //reset sensor for next activation
    if (currentMillis - stopwatchStart > cornholePeriod){ //reset number of cornholes if window of time has elapsed
      numCornholes = 0;
    }
    if (numCornholes < 1){
      if (numCornholes == 0){
        stopwatchStart = currentMillis; //begin the cornhole check period
      }
      numCornholes++;
      celeb1 = false; //cancel prior celebration sequence
      celeb2 = true; //flag to begin the celebration sequence
      sentMessage[0] = 222; //trigger to play sound 2 on opposite board
      radio.stopListening();
      radio.write(&sentMessage, sizeof(sentMessage)); //send message
      radio.startListening();
      Serial.println("Sent 222");
    }
    else{ //executes on 5th cornhole
      numCornholes = 0; //reset cornhole count
      celeb1 = false; //cancel prior celebration sequence
      celeb2 = false; //cancel prior celebration sequence
      celeb3 = true; //flag to begin the celebration sequence
      sentMessage[0] = 333; //trigger to play sound 3 on opposite board
      radio.stopListening();
      radio.write(&sentMessage, sizeof(sentMessage)); //send message
      radio.startListening();
      Serial.println("Sent 333");
    }
  }
  if (celeb1){
    celebration1(currentMillis);
  }
  else if (celeb2){
    celebration2(currentMillis);
  }
  else if (celeb3){
    celebration3(currentMillis);
  }
  if (radio.available()){ //if data has been sent over
    radio.read(&receivedMessage, sizeof(receivedMessage));
  }
  if (receivedMessage[0] == 111){
    playFirst();
    Serial.println("Received 111");
    receivedMessage[0] = 000; //reset opposite board sound trigger
  }
  else if (receivedMessage[0] == 222){
    playSecond();
    Serial.println("Received 222");
    receivedMessage[0] = 000; //reset opposite board sound trigger
  }
  else if (receivedMessage[0] == 333){
    playThird();
    Serial.println("Received 333");
    receivedMessage[0] = 000; //reset opposite board sound trigger
  }
}

void vibrISR(){
  if (currentMillis >= vibrWait){ //if wait time has elapsed (to prevent repeat activations)
    vibrWait = currentMillis + vibrWaitDuration; //reset the wait time
    vibrActivationMillisISR = currentMillis; //save the time sensor was activated
    vibrActivated = true; //flag that the sensor has been activated
  }
}

void beamISR(){
  if (currentMillis >= beamWait){ //if wait time has elapsed (to prevent repeat activations)
    beamWait = currentMillis + beamWaitDuration; //reset the wait time
    beamActivationMillisISR = currentMillis; //save the time sensor was activated
    beamActivated = true; //flag that the sensor has been activated
  }
}

void celebration1(unsigned long currentMillis)
{
  const unsigned long ledPeriod = 1500; //total time the celebration sequence LED will be active
  const unsigned int onTime = 350; //time LED will remain on per blink
  const unsigned int offTime = 200; //time LED will remain off per blink
  static unsigned long previousLedMillis = millis(); //tracks the last time event fired
  static int interval = onTime; //initialize interval
  static byte ledState = HIGH; //used to track if LED should be on or off
  static bool soundPrimed = true; //flag that the sound can be played

  if (currentMillis - vibrActivationMillisLoop <= ledPeriod) //time that LED should be flashing hasn't elapsed
  {
    digitalWrite(ledRing, ledState); //turn the LED on or off
    digitalWrite(ledStrip, ledState); //turn the LED strip on or off
    if (soundPrimed)
    {
      playFirst();
      soundPrimed = false; //flag that the sound has been played (preventing repeats)
    }
    if (currentMillis - previousLedMillis >= interval)
    {
      if (ledState == HIGH)
      {
        interval = offTime;
      }
      else
      {
        interval = onTime;
      }
      ledState = !(ledState); //toggle LED state
      previousLedMillis = currentMillis; //savee the current time to compare later
    }
  }    
  else //time that LED should be flashing HAS elapsed
  {
    digitalWrite(ledRing, HIGH); //turn the LED ring constant-on
    digitalWrite(ledStrip, HIGH); //turn the LED strip constant-on
    celeb1 = false; //flag the celebration sequence as complete
    soundPrimed = true; //flag the sound to be played again next activation
  }
}

void celebration2(unsigned long currentMillis)
{
  const unsigned long ledPeriod = 6500; //total time the celebration sequence LED will be active
  const unsigned int onTime = 500; //time LED will remain on per blink
  const unsigned int offTime = 500; //time LED will remain off per blink
  static unsigned long previousLedMillis = millis(); //tracks the last time event fired
  static int interval = onTime; //initialize interval
  static byte ledState = HIGH; //used to track if LED should be on or off
  static bool soundPrimed = true; //flag that the sound can be played

  if (currentMillis - beamActivationMillisLoop <= ledPeriod) //time that LED should be flashing hasn't elapsed
  {
    digitalWrite(ledRing, ledState); //turn the LED on or off
    digitalWrite(ledStrip, ledState); //turn the LED strip on or off
    if (soundPrimed)
    {
      playSecond();
      soundPrimed = false; //flag that the sound has been played (preventing repeats)
    }
    if (currentMillis - previousLedMillis >= interval)
    {
      if (ledState == HIGH)
      {
        interval = offTime;
      }
      else
      {
        interval = onTime;
      }
      ledState = !(ledState); //toggle LED state
      previousLedMillis = currentMillis; //savee the current time to compare later
    }
  }    
  else //time that LED should be flashing HAS elapsed
  {
    digitalWrite(ledRing, HIGH); //turn the LED ring constant-on
    digitalWrite(ledStrip, HIGH); //turn the LED strip constant-
    celeb2 = false; //flag the celebration sequence as complete
    soundPrimed = true; //flag the sound to be played again next activation
  }
}

void celebration3(unsigned long currentMillis)
{
  const unsigned long ledPeriod = 5800; //total time the celebration sequence LED will be active
  const unsigned int onTime = 750; //time LED will remain on per blink
  const unsigned int offTime = 300; //time LED will remain off per blink
  static unsigned long previousLedMillis = millis(); //tracks the last time event fired
  static int interval = onTime; //initialize interval
  static byte ledState = HIGH; //used to track if LED should be on or off
  static bool soundPrimed = true; //flag that the sound can be played

  if (currentMillis - beamActivationMillisLoop <= ledPeriod) //time that LED should be flashing hasn't elapsed
  {
    digitalWrite(ledRing, ledState); //turn the LED ring on or off
    digitalWrite(ledStrip, ledState); //turn the LED strip on or off
    if (soundPrimed)
    {
      playThird();
      soundPrimed = false; //flag that the sound has been played (preventing repeats)
    }
    if (currentMillis - previousLedMillis >= interval)
    {
      if (ledState == HIGH)
      {
        interval = offTime;
      }
      else
      {
        interval = onTime;
      }
      ledState = !(ledState); //toggle LED state
      previousLedMillis = currentMillis; //savee the current time to compare later
    }
  }    
  else //time that LED should be flashing HAS elapsed
  {
    digitalWrite(ledRing, HIGH); //turn the LED ring constant-on
    digitalWrite(ledStrip, HIGH); //turn the LED strip constant-on
    celeb3 = false; //flag the celebration sequence as complete
    soundPrimed = true; //flag the sound to be played again next activation
  }
}

void playFirst() //plays sound file 1
{
  myDFPlayer.playLargeFolder(1, 1);  //play specific mp3 in SD:/15/004.mp3; Folder Name(1~99); File Name(1~255)
//  delay(100);
}

void playSecond() //plays sound file 2
{
  myDFPlayer.playLargeFolder(1, 2);
//  delay(100);
}

void playThird() //plays sound file 3
{
  myDFPlayer.playLargeFolder(1, 3);
//  delay(100);
}

long vibration(){
  long vibrMeasurement = pulseIn(vibrPin, HIGH);
  return vibrMeasurement;
}

void ready_light(){
  for (int i = 0; i < 2; i++){
    digitalWrite(ledRing, HIGH);
    digitalWrite(ledStrip, HIGH);
    delay(100);
    digitalWrite(ledRing, LOW);
    digitalWrite(ledStrip, LOW);
    delay(100);
  }
}
