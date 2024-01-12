
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

typedef enum
{
    STEPPER_MODE_STEPS,
    STEPPER_MODE_CONDITION,
    STEPPER_MODE_COUNT
} stepper_mode_E;

typedef struct
{
    uint8_t pin_dir;
    uint8_t pin_pul;
    uint8_t pin_ena;               // Enable:LOW, Disable:HIGH      
    uint8_t dir;                   // 1:CW 0:CCW (top-down, imaging plane left)
    uint8_t rate;                  // Steps per second
    uint16_t counter;
    stepper_mode_E mode;
    // for step-based control
    uint16_t des_steps;
    uint16_t curr_steps;
    uint16_t ramp_steps;
    uint16_t ramp_start;
    uint8_t curr_rate;
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
            .pin_dir = PB7,
            .pin_pul = PB8,
            .pin_ena = PB6
        },
        [STEPPER_PLANE] =
        {
            .pin_dir = PB4,
            .pin_pul = PB5,
            .pin_ena = PB3
        },
        [STEPPER_ARM] = 
        {
            .pin_dir = PA11,
            .pin_pul = PA12,
            .pin_ena = PA15
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

bool stepper_command(stepper_id_E stepper, uint16_t steps, uint8_t dir, 
                     uint16_t rate, uint16_t ramp, uint8_t ramp_start)
{
    bool ret = false;
    stepper_s* s = &stepper_data.steppers[stepper];
    if (s->curr_steps == 0)
    {
        s->des_steps = steps;
        s->rate = rate;
        s->ramp_start = ramp_start;
        if (ramp == 0)
        {
            s->curr_rate = rate;
        }
        else
        {
            s->curr_rate = ramp_start;
        }
        s->dir = dir;
        s->mode = STEPPER_MODE_STEPS;
        s->ramp_steps = ramp;
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

bool stepper_commandUntil(stepper_id_E stepper, stepper_cond_f cond, 
                          uint8_t dir, uint16_t rate)
{
    bool ret = false;
    stepper_s* s = &stepper_data.steppers[stepper];
    if (cond() == false)
    {
        s->rate = rate;
        s->dir = dir;
        s->mode = STEPPER_MODE_CONDITION;
        s->condition = cond;
        s->cond_met = false;
    }
    else if (s->cond_met)
    {
        s->condition = NULL;
        s->cond_met = false;
        s->until = STEPPER_MODE_STEPS;
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

    switch (s->mode)
    {
        case STEPPER_MODE_STEPS:
            if (s->counter >= MILLI_SEC_TO_SEC/s->curr_rate)
            {
                digitalWrite(s->pin_dir, s->dir);
                delayMicroseconds(10); // Ensure direction is registered
                if (s->des_steps > s->curr_steps)
                {   
                    uint8_t delta_rate = 0;
                    if (s->ramp_steps > 0)
                    {
                        delta_rate = s->rate / s->ramp_steps;
                    }

                    if (s->curr_steps < s->ramp_steps && delta_rate > 0)
                    {
                        if (s->rate - s->curr_rate < delta_rate)
                        {
                            s->curr_rate = s->rate;
                        }
                        else
                        {
                            s->curr_rate += delta_rate;
                        }
                    }
                    else if (s->des_steps - s->ramp_steps < s->curr_steps && 
                             delta_rate > 0)
                    {
                        if (s->curr_rate - s->ramp_start < delta_rate)
                        {
                            s->curr_rate = s->ramp_start;
                        }
                        else
                        {
                            s->curr_rate -= delta_rate;
                        }
                    }
                    else
                    {
                        // do nothing to the rate
                    }

                    digitalWrite(s->pin_pul, HIGH);
                    s->curr_steps++;
                }
                else
                {
                    // reset current and desired steps
                    s->curr_steps = 0;
                    s->des_steps = 0;
                    s->curr_rate = s->rate;
                }
                s->counter = 0;
            }
            else
            {
                digitalWrite(s->pin_pul, LOW);
                s->counter++;
            }
            break;
        case STEPPER_MODE_CONDITION:
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
                    s->mode = STEPPER_MODE_STEPS;
                    s->condition = NULL;

                }
                s->counter = 0;
            }
            else
            {
                digitalWrite(s->pin_pul, LOW);
                s->counter++;
            }
            break;
        case STEPPER_MODE_COUNT:
        default:
            break;
    }
}

void stepper_cli_move(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "depositor") == 0)
    {   
        float steps = atoi(args[1]);
        uint8_t dir = atoi(args[2]);
        uint16_t rate = atoi(args[3]);
        uint16_t ramp = atoi(args[4]);
        uint8_t ramp_start = atoi(args[5]);
        stepper_command(STEPPER_DEPOSITOR, steps, dir, rate, ramp, ramp_start);
    }
    else if (strcmp(args[0], "plane") == 0)
    {
        float steps = atoi(args[1]);
        uint8_t dir = atoi(args[2]);
        uint16_t rate = atoi(args[3]);
        uint16_t ramp = atoi(args[4]);
        uint8_t ramp_start = atoi(args[5]);
        stepper_command(STEPPER_PLANE, steps, dir, rate, ramp, ramp_start);
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
                "{\"des_steps\":%d,\"curr_steps\":%d,\"dir\":%d,\"rate\":%d,\ 
                  \"ramp_steps\":%d}", 
                s->des_steps, s->curr_steps, s->dir, s->rate, s->ramp_steps);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
    else if (strcmp(args[0], "plane") == 0)
    {
        stepper_s* s = &stepper_data.steppers[STEPPER_PLANE];
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, 
                "{\"des_steps\":%d,\"curr_steps\":%d,\"dir\":%d,\"rate\":%d,\ 
                  \"ramp_steps\":%d}", 
                s->des_steps, s->curr_steps, s->dir, s->rate, s->ramp_steps);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid stepper");
    }
}
