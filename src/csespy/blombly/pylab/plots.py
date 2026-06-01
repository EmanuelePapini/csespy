

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker
from ..math import functions as _mfunc
from . import palette_tools as ept
#
#   PLOTTING TOOLS
#


def saturate(array,vmin = None, vmax = None,replace_zeroes = None):
    """
    Fucking python doesn't like reducing plotting ranges (even though it seys it can do it).  
    So this function does the trick, by saturating whathever array to the desired values.
    """
    outa = array.copy()
    if vmin is not None:
        outa[array<vmin] = vmin
    if vmax is not None:
        outa[array>vmax] = vmax
    if replace_zeroes is not None:
        filval = fillzeroes if type(fillzeroes) is float else np.min(array[array!=0])
        outa[array==0] = filval
    return outa

def log_levels(vmin,vmax,nlev,logbase = 10):
    return logbase**np.linspace(_mfunc.logn(vmin,logbase),_mfunc.logn(vmax,logbase),nlev)

def reset_color_cycle():
    plt.gca().set_prop_cycle(None)


class SciNotFormatter(matplotlib.ticker.ScalarFormatter):
    def __init__(self, order=0, fformat="%1.1f", offset=True, mathText=True):
        self.oom = order
        self.fformat = fformat
        matplotlib.ticker.ScalarFormatter.__init__(self,useOffset=offset,useMathText=mathText)
    def _set_orderOfMagnitude(self, nothing):
        self.orderOfMagnitude = self.oom
    def _set_format(self, vmin, vmax):
        self.format = self.fformat
        if self._useMathText:
            self.format = '$%s$' % matplotlib.ticker._mathdefault(self.format)


def add_colorbar(im, aspect=20, pad_fraction=0.5, position="right",scientific=False, **kwargs):
    """Add a vertical color bar to an image plot."""
    axxes=im.axes if hasattr(im,'axes') else im.ax
    from mpl_toolkits import axes_grid1
    divider = axes_grid1.make_axes_locatable(axxes)
    width = axes_grid1.axes_size.AxesY(axxes, aspect=1./aspect)
    pad = axes_grid1.axes_size.Fraction(pad_fraction, width)
    current_ax = plt.gca()
    cax = divider.append_axes(position, size=width, pad=pad)
    plt.sca(current_ax)
    if scientific :
        expp=np.log10(np.abs(im.get_array()).max())
        return axxes.figure.colorbar(im, cax=cax, format=SciNotFormatter(expp,mathText=False), **kwargs)
    
    else:
        return axxes.figure.colorbar(im, cax=cax, **kwargs)

def add_subplot_colorbar(fig,ax,img, width="2%", height="100%", loc='lower left',
                   bbox_to_anchor=(1.05, 0., 1, 1), borderpad=0,**kwargs):
    
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    axins = inset_axes(ax,
                   width=width,  # width = 5% of parent_bbox width
                   height=height,  # height : 50%
                   loc= loc ,
                   bbox_to_anchor= bbox_to_anchor,
                   bbox_transform=ax.transAxes,
                   borderpad=0,
                   )

    return fig.colorbar(img, cax=axins,**kwargs)


def hline(x,ax=None,**kwargs):
    from pylab import axhline
    if ax is None:
        if np.size(x) == 1 :
            axhline(y=x,**kwargs)
        else :
            [axhline(y=i,**kwargs) for i in x]
    else:
        if np.size(x) == 1 :
            ax.axhline(y=x,**kwargs)
        else :
            [ax.axhline(y=i,**kwargs) for i in x]

def vline(x,ax=None,**kwargs):
    from pylab import axvline
    if ax is None:
        if np.size(x) == 1 :
            axvline(x=x,**kwargs)
        else :
            [axvline(x=i,**kwargs) for i in x]
    else:
        if np.size(x) == 1 :
            ax.axvline(x=x,**kwargs)
        else :
            [ax.axvline(x=i,**kwargs) for i in x]


def vspan(x,err,**kwargs):
    from pylab import axvspan
    if np.size(x) == 1 :
        axvspan(x-err,x+err,**kwargs)
    else :
        [axvspan(i-j,i+j,**kwargs) for i,j in zip(x,err)]

def oplot_slope(slpe, anchor, rng = None, nn = 100, label = None, xylabel = None, ax = None, ylabel_factor=1.4,annotate_kwargs={}, *args, **kwargs):

    if rng is None:
        rng = plt.xlim()


    x=np.linspace(rng[0],rng[1],nn)
    
    fac=anchor[1]/anchor[0]**slpe

    if ax is None:
        ax=plt
        
    ax.plot(x, (x**slpe)*fac, *args, **kwargs)

    if label is not None:
        if xylabel is None:
            ax.annotate(label,np.array(anchor)*ylabel_factor)
        else:
            if type(xylabel) is list:
                ax.annotate(label,xylabel,**annotate_kwargs)
            else:
                ax.annotate(label,[xylabel,(xylabel**slpe)*fac*ylabel_factor],**annotate_kwargs)


