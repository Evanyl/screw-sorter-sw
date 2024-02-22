/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "core_comms.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct 
{
    struct pt thread;
} core_comms_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

static char run100ms(struct pt* thread);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

core_comms_s core_comms_data;

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 


static PT_THREAD(run100ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, 
                  scheduler_taskReleased(PERIOD_100ms, (uint8_t) CORE_COMMS));

    // wait until there is serial data
    while (serial_available(PORT_RPI))
    {
        if (serial_handleByte(PORT_RPI, serial_readByte(PORT_RPI)))
        {
            serial_echo(PORT_RPI);
            break;
        }
    }

    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void core_comms_init(void)
{
    PT_INIT(&core_comms_data.thread);
    serial_init(PORT_RPI);
}

void core_comms_run100ms(void)
{
    run100ms(&core_comms_data.thread);
}

system_state_E core_comms_getDesiredState(void)
{
    return SYSTEM_STATE_IDLE;
}
