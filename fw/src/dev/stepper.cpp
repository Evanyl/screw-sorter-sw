
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "stepper.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define MICROSEC_TO_SEC (uint32_t)  1000000
#define MOTOR_RUNNER_CYCLE_us       500
#define MOTOR_RUNNER_PERIOD_PER_SEC MICROSEC_TO_SEC / MOTOR_RUNNER_CYCLE_us

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef enum
{
    STEPPER_MODE_STEPS,
    STEPPER_MODE_CONDITION,
    STEPPER_MODE_ANGLE,
    STEPPER_MODE_COUNT
} stepper_mode_E;

typedef struct
{
    uint8_t pin_dir;
    uint8_t pin_pul;
    uint8_t pin_ena;               // Enable:LOW, Disable:HIGH      
    uint8_t dir;                   // 1:CW 0:CCW (top-down, imaging plane left)
    uint16_t rate;                 // Steps per second
    uint16_t ramp_start;
    uint16_t curr_rate;
    uint16_t counter;
    stepper_mode_E mode;
    // Angle based control
    float last_des_angle;          
    float des_angle;
    float curr_angle;
    float ramp_angle;
    float angle_per_step;
    // Step based control
    uint16_t des_steps;
    uint16_t curr_steps;
    uint16_t ramp_steps;
    // Condition-based control
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

static stepper_id_E _stepper_which(char* name);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

stepper_data_s stepper_data = 
{
    .steppers = 
    {
#ifdef DEPOSIT
        [STEPPER_BOXES] = 
        {
            .pin_dir = PA2,
            .pin_pul = PA1,
            .pin_ena = PA3
        },
#elif ISOLATE_CLASSIFY
        [STEPPER_DEPOSITOR] =
        {
            .pin_dir = PB7,
            .pin_pul = PB8,
            .pin_ena = PB6,
            .last_des_angle = 0.0,
            .des_angle = 0.0,
            .curr_angle = 0.0,
            .angle_per_step = 1.0 / ((3200.0 / 360.0)*(72 / 24))
        },
        [STEPPER_PLANE] =
        {
            .pin_dir = PB4,
            .pin_pul = PB5,
            .pin_ena = PB3,
            .last_des_angle = 0.0,
            .des_angle = 0.0,
            .curr_angle = 0.0,
            .angle_per_step = 1.0 / ((3200.0 / 360.0)*(150 / 30))
        },
        [STEPPER_ARM] = 
        {
            .pin_dir = PA12,
            .pin_pul = PA15,
            .pin_ena = PA11,
            .last_des_angle = 0.0,
            .des_angle = 0.0,
            .curr_angle = 0.0,
            .angle_per_step = 1.0 / ((4000.0 / 360.0)*(133.0 / 24))
        },
        [STEPPER_SIDELIGHT] =
        {
            .pin_dir = PA2,
            .pin_pul = PA1,
            .pin_ena = PA3
        },
        [STEPPER_BELT_TOP] = 
        {
            .pin_dir = PA5,
            .pin_pul = PA4,
            .pin_ena = PA6
        },
        [STEPPER_BELT_BOTTOM] =
        {
            .pin_dir = PB13,
            .pin_pul = PB14,
            .pin_ena = PB12
        }
#else
        // nothing
#endif
    },
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/

static stepper_id_E _stepper_which(char* name)
{
    stepper_id_E s = STEPPER_COUNT;
#ifdef DEPOSIT
    if (strcmp(name, "boxes") == 0)
    {
        s = STEPPER_BOXES;
    }
#elif ISOLATE_CLASSIFY
    if (strcmp(name, "depositor") == 0)
    {
        s = STEPPER_DEPOSITOR;
    }
    else if (strcmp(name, "plane") == 0)
    {
        s = STEPPER_PLANE;
    }
    else if (strcmp(name, "arm") == 0)
    {
        s = STEPPER_ARM;
    }
    else if (strcmp(name, "sidelight") == 0)
    {
        s = STEPPER_SIDELIGHT;
    }
    else if (strcmp(name, "belt_top") == 0)
    {
        s = STEPPER_BELT_TOP;
    }
    else if (strcmp(name, "belt_bottom") == 0)
    {
        s = STEPPER_BELT_BOTTOM;
    }
#else
    // nothing
#endif
    return s;
}

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
    if (s->curr_steps == 0 && steps != 0)
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
    else if (s->curr_steps == s->des_steps || steps == 0)
    {
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

bool stepper_commandAngle(stepper_id_E stepper, float angle, float ramp_angle, 
                          uint16_t rate, uint16_t rate_start)
{
    bool ret = false;
    stepper_s* s = &stepper_data.steppers[stepper];
    if (s->curr_angle == angle)
    {
        // we've attained the desired angle
        ret = true;
    }
    else if (s->des_angle == angle)
    {
        // moving to the des_angle, command has already registered
        ret = false;
    }
    else
    {
        // only update rates if we are traversing to new des_angle
        //     not for repeated calls to the same des_angle...
        ret = false;
        s->des_angle = angle;
        s->ramp_angle = ramp_angle;
        s->rate = rate;
        s->ramp_start = rate_start;
        s->ramp_steps = (uint16_t) ramp_angle / s->angle_per_step;
        if (s->ramp_steps == 0)
        {
            s->curr_rate = rate;
        }
        else
        {
            s->curr_rate = s->ramp_start;
        }

        s->mode = STEPPER_MODE_ANGLE;
        if (s->curr_angle < s-> des_angle)
        {
            // Step CCW (0)
            s->dir = 0;
        }
        else
        {
            // Step CW (1)
            s->dir = 1;
        }
    }
    return ret;
}

void stepper_calibAngle(stepper_id_E stepper, float angle)
{
    stepper_data.steppers[stepper].curr_angle = angle;
    stepper_data.steppers[stepper].last_des_angle = angle;
    stepper_data.steppers[stepper].des_angle = angle;
}

void stepper_calibSteps(stepper_id_E stepper)
{
    stepper_data.steppers[stepper].curr_steps = 0;
    stepper_data.steppers[stepper].des_steps = 0;
}

void stepper_update(stepper_id_E stepper)
{
    stepper_s* s = &stepper_data.steppers[stepper];

    switch (s->mode)
    {
        case STEPPER_MODE_STEPS:
            if (s->counter >= MOTOR_RUNNER_PERIOD_PER_SEC/s->curr_rate)
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
                    // s->curr_steps = 0;
                    // s->des_steps = 0;
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
            if (s->counter >= MOTOR_RUNNER_PERIOD_PER_SEC/s->rate)
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

        case STEPPER_MODE_ANGLE:
            if (s->counter >= MOTOR_RUNNER_PERIOD_PER_SEC/s->curr_rate)
            {
                digitalWrite(s->pin_dir, s->dir);
                delayMicroseconds(10); // Ensure direction is registered
                if (abs(s->des_angle - s->curr_angle) > s->angle_per_step)
                {
                    uint8_t delta_rate = 0;
                    if (s->ramp_steps > 0)
                    {
                        delta_rate = s->rate / s->ramp_steps;
                    }

                    // Get angle deltas (positive by construction)
                    float start_to_curr_angle;
                    float curr_angle_to_end;
                    float delta_angle;
                    if (s->dir == 0)
                    {
                        start_to_curr_angle = s->curr_angle - s->last_des_angle;
                        curr_angle_to_end = s->des_angle - s->curr_angle;
                        delta_angle = s->angle_per_step;
                    }
                    else
                    {
                        start_to_curr_angle = s->last_des_angle - s->curr_angle;
                        curr_angle_to_end = s->curr_angle - s->des_angle;
                        delta_angle = -s->angle_per_step;
                    }
                    // Ramping up
                    if (start_to_curr_angle < s->ramp_angle && 
                        delta_rate > 0)
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
                    // Ramping down
                    else if (curr_angle_to_end < s->ramp_angle && 
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
                    // Executing normal rate
                    else
                    {
                        // do nothing to the rate
                    }

                    digitalWrite(s->pin_pul, HIGH);
                    // Update curr_angle after step
                    s->curr_angle += delta_angle;
                }
                else
                {
                    // Set curr_steps to des_steps and reset curr_rate
                    s->last_des_angle = s->des_angle;
                    s->curr_angle = s->des_angle;
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
        case STEPPER_MODE_COUNT:
        default:
            break;
    }
}

void stepper_cli_zero(uint8_t argNumber, char* args[])
{
    stepper_id_E s = _stepper_which(args[0]);

    if (s == STEPPER_COUNT)
    {
        serial_send_nl(PORT_COMPUTER, "invalid stepper");
    }
    else
    {
        if (strcmp(args[1], "angle") == 0)
        {
            stepper_calibAngle(s, 0.0);
        }
        else if (strcmp(args[1], "steps") == 0)
        {
            stepper_calibSteps(s);
        }
        else
        {
            serial_send_nl(PORT_COMPUTER, "invalid mode");
        }
    }
}

void stepper_cli_move(uint8_t argNumber, char* args[])
{
    stepper_id_E s = _stepper_which(args[0]);

    if (s == STEPPER_COUNT)
    {
        serial_send_nl(PORT_COMPUTER, "invalid stepper");
    }
    else
    {
        // bool stepper_commandAngle(stepper_id_E stepper, float angle, float ramp_angle, 
        //                   uint16_t rate, uint16_t rate_start)
        if (strcmp(args[1], "angle") == 0)
        {
            float des_angle = atof(args[2]);
            uint16_t rate = atoi(args[4]);
            float ramp_angle = atof(args[3]);
            uint8_t ramp_start = atoi(args[5]);
            stepper_commandAngle(s, des_angle, ramp_angle, rate, ramp_start);
        }
        else if (strcmp(args[1], "steps") == 0)
        {
            uint16_t steps = atoi(args[2]);
            uint8_t dir = atoi(args[3]);
            uint16_t rate = atoi(args[4]);
            uint16_t ramp_steps = atoi(args[5]);
            uint16_t ramp_start = atoi(args[6]);
            stepper_command(s, steps, dir, rate, ramp_steps, ramp_start);
        }
        else
        {
            serial_send_nl(PORT_COMPUTER, "invalid stepper mode");
        }
    }
}

void stepper_cli_dump(uint8_t argNumber, char* args[])
{
    stepper_id_E s_id = _stepper_which(args[0]);

    if (s_id == STEPPER_COUNT)
    {
        serial_send_nl(PORT_COMPUTER, "invalid stepper");
    }
    else
    {
        stepper_s* s = &stepper_data.steppers[s_id];
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, 
                "{\"des_steps\":%d,\"curr_steps\":%d,\"dir\":%d,\"rate\":%d,\ 
                    \"ramp_steps\":%d}", 
                s->des_steps, s->curr_steps, s->dir, s->rate, s->ramp_steps);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
}
