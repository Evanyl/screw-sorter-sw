
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

#ifdef DEPOSIT
void switch_boxes_ISR(void);
#elif ISOLATE_CLASSIFY
void switch_depositor_ISR(void);
void switch_arm_bottom_ISR(void);
void switch_arm_ISR(void);
void switch_lights_ISR(void);
void switch_sidelight_ISR(void);
#else
#endif

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

switch_data_S switch_data =
{
    .switches = 
    {
#ifdef DEPOSIT
        [SWITCH_BOXES] = 
        {
            .activated = false,
            .pin = PB15,
            .ISR = switch_boxes_ISR
        }
#elif ISOLATE_CLASSIFY
        [SWITCH_DEPOSITOR] =
        {
            .activated = false, 
            .pin = PC14, // active LOW switch
            .ISR = switch_depositor_ISR
        },
        [SWITCH_ARM] = 
        {
            .activated = false,
            .pin = PC15, // active LOW switch
            .ISR = switch_arm_ISR
        },
        [SWITCH_SIDELIGHT] = 
        {
            .activated = false,
            .pin = PC13,
            .ISR = switch_sidelight_ISR
        }
#else
        // nothing
#endif
    }
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

#ifdef DEPOSIT
void switch_boxes_ISR(void)
{
    switch_S* sw = &switch_data.switches[SWITCH_BOXES];
    sw->activated = true ^ sw->activated;
}
#elif ISOLATE_CLASSIFY
void switch_depositor_ISR(void)
{
    switch_S* sw = &switch_data.switches[SWITCH_DEPOSITOR];
    sw->activated = true ^ sw->activated;
}

void switch_arm_ISR(void)
{
    switch_S* sw = &switch_data.switches[SWITCH_ARM];
    sw->activated = true ^ sw->activated;
}

void switch_sidelight_ISR(void)
{
    switch_S* sw = &switch_data.switches[SWITCH_SIDELIGHT];
    sw->activated = true ^ sw->activated;
}
#else
// nothing
#endif

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void switch_init(switch_id_E switch_id)
{
    switch_S* sw = &switch_data.switches[switch_id];
    pinMode(sw->pin, INPUT_PULLUP);
    delay(500);
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
    switch_S* sw = NULL;
#ifdef DEPOSIT
    if (strcmp(args[0], "boxes") == 0)
    {   
        sw = &switch_data.switches[SWITCH_BOXES];
    }
#elif ISOLATE_CLASSIFY
    if (strcmp(args[0], "depositor") == 0)
    {   
        sw = &switch_data.switches[SWITCH_DEPOSITOR];
    }
    else if (strcmp(args[0], "arm") == 0)
    {
        sw = &switch_data.switches[SWITCH_ARM];
    }
    else if (strcmp(args[0], "sidelight") == 0)
    {
        sw = &switch_data.switches[SWITCH_SIDELIGHT];
    }
#else
    // nothing
#endif

    if (sw == NULL)
    {
        serial_send_nl(PORT_COMPUTER, "invalid switch");
    }
    else
    {
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, 
                "{\"activated\":%d}", 
                (uint8_t) sw->activated);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
}
