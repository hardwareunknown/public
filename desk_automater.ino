const int up_button = 3; //button on custom PCB
const int down_button = 2; //button on custom PCB
const int stand_button = 5; //button on custom PCB
const int sit_button = 4; //button on custom PCB
const int down_signal = 7; //sent to the OEM desk PCB to move the desk
const int up_signal = 8; //sent to the OEM desk PCB to move the desk
unsigned long stand_delay = 13000; //length of time desk moves when switching to stand mode
unsigned long sit_delay = 12800; //length of time desk moves when switching to sit mode

//track if buttons are currently pressed or not
int up_button_state = 0;
int down_button_state = 0;
int stand_button_state = 0;
int sit_button_state = 0;

//initialize buttons as inputs
void setup() {
  pinMode(up_button, INPUT);
  pinMode(down_button, INPUT);
  pinMode(stand_button, INPUT);
  pinMode(sit_button, INPUT);
}

void loop() {
  //check if buttons are pressed
  up_button_state = digitalRead(up_button);
  down_button_state = digitalRead(down_button);
  stand_button_state = digitalRead(stand_button);
  sit_button_state = digitalRead(sit_button);

  //if button is pressed, initiate corresponding desk movement

  //move desk up as long as button is held
  if (up_button_state == HIGH) {
    digitalWrite(up_signal, HIGH); 
  } 

  //move desk down as long as button is held
  else if (down_button_state == HIGH) {
    digitalWrite(down_signal, HIGH);
  }

  //move desk up automatically for designated length of time
  else if (stand_button_state == HIGH) {
    digitalWrite(up_signal, HIGH);
    delay(stand_delay);
    digitalWrite(up_signal, LOW);
  }

  //move desk down automatically for designated length of time
  else if (sit_button_state == HIGH) {
    digitalWrite(down_signal, HIGH);
    delay(sit_delay);
    digitalWrite(down_signal, LOW);
  }

  //keep desk in place when no buttons are pressed
  else {
    digitalWrite(up_signal, LOW);
    digitalWrite(down_signal, LOW);
  }
  
}
