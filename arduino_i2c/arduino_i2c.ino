//
// I2C library: http://dsscircuits.com/articles/arduino-i2c-master-library
//
// author: roychan@
//
// 1. Read <NUM> of bytes from register <REG> of device <DEV>, NUM=1 to 32 max.
//      r<DEV in HEX><REG in HEX><NUM in HEX>\n
//    Examples:
//      Read 16 byte start from registe 0x00 of device 0x0C:
//      r0CF00F
// 2. Write single byte to register <REG> of device <DEV>
//      w<DEV in HEX><REG in HEX><VALUE in HEX>\n
//    Example (read single byte 0x55 to registe 0x41 of device 0x0C):
//      w0C4155
// 3. Read <NUM> of bytes from device <DEV>
//      R<DEV><NUM>\n
// 4. Write <NUM> of bytes to register <REG> of device <DEV>
//      W<DEV><REG><NUM><VALUE>...<VALUE>\n
//
#include <I2C.h>

#define VERSION "FPDL_DISP_ITL_1.1.1"
#define RESET_PIN 14  //Reset pin number
#define CHG 2

#define msgr(p,m) Serial.print(p); Serial.println(m,HEX);
#define msg(s) Serial.print(s)
#define msgh(s) Serial.print(s,HEX)
#define msgh0(s) Serial.println(s,HEX)
#define msg0(s) Serial.println(s)

// D2: DES_GPIO0, CHG, interrupt (input)
// D3: DES_GPIO1, LED Driver fault (input)
// D4: DES_GPIO2, LED Driver PWM (output)
// D5: DES_GPIO3, Touch_Reset_L (output)
// D6: SER_GPIO5_REG (input) - not use
// D7: SER_GPIO6_REG (input) - not use
// D8: SER_GPIO7_REG (input) - not use
// D9: SER_GPIO8_REG (input) - not use
// D10: SER_INTB (input) - not use
// A0: SER_PDB, high: power up, low: power down (ouput)
// A3: Local load switch, 12V_Display Enable, active low (output)

volatile byte touch_output=0;
byte retcode=0;

