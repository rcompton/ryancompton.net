from numpy import *
import pylab
import glob
import re
import os

#this is such a cool trick
#I forget where I first saw it
def make_pngs_into_an_avi(fps):
    video_command = ('mencoder',
           'mf://*.png',
           '-mf',
           'type=png:w=800:h=600:fps='+str(fps),
           '-ovc',
           'lavc',
           '-lavcopts',
           'vcodec=mpeg4',
           '-oac',
           'copy',
           '-o',
           'output.avi')

    os.spawnvp(os.P_WAIT, 'mencoder', video_command)

    print "The movie was drawn to 'output.avi'"

    audio_command = ('mencoder',
            '-ovc',
            'copy',
            '-audiofile',
            'fast_fourier_music.wav',
            '-oac',
            'copy',
            'output.avi',
            '-o',
            'video_new.avi')

    os.spawnvp(os.P_WAIT, 'mencoder', audio_command)


#    os.system(mencoder -ovc copy -audiofile drumChordSort.wav -oac copy output.avi -o video_new.avi")

    return

def main():
    filenames = glob.glob("*.dat")
    filenames = sort(filenames) #yeah, python is easy

    N = len(filenames)
    picture = zeros((N,N))

    pylab.cla()
    stepcount = 1 
    for i in filenames:
        file = open(i)
        data = array(file.read().strip().split(" "))

        #put the data into the 2D picture array
        for j in range(N):
   #         print data[j]==str(1), " dataj ", type(data[j])
            if data[j] == str(1):
                picture[0:stepcount,j] = data[j]

        pylab.imshow(picture)
        
        fname = re.sub("dat", "png", i)
        pylab.savefig(fname)

        stepcount += 1
        print i

    make_pngs_into_an_avi(.5)

    os.system("rm *dat")
    os.system("rm *png")

    return


if __name__ == "__main__":
    main()

