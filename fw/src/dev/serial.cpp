
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BAUD_RATE  (115200)
#define SERIAL_EOL '\n'
#define SERIAL_EOS '\0'

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/

typedef struct
{
    uint8_t index;
    char line[SERIAL_MESSAGE_SIZE];
} port_buffer_s;

typedef struct
{
    port_buffer_s port_buffer;
    HardwareSerial* connection;
} port_data_s;

typedef struct
{
    port_data_s ports[PORT_COUNT];
} serial_data_s;

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/

static serial_data_s serial_data = 
{
    .ports = 
    {
        [PORT_COMPUTER] = 
        {
            .port_buffer = 
            {
                .index = 0
            },
            .connection = &Serial1
        },
        [PORT_RPI] = 
        {
            .port_buffer = 
            {
                .index = 0
            },
            .connection = &Serial2
        }
    }
};

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/

void serial_init(serial_port_E port)
{
    serial_data.ports[port].connection->begin(BAUD_RATE);
}

bool serial_available(serial_port_E port)
{
    return serial_data.ports[port].connection->available() > 0;
}

char serial_readByte(serial_port_E port)
{
    return serial_data.ports[port].connection->read();
}

bool serial_handleByte(serial_port_E port, char byte)
{
    port_data_s* p = &serial_data.ports[port];
    bool ret = false;
    if (byte == SERIAL_EOL)
    {
        p->port_buffer.line[p->port_buffer.index] = SERIAL_EOS;
        p->port_buffer.index = 0;
        ret = true;
    }
    else
    {
        p->port_buffer.line[p->port_buffer.index++] = byte;
    }
    return ret;
}

void serial_send(serial_port_E port, char* line)
{
    serial_data.ports[port].connection->println(line);
}

void serial_echo(serial_port_E port)
{
    port_data_s* p = &serial_data.ports[port];
    uint8_t i = 0;
    while (p->port_buffer.line[i] != SERIAL_EOS)
    {
        p->connection->print(p->port_buffer.line[i]);
        i++;
    }
    p->connection->print(SERIAL_EOL);
}

void serial_getLine(serial_port_E port, char* lineBuffer)
{
    memcpy(&serial_data.ports[port].port_buffer.line, lineBuffer, 
           sizeof(serial_data.ports[port].port_buffer.line));
}