
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "switch.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    volatile bool activated;
    uint8_t pin;
    void (*ISR) (void);
} switch_S;

typedef struct
{
    switch_S switches[SWITCH_COUNT];
} switch_data_S;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/

void switch_depositor_ISR(void);
void switch_arm_bottom_ISR(void);
void switch_arm_top_ISR(void);
void switch_lights_ISR(void);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

switch_data_S switch_data =
{
    .switches = 
    {
        [SWITCH_DEPOSITOR] =
        {
            .activated = false, 
            .pin = PB12, // ACTIVE LOW switch
            .ISR = switch_depositor_ISR
        }
    }
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

void switch_depositor_ISR(void)
{
    switch_S* sw = &switch_data.switches[SWITCH_DEPOSITOR];
    sw->activated = true ^ sw->activated;
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void switch_init(switch_id_E switch_id)
{
    switch_S* sw = &switch_data.switches[switch_id];
    pinMode(sw->pin, INPUT_PULLUP);
    if (digitalRead(sw->pin) == HIGH)
    {
        sw->activated = false;
    }
    else
    {
        sw->activated = true;
    }
    attachInterrupt(digitalPinToInterrupt(sw->pin), sw->ISR, CHANGE);
}

bool switch_state(switch_id_E switch_id)
{
    return switch_data.switches[switch_id].activated;
}

void switch_cli_state(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "depositor") == 0)
    {   
        switch_S* sw = &switch_data.switches[SWITCH_DEPOSITOR];
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, 
                "{\"activated\":%d}", 
                (uint8_t) sw->activated);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid switch");
    }
}
