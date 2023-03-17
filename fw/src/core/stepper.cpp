

#include "stepper.h"

#define STEPS 200
#define STEP_ANGLE 1.8

static stepper_t stepper_arr[] = 
{
    {
        .angle = 0,
        .stepper = Stepper(STEPS, PA5, PA6)
    }
};

// static Stepper plane = Stepper(STEPS, PA5, PA6);

void stepper_rotate(stepper_id_t stepperId, uint16_t angle)
{
    stepper_arr[stepperId].stepper.step((int16_t) angle / STEP_ANGLE);
    stepper_arr[stepperId].angle += angle;
}

void stepper_setSpeed(stepper_id_t stepperId, uint16_t rpm)
{
    stepper_arr[stepperId].stepper.setSpeed(rpm);
}