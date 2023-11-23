
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "cli.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define BAUD_RATE (115200)

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/

typedef struct
{
    struct pt thread;
    HardwareSerial* connection;
} serial_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

static char run100ms(struct pt* thread);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/

static serial_data_s serial_data;

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static PT_THREAD(run100ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, scheduler_taskReleased(PERIOD_100ms, (uint8_t) CLI));
    // serial code goes here
    serial_data.connection->println(micros());
    PT_END(thread);
}

/*******************************************************************************
*            P U B L I C    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void serial_init(void)
{
    memset(&serial_data, 0, sizeof(serial_data_s));
    PT_INIT(&serial_data.thread);
    serial_data.connection = &Serial1;
    serial_data.connection->begin(BAUD_RATE);
}

void serial_run100ms(void)
{
    run100ms(&serial_data.thread);
}