
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "servo.h"
#include "serial.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define MICROSEC_TO_SEC (uint32_t)  1000000
#define MOTOR_RUNNER_CYCLE_us       500
#define MOTOR_RUNNER_PERIOD_PER_SEC MICROSEC_TO_SEC / MOTOR_RUNNER_CYCLE_us

#define SERVO_PWM_PERIOD_MICROSEC (20000)
#define SERVO_PWM_FREQ_HZ         (1 / (SERVO_PWM_PERIOD_MICROSEC * pow(10,-6)))
#define SERVO_PWM_PULSE_MAX       (2000)
#define SERVO_PWM_PULSE_MIN       (1000)
#define MAX_PWM_DUTY_16BITS       (int)(65535)* \
                                  ((float)SERVO_PWM_PULSE_MAX/(float)SERVO_PWM_PERIOD_MICROSEC)
#define MIN_PWM_DUTY_16BITS       (int)(65535)* \
                                  ((float)SERVO_PWM_PULSE_MIN/(float)SERVO_PWM_PERIOD_MICROSEC)

#define DELTA_PWM_DUTY_16BITS     (MAX_PWM_DUTY_16BITS - MIN_PWM_DUTY_16BITS)
#define DELTA_ANGLE               (90)

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/ 

typedef struct
{
    uint8_t pwm_pin;
    uint8_t dig_pin;
    uint8_t pin;
    volatile float curr_angle;
    float des_angle;
    float delta;
    uint16_t counter;
    uint16_t rate;
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
            .pwm_pin = PA_7,
            .dig_pin = PA7,
            .curr_angle = 0.0,
            .des_angle = 0.0,
            .delta = 0.0,
            .counter = 0,
            .rate = 100
        },
        [SERVO_COVER] = 
        {
            .pwm_pin = PB_0,
            .dig_pin = PB0,
            .curr_angle = 0.0,
            .des_angle = 0.0,
            .delta = 0.0,
            .counter = 0,
            .rate = 100
        }
    }
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void servo_init(servo_id_E servo, float angle)
{
    // provide initial angle for servo
    servo_s* s = &servo_data.servos[servo];
    s->des_angle = angle;
    s->curr_angle = angle;
    pinMode(s->dig_pin, OUTPUT);

    pwm_start((PinName) s->pwm_pin, 
              SERVO_PWM_FREQ_HZ, 
              MIN_PWM_DUTY_16BITS + 
                  (int) DELTA_PWM_DUTY_16BITS*((s->des_angle+DELTA_ANGLE/2)/DELTA_ANGLE),
              TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
}

bool servo_command(servo_id_E servo, float angle, uint8_t steps, uint16_t rate) // step size (sets delta) and rate (sets counter)
{
    bool ret = false;
    servo_s* s = &servo_data.servos[servo];
    if (s->des_angle != angle)
    {
        s->des_angle = angle;
        s->delta = (float) (s->des_angle - s->curr_angle) / steps;
        s->rate = rate;
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
    if (s->counter >= MOTOR_RUNNER_PERIOD_PER_SEC/s->rate)
    {
        if (abs(s->des_angle - s->curr_angle) < abs(s->delta) && 
            s->curr_angle != s->des_angle)
        {
            s->curr_angle = s->des_angle;
            pwm_start((PinName) s->pwm_pin,
                    SERVO_PWM_FREQ_HZ,
                    MIN_PWM_DUTY_16BITS +
                        (int) DELTA_PWM_DUTY_16BITS *
                        ((s->des_angle+DELTA_ANGLE/2)/DELTA_ANGLE),
                    TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
        }
        else if (abs(s->des_angle - s->curr_angle) > 0)
        {
            s->curr_angle += s->delta;
            pwm_start((PinName) s->pwm_pin,
                    SERVO_PWM_FREQ_HZ, 
                    MIN_PWM_DUTY_16BITS +
                        (int) DELTA_PWM_DUTY_16BITS *
                        ((s->curr_angle+DELTA_ANGLE/2)/DELTA_ANGLE),
                    TimerCompareFormat_t::RESOLUTION_16B_COMPARE_FORMAT);
        }
        else
        {
            // do nothing, desired angle has been acheived
        }
        s->counter = 0;
    }
    else
    {
        s->counter++;
    }
}

void servo_cli_move(uint8_t argNumber, char* args[])
{
    servo_id_E s = SERVO_COUNT;
    if (strcmp(args[0], "cover") == 0)
    {
        s = SERVO_COVER;
    }
    else if (strcmp(args[0], "depositor") == 0)
    {   
        s = SERVO_DEPOSITOR;
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid servo");
    }

    if (s != SERVO_COUNT)
    {
        float angle = atof(args[1]);
        uint8_t steps = atoi(args[2]);
        uint16_t rate = atoi(args[3]);
        servo_command(s, angle, steps, rate);
    }
    else
    {
         // do nohting
    }
}

void servo_cli_dump(uint8_t argNumber, char* args[])
{
    if (strcmp(args[0], "depositor") == 0)
    {
        servo_s* s = &servo_data.servos[SERVO_DEPOSITOR];
        char* st = (char*) malloc(SERIAL_MESSAGE_SIZE);
        sprintf(st, 
                "{\"des_angle\":%.3f,\"curr_angle\":%.3f,\"delta\":%.3f,\"rate\":%i}", 
                s->des_angle, s->curr_angle, s->delta, s->rate);
        serial_send_nl(PORT_COMPUTER, st);
        free(st);
    }
    else
    {
        serial_send_nl(PORT_COMPUTER, "invalid servo");
    }
}
