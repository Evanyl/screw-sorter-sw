
#ifndef DEV_SERIAL
#define DEV_SERIAL

/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include <Arduino.h>

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define SERIAL_MESSAGE_SIZE (100)

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/

typedef enum {
    PORT_COMPUTER,
    PORT_RPI,
    PORT_COUNT
} serial_port_E;

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void serial_init(serial_port_E port);
bool serial_available(serial_port_E port);
char serial_readByte(serial_port_E port);
bool serial_handleByte(serial_port_E port, char byte);
void serial_send_nl(serial_port_E port, char* line);
void serial_send(serial_port_E port, char* line);
void serial_echo(serial_port_E port);
void serial_getLine(serial_port_E port, char* lineBuffer);

#endif // DEV_SERIAL 
