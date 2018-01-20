import numpy as np 
import cv2 

def EstimateFundamentalMatrix(x1,x2):
    if x1.shape[1]==2: #converting to homogenous coordinates if not already
        x1 = cv2.convertPointsToHomogeneous(x1)[:,0,:]
        x2 = cv2.convertPointsToHomogeneous(x2)[:,0,:]

    A = np.zeros((x1.shape[0],9))

    #Constructing A matrix (vectorized)
    x1_ = x1.repeat(3,axis=1)
    x2_ = np.tile(x2, (1,3))

    A = x1_*x2_

    u,s,v = np.linalg.svd(A)
    F = v[-1,:].reshape((3,3),order='F')

    u,s,v = np.linalg.svd(F)
    F = u.dot(np.diag(s).dot(v))

    F = F / np.linalg.norm(F,'fro')
    
    return F 

def NormalizePts(x):
    mus = x[:,:2].mean(axis=0)
    sigma = x[:,:2].std()
    scale = np.sqrt(2.) / sigma

    transMat = np.array([[1,0,mus[0]],[0,1,mus[1]],[0,0,1]])
    scaleMat = np.array([[scale,0,0],[0,scale,0],[0,0,1]])

    T = scaleMat.dot(transMat)

    xNorm = T.dot(x.T).T

    return xNorm, T

def EstimateFundamentalMatrixNormalized(x1,x2): 
    if x1.shape[1]==2: #converting to homogenous coordinates if not already
        x1 = cv2.convertPointsToHomogeneous(x1)[:,0,:]
        x2 = cv2.convertPointsToHomogeneous(x2)[:,0,:]

    x1Norm,T1 = NormalizePts(x1)
    x2Norm,T2 = NormalizePts(x2)

    F = EstimateFundamentalMatrix(x1Norm,x2Norm)

    F = T1.T.dot(F.dot(T2))
    return F

def EstimateFundamentalMatrixRANSAC(img1pts,img2pts,outlierThres,prob=None,iters=None): 
    if img1pts.shape[1]==2: #converting to homogenous coordinates if not already
        img1pts = cv2.convertPointsToHomogeneous(img1pts)[:,0,:]
        img2pts = cv2.convertPointsToHomogeneous(img2pts)[:,0,:]

    Fs = np.zeros((iters,3,3))
    bestInliers, bestF, bestmask = 0, None, None

    for i in xrange(iters): 
        mask = np.random.randint(low=0,high=img1pts.shape[0],size=(8,))
        
        img1ptsiter = img1pts[mask]
        img2ptsiter = img2pts[mask]
        Fiter = EstimateFundamentalMatrix(img1ptsiter,img2ptsiter)
        
        err = SampsonError(Fiter,img1pts,img2pts)
        mask = err < outlierThres
        numInliers = np.sum(mask)

        if bestInliers < numInliers: 
            bestInliers = numInliers
            bestF = Fiter
            bestmask = mask

        if i%5000==0: 
            print '{}/{} iterations done'.format(i,iters)
        
    return bestF, bestmask

def SampsonError(F,x1,x2): 
    num = np.sum(x1.dot(F) * x2,axis=-1)
    Fx1 = x1.dot(F)
    Fx2 = F.dot(x2.T).T
    denum = Fx1[:,0]**2 + Fx1[:,1]**2 + Fx2[:,0]**2 + Fx2[:,1]**2
    err = num**2/denum
    return err