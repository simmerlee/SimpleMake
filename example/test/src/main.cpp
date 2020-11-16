#include "aaa.h"
#include "bbb.h"
#include <iostream>

using namespace std;

int main() {
    BBB bbb(12345, 54321);
    int n1 = bbb.get();
    int n2 = bbb.get();
    int n3 = aaa_f1(n1, n2);
    cout << "result: "<< aaa_f2(bbb.get(), bbb.get())<<endl;

    return 0;
}