def subplots(nrows=1, ncols=1, sharex=False, sharey=False, squeeze=True, \
             subplot_hsize=None, \
             subplot_vsize=None, hspace=0.2,\
             subplot_kw=None, gridspec_kw=None, **fig_kw):
    """
    wrapper of matplotlib.pyplot.subplots to create subplots with specific inches size
    arguments: All standard arguments subplots can take plus the following argument

        axis_size=None
    """


    if subplot_hsize is None and subplot_vsize is None:
        return plt.subplots(nrows,ncols,sharex,sharey,squeeze,subplot_kw=subplot_kw, gridspec_kw=gridspec_kw, **fig_kw)

    fig, ax = plt.subplots(nrows,ncols,sharex,sharey,squeeze,subplot_kw=subplot_kw, gridspec_kw=gridspec_kw, **fig_kw)

    figsize = fig.get_size_inches()

    fig.subplots_adjust(hspace=hspace)
    if subplot_hsize is not None:
         hsize = ncols*subplot_hsize/figsize[0]
         hsize = 1. - hsize #(fig.subplotpars.left + fig.subplotpars.right)
         plt.subplots_adjust(left=hsize*0.85, right = 1 - hsize*0.15)
    
    if subplot_vsize is not None:
         hspace= hspace*(nrows-1)
         vsize = (nrows*subplot_vsize)/figsize[1] + hspace
         vsize = 1. - vsize #(fig.subplotpars.left + fig.subplotpars.right)
         plt.subplots_adjust(bottom=vsize*0.9, top = 1 - vsize*0.1)
         print(vsize,nrows, hspace)
    return fig, ax


def imshow(x,y,img, ax=None, yscale = 'linear', palette_range = 'global', norm = None, vmin = None , vmax = None, overlap = 2,\
           raster = 'horizontal', **kwargs):
    """

    Parameters
    ----------
    img : 2d array-like shape = (NY,NX)
        image to be rendered
    x: 1d array-like shape=(NX,)
        array containing equally spaced x coordinates (if raster is 'horizontal').
        array containing arbitrary spaced x coordinates (if raster is 'vertical').
    y: 1d array-like shape=(NY,)
        array containing arbitrary spaced increasing y coordinates (if raster is 'horizontal').
        array containing equally spaced increasing y coordinates (if raster is 'vertical').
    yscale : str
        'linear': creates pixels linearly scaled, i.e., the i-th row (first index of img corresponding to the
                  y-coordinate) has a pixel width in the y direction that goes from 
                  (y[i-1]+y[i])/2 to (y[i]+y[i+1])/2

        'log10' :  creates pixels log10 scaled, i.e., the i-th row (first index of img corresponding to the
                  y-coordinate) has a pixel width in the y direction that goes from 
                  (log10(y[i-1])+log10(y[i]))/2 to (log10(y[i])+log10(y[i+1]))/2

    palette_range : str
        'global' : color level ranges are calculated on the global image (default)
        'row-relative': color level ranges are relative to each row of the image (LIM-like)
        N.B. This option is overridden if vmin and vmax are set explicitly.
    
    **kwargs: all keyword arguments allowed in pylab.imshow
    """


    if palette_range =='global':
        if vmin is None: vmin = np.min(img)
        if vmax is None: vmax = np.max(img)

    if norm is None:
        norm = mpl.colors.Normalize
    
    axx = plt if ax is None else ax
    
    NY,NX = np.shape(img)
    
    if raster == 'horizontal':
        if yscale == 'linear':
            yy=y
        elif yscale == 'log10':
            yy=np.log10(y)
        else:
            raise ValueError("Wrong value/type inserted for yscale! Only allowed values are 'linear' or 'log10'")
   
        #setting vertical length of partially overlapping pixels
        ypix0 = [yy[0]-(yy[1]-yy[0])/2] + [(i+j)/2 for i,j in zip(yy[0:-1],yy[1:])]
        ypix1 = ypix0[1:] + [yy[-1]+(yy[-1]-yy[-2])/2]
        ypix1 = np.array(ypix1); ypix0 = np.array(ypix0)
        ypix1[:-1] += (ypix1[:-1]-ypix0[:-1])*overlap
        
        if yscale == 'log10':
            ypix1 = [10**i for i in ypix1]
            ypix0 = [10**i for i in ypix0]
        
        dx = (x[1]-x[0])/2
        
        ims = [axx.imshow(img[i:i+1],origin='lower',aspect='auto',extent=[x[0]-dx,x[-1]+dx,ypix0[i],ypix1[i]],\
            norm=norm(vmin = vmin, vmax = vmax),**kwargs) for i in range(NY)]

        if ax is None:
            plt.ylim([ypix0[0],ypix1[-1]])
        else:
            ax.set_ylim([ypix0[0],ypix1[-1]])
    elif raster == 'vertical':
        xx = x
        #setting horizontal length of partially overlapping pixels
        xpix0 = [xx[0]-(xx[1]-xx[0])/2] + [(i+j)/2 for i,j in zip(xx[0:-1],xx[1:])]
        xpix1 = xpix0[1:] + [xx[-1]+(xx[-1]-xx[-2])/2]
        xpix1 = np.array(xpix1); xpix0 = np.array(xpix0)
        xpix1[:-1] += (xpix1[:-1]-xpix0[:-1])*overlap
        
        dy = (y[1]-y[0])/2
        
        ims = [axx.imshow(img[:,i:i+1],origin='lower',aspect='auto',extent=[xpix0[i],xpix1[i],y[0]-dy,y[-1]+dy,],\
            norm=norm(vmin = vmin, vmax = vmax),**kwargs) for i in range(NX)]

        if ax is None:
            plt.xlim([xpix0[0],xpix1[-1]])
        else:
            ax.set_ylim([xpix0[0],xpix1[-1]])

    else:
        raise ex

    return ims

