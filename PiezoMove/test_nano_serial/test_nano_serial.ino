/*
  Software serial multple serial test

  Receives from the hardware serial, sends to software serial.
  Receives from software serial, sends to hardware serial.

  The circuit:
   RX is digital pin 2 (connect to TX of other device)
   TX is digital pin 3 (connect to RX of other device)

  Note:
  Not all pins on the Mega and Mega 2560 support change interrupts,
  so only the following can be used for RX:
  10, 11, 12, 13, 50, 51, 52, 53, 62, 63, 64, 65, 66, 67, 68, 69

  Not all pins on the Leonardo support change interrupts,
  so only the following can be used for RX:
  8, 9, 10, 11, 14 (MISO), 15 (SCK), 16 (MOSI).

  created back in the mists of time
  modified 25 May 2012
  by Tom Igoe
  based on Mikal Hart's example

  This example code is in the public domain.

*/
#include <SoftwareSerial.h>
bool isData;

String Comm = "";
SoftwareSerial mySerial(2, 3); // RX, TX

byte rx_byte = 0;        // stores received byte
String serialString;
int piezo_delay = 100; // delay before stopping the movement of the piezo in milliseconds


void setup()
{
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Native USB only
  }
  Serial.flush();
  
  // set the data rate for the SoftwareSerial port
  mySerial.begin(19200);
  mySerial.flush();
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  digitalWrite(4, LOW);
  digitalWrite(5, LOW);
  digitalWrite(6, LOW);
}


void loop() {
  while (Serial.available() > 0 ) {
    char value = Serial.read();
    Comm += value;
    if (value == '\n') {
      isData = true;
    }
  }
  if (isData) {
    isData = false;
    if (Comm.startsWith("mot")) {
      if (Comm.startsWith("mot1")) {
        digitalWrite(4, HIGH);
      }
      else if (Comm.startsWith("mot2")) {
        digitalWrite(6, HIGH);
      }
      else if (Comm.startsWith("mot3")) {
        digitalWrite(5, HIGH);
      }

      Serial.println("Waiting input");

      while (Serial.available() <= 0) {
        delay(1);
      }
      rx_byte = Serial.read();
      mySerial.write(rx_byte);

      bool is_step = true;
      for (int bits = 5; bits > 0; bits--) {
        if (rx_byte & (1 << bits)) {
          is_step = false;
        }
      }
      if (!(rx_byte & (1 << 0))) {
        is_step = false;
      }

      if (!(rx_byte & (1 << 7)) && is_step) { // In one of the directions it must make 2 steps in order to move one at a time
        delay(piezo_delay / 2);
        mySerial.write(rx_byte);
      }

      if (!is_step) {
        delay(piezo_delay / 2);
        rx_byte = 0;
        mySerial.write(rx_byte);
      }
      Serial.println("OK");
      digitalWrite(4, LOW);
      digitalWrite(5, LOW);
      digitalWrite(6, LOW);
    }
    else if (Comm.startsWith("IDN")) {
      Serial.println("Dispertech device 2.0-fluo");
    }
    Serial.flush();
    mySerial.flush();
    Comm = "";
  }
  delay(2);
}
