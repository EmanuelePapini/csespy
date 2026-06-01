
import numpy as np


def cartesian_to_spherical(x,y,z):
    """
    convert latitude and longitude into theta and phi (angles on sphere)
    """

    r = np.sqrt(x**2+y**2+z**2)
    theta = np.arccos(z/r)
    phi = np.arctan2(y,x) 
    phi[phi<0] += 2*np.pi 
    return r,theta,phi
def geographical_to_spherical(lat,lon):
    """
    convert latitude and longitude into theta and phi (angles on sphere)
    """

    phi = lon/180*np.pi
    if any(lon<0) : phi[lon<0] += 2*np.pi #+ phi[lon<0]
    theta = -(lat-90)/180*np.pi
    return phi,theta

def get_rotation_matrix_from_vectors_scipy(vec1, vec2):
    """get rotation matrix between two vectors using scipy"""
    from scipy.spatial.transform import Rotation as R
    vec1 = np.reshape(vec1, (1, -1))
    vec2 = np.reshape(vec2, (1, -1))
    r = R.align_vectors(vec2, vec1)
    return r[0].as_matrix()

def get_rotation_matrix_from_vectors(vec1, vec2):
    """ Find the rotation matrix that aligns vec1 to vec2
    :param vec1: A 3d "source" vector
    :param vec2: A 3d "destination" vector
    :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.
    """
    a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
    v = np.cross(a, b)
    if any(v): #if not all zeros then 
        c = np.dot(a, b)
        s = np.linalg.norm(v)
        kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))

    else:
        return np.eye(3) #cross of all zeros only occurs on identical directions

def get_rotation_matrix_to_frame(bx,by,bz):
    """
    Return the rotation matrix to the frame defined by a series of vectors bx,by,bz.
    The new x direction is along the vector, the other direction is taken as the perpendicular 
    to the vector in the z plane. The third direction is the cross product 
    between the two unit vectors.
    
    Parameters:
    -----------
        bx,by,bz : 1D arrays (time series) of size n containing the components of the n vectors.

        output:
            rotation matrix of shape (n,3,3). each matrix[i,3,3] is the rotation matrix to the reference
            frame defined by the vector [bx[i],by[i],bz[i]]
    """

    from ..math import vectors as vt

    nx = np.size(bx)
    BB = np.zeros((3,np.size(bx)),bx.dtype)
    BB[0,:] = bx; BB[1,:] = by; BB[2,:] = bz
    bmod = np.sqrt(bx**2 + by**2+bz**2)

    e1 = BB/ bmod[None,:] 
    
    #now costheta (theta angle between e1 and Bz) is e1[2,:]
    e2 = np.zeros((3,nx))
    sint = 1./np.sqrt(1-e1[2,:]**2) #; sint[~np.isfinite(sint)] = 1
    e2[2,:] = sint
    e2 -= e1[2,:].flatten()*sint*e1
    e3 = vt.cross(e1,e2)

    return np.array([e1,e2,e3]).transpose([2,0,1])

def rotate_vector_to_frame(bx,by,bz,mrot):
    """
    Rotate vector to the desired reference frame defined by the rotation matrix mrot
    
    Parameters
    ----------
        bx : 1D-array of size N
            x component of the vector(s) to rotate
        by : 1D-array of size N
            y component of the vector(s) to rotate
        bz : 1D-array of size N
            z component of the vector(s) to rotate
        mrot: rotation matrices of shape (N,3,3)
            rotation matrices. 
    """

    nn = np.size(bx)
    nnrot = np.shape(mrot)[0]
    if nn !=nnrot:
        raise ValueError('Input rotation matrix/vectors dimensions mismatch!')
    
    BB = np.zeros((3,nn),bx.dtype)
    BB[0,:] = bx; BB[1,:] = by; BB[2,:] = bz

    BB = BB.transpose()
    return np.array([np.dot(mrot[i],BB[i]) for i in range(nn)]).transpose()

def get_stretched_grid(fac):
    """
    return a stretched/compressed grid of shape np.shape(fac) starting from a 
    uniform grid and using fac as stretching factor (i.e. jacobian determinant)
    the  stretching factor is defined pointwise.
    
    input
    -----
        fac: array-like (2D, float)
            array of size MxN containing the isotroping stretching factor (Real positive value)
            1 means no stretching. 0 means singular point.
    """
    M,N = fac.shape
    if M >N:
        fac = fac.transpose()
        trn = True
        M,N = fac.shape
    else:
        trn = False
    x,y = np.meshgrid(np.arange(M),np.arange(N),indexing='ij')

    for i in range(1,M):
        for j in range(i+1):
            print(j,i-j)
