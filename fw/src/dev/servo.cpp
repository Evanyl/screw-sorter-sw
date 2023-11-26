
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "servo.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define SERVO_PWM_PERIOD    (20000)
#define SERVO_PWM_PULSE_MAX (2000)
#define SERVO_PWM_PULSE_MIN (1000)
#define MAX_PWM_DUTY_16BITS (int)(65535)*(SERVO_PWM_PULSE_MAX/SERVO_PWM_PERIOD)
#define MIN_PWM_DUTY_16BITS (int)(65535)*(SERVO_PWM_PULSE_MIN/SERVO_PWM_PERIOD)

#define DELTA_PWM_DUTY_16BITS (MAX_PWM_DUTY_16BITS - MIN_PWM_DUTY_16BITS)
#define DELTA_ANGLE           (180)

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    uint8_t pin;
    volatile int16_t curr_angle;
    int16_t des_angle;
    int16_t delta;
} servo_s;

typedef struct
{
    servo_s servos[SERVO_COUNT];
} servo_data_s;


/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/ 

servo_data_s servo_data = 
{
    .servos = 
    {
        [SERVO_DEPOSITOR] = 
        {
            .pin = PA_3,
            .curr_angle = 0,
            .des_angle = 0,
            .delta = 0
        }
    }
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void servo_init(servo_id_E servo, int16_t angle)
{
    // provide initial angle for servo
    servo_s* s = &servo_data.servos[servo];
    s->des_angle = angle;
    s->curr_angle = angle;
    pinMode(s->pin, OUTPUT);
    pwm_start((PinName) s->pin, 
              1000000/SERVO_PWM_PERIOD, 
              MIN_PWM_DUTY_16BITS + 
                  (int) DELTA_PWM_DUTY_16BITS*(s->des_angle/DELTA_ANGLE),
              TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
}

bool servo_command(servo_id_E servo, int16_t angle, uint8_t steps)
{
    bool ret = false;
    servo_s* s = &servo_data.servos[servo];
    if (s->des_angle != angle)
    {
        s->des_angle = angle;
        s->delta = (int16_t) (s->des_angle - s->curr_angle) / steps;
    }
    else if (s->des_angle == s->curr_angle)
    {
        ret = true;
    }
    else
    {
        // do nothing
    }
    return ret;
}

void servo_update(servo_id_E servo)
{
    servo_s* s = &servo_data.servos[servo];
    if (abs(s->des_angle - s->curr_angle) < abs(s->delta) && 
        s->curr_angle != s->des_angle)
    {
        s->curr_angle = s->des_angle;
        pwm_start((PinName) s->pin,
                  1000000/SERVO_PWM_PERIOD,
                  MIN_PWM_DUTY_16BITS + 
                    (int) DELTA_PWM_DUTY_16BITS*(s->des_angle/DELTA_ANGLE),
                  TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
    }
    else if (abs(s->des_angle - s->curr_angle) > 0)
    {
        s->curr_angle += s->delta;
        pwm_start((PinName) s->pin,
                  1000000/SERVO_PWM_PERIOD, 
                  MIN_PWM_DUTY_16BITS + 
                    (int) DELTA_PWM_DUTY_16BITS*(s->curr_angle/DELTA_ANGLE),
                  TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
    }
    else
    {
        // do nothing, desired angle has been acheived
    }
}

void servo_cli_move(uint8_t argNumber, char* args[])
{
    int16_t angle = atoi(args[0]);
    uint8_t steps = atoi(args[1]);
    servo_command(SERVO_DEPOSITOR, angle, steps);
}

void servo_cli_dump(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "depositor") == 0)
    {
        servo_s* s = &servo_data.servos[SERVO_DEPOSITOR];
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, "{\"des_angle\": %i, \"curr_angle\": %i}", 
                s->des_angle, s->curr_angle);
        serial_send(PORT_COMPUTER, st);
        free(st);
    }
    else
    {
        serial_send(PORT_COMPUTER, "invalid servo");
    }
}
