
#include<iostream>
#include<string>
#include<fstream>
#include<iomanip>

//
//make a file that has a big list of 0s save for a 1
//at the index of search_value.
//these are easy to read into pylab as numpy arrays
//and let us make nice plots
//
//I don't know why I templated this.
//
template<typename T>
void print_step( T* f, int n, T search_value, int stepcount){
    std::ofstream fout;
    //some crap to make the int a string
    std::string s;
    std::stringstream out;
    out << std::setfill('0')<<std::setw(4) << stepcount;
    s = out.str();
    s += ".dat";
    fout.open(s.c_str());

    //find the index of search_value
    //I guess f could be randomly ordered
    int index;
    for(int i=0; i<n; i++){
        if( search_value == f[i])
            index = i;
    }

    //print out the nice array
    for(int i=0; i<n; i++){
        fout << (i==index) << " ";
    }

    std::cout << "made file " << stepcount << std::endl;

    fout.close();
    return;
}
