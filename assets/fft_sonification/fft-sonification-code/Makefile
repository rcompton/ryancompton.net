#not sure why I need this
SHELL=/bin/sh

#ok, spec some varbs
STKINCL_DIR = /usr/include/stk/

CPPFLAGS = -I $(STKINCL_DIR)

LIBS = -lstk

fft_sonification : fft_sonification.cpp
	g++ -o fft_sonification fft_sonification.cpp -I $(STKINCL_DIR) $(LIBS) 

