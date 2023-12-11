
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "stepper.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define MILLI_SEC_TO_SEC 1000

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    uint8_t pin_dir;
    uint8_t pin_pul;
    uint8_t pin_ena;               // Enable:LOW, Disable:HIGH      
    uint8_t dir;                   // 1:CW 0:CCW
    uint8_t rate;                  // Steps per second
    uint16_t counter;
    // for step-based control
    uint16_t des_steps;
    uint16_t curr_steps;
    // for condition-based control
    bool until;
    stepper_cond_f condition;
    bool cond_met;
} stepper_s;

typedef struct
{
    stepper_s steppers[STEPPER_COUNT];
} stepper_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

stepper_data_s stepper_data = 
{
    .steppers = 
    {
        [STEPPER_DEPOSITOR] =
        {
            .pin_dir = PA5,
            .pin_pul = PA6,
            .pin_ena = PA7
        }
    },
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void stepper_init(stepper_id_E stepper)
{
    pinMode(stepper_data.steppers[stepper].pin_dir, OUTPUT);
    pinMode(stepper_data.steppers[stepper].pin_pul, OUTPUT);
    pinMode(stepper_data.steppers[stepper].pin_ena, OUTPUT);
    digitalWrite(stepper_data.steppers[stepper].pin_ena, LOW);
    stepper_data.steppers[stepper].curr_steps = 0;
    stepper_data.steppers[stepper].des_steps = 0;
    stepper_data.steppers[stepper].condition = NULL;
    stepper_data.steppers[stepper].cond_met = true;
    stepper_data.steppers[stepper].until = false;
    stepper_data.steppers[stepper].rate = 1;
    stepper_data.steppers[stepper].dir = 1;
    stepper_data.steppers[stepper].counter = 0;
}

bool stepper_command(stepper_id_E stepper, uint16_t steps, uint8_t dir, uint16_t rate)
{
    bool ret = false;
    stepper_s* s = &stepper_data.steppers[stepper];
    if (s->curr_steps == 0)
    {
        s->des_steps = steps;
        s->rate = rate;
        s->dir = dir;
        s->until = false;
        s->condition = NULL;
        s->cond_met = true;
    }
    else if (s->curr_steps == s->des_steps)
    {
        s->curr_steps = 0;
        ret = true;
    }
    else
    {
        // do nothing
    }
    return ret;
}

bool stepper_commandUntil(stepper_id_E stepper, stepper_cond_f cond, uint8_t dir, uint16_t rate)
{
    bool ret = false;
    stepper_s* s = &stepper_data.steppers[stepper];
    if (cond() == false)
    {
        s->rate = rate;
        s->dir = dir;
        s->until = true;
        s->condition = cond;
        s->cond_met = false;
    }
    else if (s->cond_met)
    {
        s->cond_met = false;
        ret = true;
    }
    else
    {
        // do nothing
    }

    return ret;
}

void stepper_update(stepper_id_E stepper)
{
    stepper_s* s = &stepper_data.steppers[stepper];

    if (s->until == false)
    {
        if (s->counter >= MILLI_SEC_TO_SEC/s->rate)
        {
            digitalWrite(s->pin_dir, s->dir);
            delayMicroseconds(10); // Ensure direction is registered
            if (s->des_steps > s->curr_steps)
            {
                digitalWrite(s->pin_pul, HIGH);
                s->curr_steps++;
            }
            else
            {
                // reset current and desired steps
                s->curr_steps = 0;
                s->des_steps = 0;
            }
            s->counter = 0;
        }
        else
        {
            digitalWrite(s->pin_pul, LOW);
            s->counter++;
        }
    }
    else
    {
        if (s->counter >= MILLI_SEC_TO_SEC/s->rate)
        {
            digitalWrite(s->pin_dir, s->dir);
            delayMicroseconds(10); // Ensure direction is registered
            if (s->condition() == false)
            {
                digitalWrite(s->pin_pul, HIGH);
            }
            else
            {
                // set flag indicating condition was met
                s->cond_met = true;
            }
            s->counter = 0;
        }
        else
        {
            digitalWrite(s->pin_pul, LOW);
            s->counter++;
        }
    }
}

void stepper_cli_move(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "depositor") == 0)
    {   
        float steps = atoi(args[1]);
        uint8_t dir = atoi(args[2]);
        uint16_t rate = atoi(args[3]);
        stepper_command(STEPPER_DEPOSITOR, steps, dir, rate);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid servo");
    }
}

void stepper_cli_dump(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "depositor") == 0)
    {
        stepper_s* s = &stepper_data.steppers[STEPPER_DEPOSITOR];
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, 
                "{\"des_steps\":%d,\"curr_steps\":%d,\"dir\":%d,\"rate\":%d}", 
                s->des_steps, s->curr_steps, s->dir, s->rate);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid stepper");
    }
}