def coloredlineplot(x,y,z,cmap,vmin=None,vmax=None,plot_func=None,**kwargs):
    """
    As contourplot but plots the coloured contour along a curve/trajectory
    (x,y) : trajectory coordinates 
    z : corresponding value the will be rendered with a color
    """
    
    if vmin is None : vmin = np.min(z)
    if vmax is None : vmax = np.max(z)
    if plot_func is None: plot_func = plt.plot 

    from .palette_tools import get_color_from_value
    cc = get_color_from_value(z,cmap,vmin=vmin,vmax=vmax)
    for i in range(len(x)-1):
        xi = x[i:i+1+1]
        yi = y[i:i+1+1]
        ci = cc[i]
        #ci = colors[i]
        plot_func(xi, yi, color=ci,**kwargs)# linestyle='solid', linewidth='10')
    
def coloredwidthlineplot(x,y,z,cmap,vmin=None,vmax=None,wmin=1,wmax=4,plot_func=None,**kwargs):
    """
    As contourplot but plots the coloured contour along a curve/trajectory
    with increasing width with color value
    (x,y) : trajectory coordinates 
    z : corresponding value the will be rendered with a color
    """
    
    if vmin is None : vmin = np.min(z)
    if vmax is None : vmax = np.max(z)
    if plot_func is None: plot_func = plt.plot 

    from .palette_tools import get_color_from_value
    cc = get_color_from_value(z,cmap,vmin=vmin,vmax=vmax)
    ww = z-np.min(z); ww /= np.max(ww); ww = ww*(wmax-wmin) + wmin
    for i in range(len(x)-1):
        xi = x[i:i+1+1]
        yi = y[i:i+1+1]
        ci = cc[i]
        wi=ww[i]
        #ci = colors[i]
        plot_func(xi, yi, color=ci,lw=wi,**kwargs)# linestyle='solid', linewidth='10')

def plot_colorline(x, y, z=None,ax=None, cmap=plt.get_cmap('copper'), norm=plt.Normalize(0.0, 1.0),
        linewidth=3, alpha=1.0, update_xylim = True):
    """
    http://nbviewer.ipython.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb
    http://matplotlib.org/examples/pylab_examples/multicolored_line.html
    Plot a colored line with coordinates x and y
    Optionally specify colors in the array z
    Optionally specify a colormap, a norm function and a line width
    """

    import matplotlib.collections as mcoll
    import matplotlib.path as mpath

    path = mpath.Path(np.column_stack([x, y]))
    verts = path.interpolated(steps=1).vertices
    x, y = verts[:, 0], verts[:, 1]

    # Default colors equally spaced on [0,1]:
    if z is None:
        z = np.linspace(0.0, 1.0, len(x))

    else:
        z = np.asarray(z)-np.min(z)
        z = z/z.max()
    ## Special case if a single number:
    #if not hasattr(z, "__iter__"):  # to check for numerical input -- this is a hack
    #    z = np.array([z])

    #z = np.asarray(z)

    segments = make_segments(x, y)
    lc = mcoll.LineCollection(segments, array=z, cmap=cmap, norm=norm,
                              linewidth=linewidth, alpha=alpha)

    if ax is None : fig, ax = plt.subplots()
    #ax = plt.gca()
    ax.add_collection(lc)

    if update_xylim:
        ax.set_xlim([np.min(x), np.max(x)])
        ax.set_ylim([np.min(y), np.max(y)])

    return lc


