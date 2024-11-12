#ifndef CONTROLLER_H
#define CONTROLLER_H
#include "CPUModel.h"
#include "View.h"
#include "CPUModel.h"

#include <iostream>
#include <fstream>
#include <iomanip>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <vector>



class Controller{
    private:
        CPUMod cpu;
        View display;
        unsigned int PCc;
        unsigned int ii;

    public:
        Controller() = default;
         Controller() : cpu(), display(), PCc(0) {}

         void executeFile(const char* file);
};

#endif