uint8_t pin[] = {2, 3,4,5,6, 7,8,9,10, A0,A3};
uint8_t pin_dir[] = {INPUT,  INPUT,OUTPUT,OUTPUT,INPUT,  INPUT,INPUT,INPUT,INPUT,  OUTPUT,OUTPUT};
uint8_t T100[] = { 0x0C, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 
                   0x20, 0x2A, 0x00, 0x00, 0xFF, 0x0F, 0x00, 0x00, 0x00, 0x00, 
                   0x00, 0x14, 0x2A, 0x00, 0x00, 0xFF, 0x0F, 0x00, 0x00, 0x0B, 
                   0x00, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
uint8_t T7[] = { 0x09, 0xFF, 0xFF, 0x32, 0x02, 0x00, 0x00, 0x00 };
uint8_t TT[] = { 0x0C, 0,0,0,0,0, 0,0,0,0,0, 0,0,0 };

void setup() {

  for (int i=0; i<sizeof(pin); i++) {
    pinMode(pin[i], pin_dir[i]);
  }
  digitalWrite(5, HIGH);
  digitalWrite(A0, HIGH); //Power up Serializer
  digitalWrite(A3, LOW);  //Turn on 12V for display module
  
  Serial.begin(115200); 
  I2c.begin();
  I2c.timeOut(500);
  I2c.setSpeed(0);  //0:STD, 1:400kHz
  attachInterrupt(digitalPinToInterrupt(CHG), touch_isr, FALLING);


  delay(100);
  // SER init
  I2c.write(0x0c, 0x4f, 0x01);
  I2c.write(0x0c, 0x0d, 0x25);
  I2c.write(0x0c, 0x0e, 0x35);
  I2c.write(0x0c, 0x0f, 0x03);
  I2c.write(0x0c, 0x03, 0xda);
  I2c.write(0x0c, 0x17, 0x9e);
  I2c.write(0x0c, 0x54, 0xa8);
  I2c.write(0x0c, 0x54, 0x28);

  delay(100);
 
//  // DES init
  I2c.write(0x3b, 0x02, 0xF0);
  delay(100);
  I2c.write(0x3b, 0x1d, 0x23);  
  I2c.write(0x3b, 0x1e, 0x53);
  I2c.write(0x3b, 0x1f, 0x05);  
  I2c.write(0x3b, 0x20, 0x13);
  I2c.write(0x3b, 0x21, 0x99);

  delay(500);
   
//  // LED init
  I2c.write(0x2d, 0x0C, 0x10);
  I2c.write(0x2d, 0x0, 0x33);
  I2c.write(0x2d, 0x1, 0x33);
  I2c.write(0x2d, 0xa, 0x01);
  I2c.write(0x2d, 0xb, 0x99);
  

  I2c.write(0x4B, 0x87, 0x06);
  retcode = I2c.read(0x4B,11); 
  while (I2c.available()) {
      I2c.receive();
  }

// TOUCH init
  I2c.write(0x4B, 0x2F, T100, 60);
  I2c.write(0x4B, 0x6A, TT, 14);  
  I2c.write(0x4B, 0xC1, T7, 8);

}

void i2c_read(byte dev, byte reg, byte num) {
  
  retcode = I2c.read(dev,reg,num); 
  
  if (retcode) {
    msgr("-",retcode);
    return;
  }
  
  while (I2c.available()) {
    msgh(I2c.receive());
    msg(" ");
  }
  msg0();
  
  return;
}

void i2c_read_many(byte dev, byte num) {
  
  retcode = I2c.read(dev, num); 
  
  if (retcode) {
    msgr("-",retcode);
    return;
  }
  
  while (I2c.available()) {
    msgh(I2c.receive());
    msg(" ");
  }
  msg0();
  
  return;
}

void i2c_write(byte dev, byte reg, byte val) {
  retcode = I2c.write(dev,reg,val); 
  if (retcode) {
    msgr("-", retcode);
  }
  else {
    msg0("OK");
  }
}

void i2c_write_many(byte dev, byte reg, byte num, int8_t *val) {
  
  retcode = I2c.write(dev,reg,val,num); 
  if (retcode) {
    msgr("-", retcode);
  }
  else {
    msg0("OK");
  }
}

//int n=0;
void touch_isr() {
  if (digitalRead(CHG)==1) {
    return;
  }
  
  if (touch_output==1) {
    I2c.write(0x4B, 0x87, 0x06);
    retcode = I2c.read(0x4B,11); 
    
    if (retcode) {
      msgr("-",retcode);
      return;
    }

    msg("T5 ");
    while (I2c.available()) {
      msgh(I2c.receive());
      msg(" ");
    }
    msg0();
  }
}

#define LINE_BUF_SIZE 141     //Maximum input string length

char line[LINE_BUF_SIZE];
byte line_bytes[70];
byte line_len;
char byte1[3];

void loop() {
  String line_string;
  unsigned long number = strtoul(&line[1], nullptr, 16);

  while(!Serial.available());
  line_string = Serial.readStringUntil(13);
  line_string.toCharArray(line, LINE_BUF_SIZE);
  line_len = line_string.length();

  // String to array of bytes:
  for(int i=1; i<line_len; i=i+2) {
    memcpy(byte1, &line[i], 2);
    byte1[2]='\0';    
    number = strtoul(byte1, nullptr, 16);
    line_bytes[(i-1)/2]=number;
  }

  // READ/WRITE Command
  if (line[0] == 'r') {
    if (line_bytes[2]>32)  // <NUM>
      return;
    i2c_read(line_bytes[0],line_bytes[1],line_bytes[2]);
  }
  
  else if (line[0]=='w') {
    i2c_write(line_bytes[0], line_bytes[1], line_bytes[2]);
  }

  //Ping response
  else if (line[0]=='p') {
    msg0(VERSION);
  }
  
  // 3. Read <NUM> of bytes from device <DEV>
  //    R<DEV><NUM>\n

  if (line[0] == 'R') {
    i2c_read_many(line_bytes[0], line_bytes[1]);
  }

  // 4. Write <NUM> of bytes to register <REG> of device <DEV>
  //    W<DEV><REG><NUM><VALUE>...<VALUE>\n  
  else if (line[0]=='W') {
    i2c_write_many(line_bytes[0], line_bytes[1], line_bytes[2], &line_bytes[3]);
  }
  // I2C SCAN Command
  else if (line[0] == 's') {
    I2c.scan();
    return;
  }
  // GPIO commands
  else if (line[0] == 'I') {
    if (line_bytes[0]<=sizeof(pin)) {
      msg(pin_dir[line_bytes[0]]);
      msgr(':', digitalRead(pin[line_bytes[0]]));
    }
  }
  else if (line[0] == 'O') {
    if (line_bytes[0]<=sizeof(pin)) {
      
      msg(pin[line_bytes[0]]);
      
      if (line_bytes[1]>0) {
        digitalWrite(pin[line_bytes[0]], HIGH);
      }
      else {
        digitalWrite(pin[line_bytes[0]], LOW);        
      }
    }
  }  

  // Enable touch data reading
  else if (line[0] == 't') {
    if (line[1] == '1') {
      touch_output = 1;
      retcode = I2c.read(0x4B,11); 
      while (I2c.available()) {
        msgh(I2c.receive());
      }
    }
    else {
      touch_output = 0;
    }
  }

  else if (line[0]=='?') {
    msgr("touch_output=", touch_output);
  }

  memset(line, 1, LINE_BUF_SIZE);  
}
