#include "bbb.h"

BBB::BBB(int a, int b):aa(a),bb(b){}

int BBB::get() {
    aa += aa + bb;
    bb += 2333;
    return aa*bb + 666;
}
