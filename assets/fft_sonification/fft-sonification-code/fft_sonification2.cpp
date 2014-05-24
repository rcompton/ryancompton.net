#include <iostream>
#include <complex>
#include <cmath>
using namespace std;

#include "stk/FileWvOut.h"
#include "Plucked.h"
using namespace stk;

#include "print_step.cpp"

//stk defines it's own PI
//const double PI = 4.0*atan(1.0);


complex<double>* global_f;
int global_n;
int global_stepcount;

void fft_sonification(int n, complex<double>* f, FileWvOut& output_wv, StkFloat fps){

    //
    //set up the stk stuff
    //

    Instrmnt* music = new Plucked(57.01);

    //we're going to tick a lot of frames
    //in fact, we'll tick fps (probably 44100) frames
    //at each base case 
    StkFrames frame(fps, 1);


    //
    //do the fft stuff
    //

    //if not a power of 2, then fuck you.
    if( n&(n-1) && n>0){
        cout << "fuck you\n";
        return;
    }

    complex<double>* f_even = new complex<double>[n/2]; //evens
    complex<double>* f_odd = new complex<double>[n/2]; //odds


    //when you hit the base case
    //music fills the place
    if(n == 0){
        cout << "oh shit nothing to do\n";
        return;
    }
    if(n == 1){
        StkFloat freq = f[0].real(); //real part for freq
        StkFloat loudness = f[0].imag(); //im part for loudness

        StkFloat duration;
        double max_val = abs(global_f[0]);
        double min_val = abs(global_f[0]);
        for(int i=0; i<global_n; i++){
            if(max_val < abs(global_f[i]))
                max_val = abs(global_f[i]);
            if(min_val > abs(global_f[i]))
                min_val = abs(global_f[i]);
        }

        duration = (1.0 - (f[0].real() - min_val)/(max_val-min_val) )*.3 + .1;
        duration *= 44100;
        StkFrames frame_d(duration, 1);

        music->noteOn(freq , loudness);
        music->tick(frame_d);
        output_wv.tick(frame_d);

        cout << "play note at " << f[0] << "\n";

        //all that globals just for this..
        global_stepcount++;
        print_step(global_f, global_n, f[0], global_stepcount);

        return;
    }


    int i,j;
    for(int k=0; k<n/2; k++){
        f_even[k] = f[2*k];
        f_odd[k] = f[2*k+1];
    }

    //transform the sub arrays
    fft_sonification(n/2, f_even, output_wv, fps);
    fft_sonification(n/2, f_odd, output_wv, fps);

    //use the Danielson-Lanczos and copy stuff back in
    for(int k = 0; k < n/2; k++) {

        complex<double> w;
        w = complex<double>(0.0, 2.0*PI*k/n);
        w = exp(w); 


        f[k] = f_even[k] + w*f_odd[k];
        f[k+n/2] = f_even[k] - w*f_odd[k];
    }

    delete[] f_even, f_odd; 
    return;

}


int main(){

    //setup all the audio 

    StkFloat samp_rate = 44100.0;

    Stk::setSampleRate(samp_rate);//high quality output_wv

    Stk::setRawwavePath("/home/ryan/stk-4.4.1/rawwaves/");

    StkFloat fps = 4.0; //denominator frames per sec
    fps = samp_rate/fps;

    FileWvOut output_wv; //this is how we write .wav files
    output_wv.openFile("fast_fourier_music.wav", 1, FileWrite::FILE_WAV, Stk::STK_SINT16);

    //make some initial data to transform out of

    global_n = pow(2,6);
    global_f = new complex<double>[global_n];

    for(int i=0; i<global_n; i++){
        global_f[i] = complex<double>(41.0*pow(2, i/32.0), .5);
        // cout << f[i] << " ";
    }
    cout <<"\n that was before FFT\n";

    //for those about to rock
    fft_sonification(global_n, global_f, output_wv, fps);


    delete[] global_f;
    return 0;

}


