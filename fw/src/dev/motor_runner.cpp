
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "motor_runner.h"
#include "servo.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

#define MOTOR_PERIOD_MIROSEC (100)

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/

typedef struct
{
    HardwareTimer* timer;
    servo_update_f servo_data_func;
} motor_runner_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

void motor_runner_ISR(void);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/

static motor_runner_data_s motor_runner_data = 
{
    .servo_data_func = &servo_update,
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

void motor_runner_ISR(void)
{
    // call all the update functions of all motors
    for (uint8_t servo = 0; servo < SERVO_COUNT; servo++)
    {
        motor_runner_data.servo_data_func((servo_id_E) servo);
    }
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void motor_runner_init(void)
{
    motor_runner_data.timer = new HardwareTimer(TIM3);
    motor_runner_data.timer->setOverflow(MOTOR_PERIOD_MIROSEC, MICROSEC_FORMAT);
    motor_runner_data.timer->refresh();
    motor_runner_data.timer->attachInterrupt(motor_runner_ISR);
    motor_runner_data.timer->resume();
}