#        x[j,i-j] = qualcosa che interseca due cerchi





def get_transform_matrix_sph2car(theta,phi):
    """
    Return the transformation matrix for vectors from spherical to cartesian coordinates
    """

    sint = np.sin(theta); cost = np.cos(theta);
    sinp = np.sin(phi); cosp = np.cos(phi);
    mat = np.zeros((3,3,theta.size))

    mat[0,0,:] = sint*cosp ; mat[0,1,:] = cost*cosp ; mat[0,2,:] = -sinp
    mat[1,0,:] = sint*sinp ; mat[1,1,:] = cost*sinp ; mat[1,2,:] =  cosp
    mat[2,0,:] = cost ; mat[2,1,:] = -sint ; mat[2,2,:] =  0

    return mat

def get_transform_matrix_car2sph(x,y,z):
    """
    Return the transformation matrix for vectors from cartesian to spherical coordinates
    given the coordinates (x,y,z) of the application point of the vector
    """

    r = np.sqrt( x**2 + y**2 + z**2 )
    theta = np.arccos(z/r)
    phi = np.arctan2(y,x) 
    #phi[phi<0] = 2*np.pi+phi[phi<0]
    sint = np.sin(theta); cost = np.cos(theta);
    sinp = np.sin(phi); cosp = np.cos(phi);
    mat = np.zeros((3,3,theta.size))

    mat[0,0,:] = sint*cosp ; mat[0,1,:] = sint*sinp ; mat[0,2,:] =  cost
    mat[1,0,:] = cost*cosp ; mat[1,1,:] = cost*sinp ; mat[1,2,:] = -sint
    mat[2,0,:] = -sinp ; mat[2,1,:] = cosp ; mat[2,2,:] =  0

    return mat

def transform_vector_sph2car(vec_sph,tlat,philon,sphtype='thetaphi'):
    """
    transform a vector from spherical to cartesian coordinates

    input:
        vec_sph: array_like, shape (3,n)
            array containing the vector components in spherical ref. frame:
            either [e_r,e_theta,e_phi] or [e_lat,e_lon,-e_r], depending on the chosen sphtype
        tlat : array_like, shape (n,)
            array containing latitude/theta position of the point where the vector is applied
        philon : array_like, shape (n,)
            array containing longitude/phi position of the point where the vector is applied
        sphtype : str
            either 'thetaphi' or 'latlon' (self-explaining)
    """

    if sphtype == 'latlon':
        phi,theta = geographical_to_spherical(tlat,philon)

        invec = np.concatenate([-vec_sph[2],-vec_sph[0],vec_sph[1]]).reshape(vec_sph.shape)
    else:
        invec = vec_sph
        phi,theta = philon,tlat
    mat = get_transform_matrix_sph2car(theta,phi)

    outvec = np.zeros(vec_sph.shape)

    outvec[0] = mat[0,0]*invec[0] + mat[0,1]*invec[1] + mat[0,2]*invec[2]
    outvec[1] = mat[1,0]*invec[0] + mat[1,1]*invec[1] + mat[1,2]*invec[2]
    outvec[2] = mat[2,0]*invec[0] + mat[2,1]*invec[1] + mat[2,2]*invec[2]
    return outvec

def transform_vector_car2sph(vec_car,x,y,z):
    """
    transform a vector from cartesian to spherical coordinates

    input:
        vec_car: array_like, shape (3,n)
            array containing the vector components in cartesian ref. frame:
        x : array_like, shape (n,)
            array containing x position of the point where the vector is applied
        y : array_like, shape (n,)
            array containing y position of the point where the vector is applied
        z : array_like, shape (n,)
            array containing y position of the point where the vector is applied
    """


    mat = get_transform_matrix_car2sph(x,y,z)
    invec = vec_car
    outvec = np.zeros(vec_car.shape)

    outvec[0] = mat[0,0]*invec[0] + mat[0,1]*invec[1] + mat[0,2]*invec[2]
    outvec[1] = mat[1,0]*invec[0] + mat[1,1]*invec[1] + mat[1,2]*invec[2]
    outvec[2] = mat[2,0]*invec[0] + mat[2,1]*invec[1] + mat[2,2]*invec[2]
    return outvec