def make_segments(x, y):
    """
    Create list of line segments from x and y coordinates, in the correct format
    for LineCollection: an array of the form numlines x (points per line) x 2 (x
    and y) array
    """

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    return segments


def subpolarplot(**kwargs):
    return plt.subplots(subplot_kw = {'projection': 'polar'},**kwargs)


class multiplot():
    """
    Class to mimic the !p.multi option of idl
    takes all the arguments of pylab.subplots and cycles through the axes
    """
    def __init__(self,*args,**kwargs):

        self.fig,self.ax = plt.subplots(*args,**kwargs)
        
        self.naxes = self.ax.size

        self.iax=0

    def plot(self,overplot = False, *args,**kwargs):

        it = self.iax
        if not overplot: self.ax.flatten()[it].cla()
        self.iax +=1
        self.iax = self.iax % self.naxes
        return self.ax.flatten()[it].plot(*args,**kwargs)
        

    def imshow(self,overplot = False, *args,**kwargs):

        it = self.iax
        if not overplot: self.ax.flatten()[it].cla()
        self.iax +=1
        self.iax = self.iax % self.naxes
        return self.ax.flatten()[it].imshow(*args,**kwargs)


def plot_slice(xra,yra,zra,slicing,ax,**kwargs):

    x=np.linspace(xra[0],xra[1],100)
    y=np.linspace(yra[0],yra[1],100)
    z=np.linspace(zra[0],zra[1],100)

    if slicing == 'x':
        Y,Z = np.meshgrid(y,z)
        X = np.zeros(Y.shape)
        X[:,:] = xra[0]
    
    if slicing == 'y':
        X,Z = np.meshgrid(x,z)
        Y = np.zeros(X.shape)
        Y[:,:] = yra[0]
    
    if slicing == 'z':
        X,Y = np.meshgrid(x,y)
        Z = np.zeros(X.shape)
        Z[:,:] = zra[0]

    ax.plot_surface(X,Y,Z,**kwargs)


def imshow_pix(x,y,z,**kwargs):

    nx,ny = z.shape
    vmin=z.min()
    vmax=z.max()
    for i in range(nx):
        for j in range(ny):
            plt.imshow(z[i,j].reshape(1,1),vmin=vmin,vmax=vmax,extent = [x[i],x[i+1],y[i],y[i+1]],**kwargs)


def shade_surf(X,Y=None,Z=None,ax=None,fig = None, **kwargs):
    if fig is None and ax is None:
        fig = plt.figure()
    if ax is None:
        ax = fig.subplots(subplot_kw={"projection": "3d"})
    if Y is None:
        Z = X
        X,Y = np.meshgrid(np.arange(Z.shape[1]),np.arange(Z.shape[0]))
    ax.plot_surface(X,Y,Z,**kwargs)    
    return fig,ax

def plot3D(X,Y,Z,ax = None,fig = None,**kwargs):
    if fig is None and ax is None:
        fig = plt.figure()
    if ax is None:
        ax = fig.subplots(subplot_kw={"projection": "3d"})
    ax.plot3D(X,Y,Z,**kwargs)
    return fig,ax

def image_label(X,*args,ax =None, fig = None,fill=True,**kwargs):

    if fig is None:
        fig,ax = plt.subplots()
    if ax is None:
        ax = fig.add_subplot()

    contour = getattr(ax,'contourf') if fill else getattr(ax,'contour')

    if len(args) == 1: return fig,ax,contour(X,*args,**kwargs)


    Y = args[0]
    Z = args[1]
    levs = args[2] if len(args) == 3 else None
    nx = X.shape[0]
    ny = Y.shape[0]
    if levs is not None and 'cmap' in kwargs:
        if type(kwargs['cmap']) is str:
            kwargs['cmap'] = getattr(plt.cm,kwargs['cmap'])
        cols = ept.get_palette(ncolors=np.size(levs),cmap=kwargs['cmap'])
        del kwargs['cmap']
        kwargs['colors'] = cols
    return fig,ax,contour(X[None,:]*np.ones((ny,nx)),Y[:,None]*np.ones((ny,nx)),\
        Z.transpose(),levs,**kwargs)


def plot3Disosurface(fld,iso_val,spacing=(0.1,0.1,0.1),fig=None,ax=None):
    from skimage import measure
    from mpl_toolkits.mplot3d import Axes3D
   
    if fig is None:
        fig,ax = plt.subplots()
    if ax is None:
        ax = fig.add_subplot()
   
    
    verts, faces,_,_ = measure.marching_cubes(fld, iso_val, spacing=spacing)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_trisurf(verts[:, 0], verts[:,1], faces, verts[:, 2],
                    cmap='Spectral', lw=1)

    return fig,ax
