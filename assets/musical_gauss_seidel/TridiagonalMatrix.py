from numpy import *

#a tridiagonal matrix class
class TridiagonalMatrix:
    #initialize with 3 numpy arrays
    def __init__(self, upper_in, diag_in, lower_in):
        self.upper  = upper_in
        self.diag   = diag_in
        self.lower  = lower_in
        self.dim    = diag_in.shape[0]
    #matrix mulitplication
    def apply(self, v):
        out = ndarray(self.dim)
        try:
            out[0] = self.diag[0]*v[0] + self.upper[0]*v[1]
            out[self.dim-1] = self.lower[self.dim-2]*v[self.dim-2] + self.diag[self.dim-1]*v[self.dim-1]
            for i in range(1, self.dim-1):
                out[i] = self.lower[i-1]*v[i-1] + self.diag[i]*v[i] + self.upper[i]*v[i+1]
        except(IndexError):
            print "Wrong sizes"

        return out

    #solve Ax=b using gauss seidel
    #with initial guess x0
    def gauss_seidel(self, b, x0, tol):
        error = self.apply(x0) - b
        x = x0
        count=0
        while(linalg.norm(error) > tol):
            #update x in place
            x[0] = (b[0] - self.upper[0]*x[1])/self.diag[0]
            x[self.dim-1] = (b[self.dim-1] - self.lower[self.dim-2]*x[self.dim-2])/self.diag[self.dim-1]
            for i in range(1,self.dim-1):
                x[i] = (b[i] - self.lower[i-1]*x[i-1] - self.upper[i]*x[i+1])/self.diag[i]
            #update the error
            error = self.apply(x) - b

            count = count+1
            print count
        return x
            

"""
#test code..
A = TridiagonalMatrix(ones(59),ones(60), ones(59))
for i in range(60):
    A.diag[i] = -2
b = ones(60)

print A.apply(b)

x0 = ones(60)
tol = 1e-4
x =  A.gauss_seidel(b, x0, tol)
print x

B = zeros((60,60))
for i in range(60):
    B[i,i] = -2
for i in range(1,60):
    B[i,i-1] = 1
for i in range(0,59):
    B[i,i+1] = 1

y = linalg.solve(B,b)

print y

print y-x

print linalg.norm(x-y), " error"
"""

