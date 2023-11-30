
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "stepper.h"

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
    uint8_t pin_ena;
    uint16_t des_steps;
    uint16_t curr_steps;
    uint8_t dir; // 1:CW 0:CCW
    uint8_t rate;
    uint16_t counter;
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
    digitalWrite(stepper_data.steppers[stepper].pin_ena, HIGH); // check this
    stepper_data.steppers[stepper].curr_steps = 0;
    stepper_data.steppers[stepper].des_steps = 0;
    stepper_data.steppers[stepper].rate = 0;
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

void stepper_update(stepper_id_E stepper)
{
    stepper_s* s = &stepper_data.steppers[stepper];
    if (s->counter >= MILLI_SEC_TO_SEC/s->rate)
    {
        digitalWrite(s->pin_dir, s->dir);
        delayMicroseconds(10); // Ensure direction is registered
        if (s->des_steps >= s->curr_steps)
        {
            digitalWrite(s->pin_pul, HIGH);
        }
        else
        {
            // do nothing, desired angle has been acheived
        }
        s->counter = 0;
    }
    else
    {
        digitalWrite(s->pin_pul, LOW);
        s->counter++;
    }
}
