
/*******************************************************************************
*                                I N C L U D E S                               *
*******************************************************************************/ 

#include "motor_runner.h"
#include "scheduler.h"

#include "dev/servo.h"
#include "dev/stepper.h"

/*******************************************************************************
*                               C O N S T A N T S                              *
*******************************************************************************/ 

/*******************************************************************************
*                      D A T A    D E C L A R A T I O N S                      *
*******************************************************************************/

typedef struct
{
    struct pt thread;
    servo_update_f servo_update_func;
    stepper_update_f stepper_update_func;
} motor_runner_data_s;

/*******************************************************************************
*          P R I V A T E    F U N C T I O N    D E C L A R A T I O N S         *
*******************************************************************************/ 

void run1ms(void);

/*******************************************************************************
*                 S T A T I C    D A T A    D E F I N I T I O N S              *
*******************************************************************************/

static motor_runner_data_s motor_runner_data = 
{
    .servo_update_func = &servo_update,
    .stepper_update_func = &stepper_update
};

/*******************************************************************************
*                      P R I V A T E    F U N C T I O N S                      *
*******************************************************************************/ 

static PT_THREAD(run1ms(struct pt* thread))
{
    PT_BEGIN(thread);
    PT_WAIT_UNTIL(thread, scheduler_taskReleased(PERIOD_1ms, (uint8_t) MOTOR_RUNNER));
    
    // call all the update functions of all motors
    for (uint8_t servo = 0; servo < SERVO_COUNT; servo++)
    {
        motor_runner_data.servo_update_func((servo_id_E) servo);
    }
    
    for (uint8_t stepper = 0; stepper < STEPPER_COUNT; stepper++)
    {
        motor_runner_data.stepper_update_func((stepper_id_E) stepper);
    }

    PT_END(thread);
}

/*******************************************************************************
*                       P U B L I C    F U N C T I O N S                       *
*******************************************************************************/ 

void motor_runner_init(void)
{
    PT_INIT(&motor_runner_data.thread);
}

void motor_runner_run1ms(void)
{
    run1ms(&motor_runner_data.thread);
}
