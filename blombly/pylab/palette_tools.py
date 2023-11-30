import pylab as plt
mpl = plt.mpl
import numpy as np


def get_palette(ncolors=255, start=0.,stop=1.,cmap=mpl.cm.jet):
    """
    ADAPTED FROM AN EXAMPLE I FOUND ON INTERNET
        import matplotlib.pyplot as plt
        
        from matplotlib import cm
        from numpy import linspace
        
        start = 0.0
        stop = 1.0
        number_of_lines= 1000
        cm_subsection = linspace(start, stop, number_of_lines) 
        
        colors = [ cm.jet(x) for x in cm_subsection ]
        
        for i, color in enumerate(colors):
            plt.axhline(i, color=color)
        
            plt.ylabel('Line Number')
            plt.show()
    """
    

    cm_subsection = np.linspace(start, stop, ncolors) 
    return [ cmap(x) for x in cm_subsection ]


def get_color_from_value(x,cmap,vmin=0,vmax=255):

    return cmap((x - vmin)/(vmax-vmin))

class MidpointNormalize(mpl.colors.Normalize):
    
    def __init__(self, vmin, vmax, midpoint=0, clip=False):
        self.midpoint = midpoint
        mpl.colors.Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        import scipy as sp 
        normalized_min = max(0, 1 / 2 * (1 - abs((self.midpoint - self.vmin) / (self.midpoint - self.vmax))))
        normalized_max = min(1, 1 / 2 * (1 + abs((self.vmax - self.midpoint) / (self.midpoint - self.vmin))))
        normalized_mid = 0.5
        x, y = [self.vmin, self.midpoint, self.vmax], [normalized_min, normalized_mid, normalized_max]
        return sp.ma.masked_array(sp.interp(value, x, y))

class MidpointNormalize_custom(mpl.colors.Normalize):
    
    def __init__(self, vmin, vmax, midpoint=0,func=None, clip=False):
        self.midpoint = midpoint
        self.func=func
        mpl.colors.Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        import scipy as sp 
        normalized_min = max(0, 1 / 2 * (1 - abs((self.midpoint - self.vmin) / (self.midpoint - self.vmax))))
        normalized_max = min(1, 1 / 2 * (1 + abs((self.vmax - self.midpoint) / (self.midpoint - self.vmin))))
        normalized_mid = 0.5
        x, y = [self.vmin, self.midpoint, self.vmax], [normalized_min, normalized_mid, normalized_max]
        if self.func is None :
            return sp.ma.masked_array(sp.interp(value, x, y))
        return self.func(sp.ma.masked_array(sp.interp(value, x, y)))


class MidpointNormalize_log(mpl.colors.LogNorm):

    def __init__(self, vmin, vmax,func=None, clip=False):
        #self.midpoint = midpoint
        self.func=func
        mpl.colors.LogNorm.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        if clip is None:
            clip = self.clip

        result, is_scalar = self.process_value(value)

        result = np.ma.masked_less_equal(result, 0, copy=False)

        self.autoscale_None(result)
        #self._check_vmin_vmax()
        vmin, vmax = self.vmin, self.vmax
        if vmin == vmax:
            result.fill(0)
        else:
            if clip:
                mask = np.ma.getmask(result)
                result = np.ma.array(np.clip(result.filled(vmax), vmin, vmax),
                                     mask=mask)
            # in-place equivalent of above can be much faster
            resdat = result.data
            mask = result.mask
            if mask is np.ma.nomask:
                mask = (resdat <= 0)
            else:
                mask |= resdat <= 0
            np.copyto(resdat, 1, where=mask)
            np.log(resdat, resdat)
            resdat -= np.log(vmin)
            resdat /= (np.log(vmax) - np.log(vmin))
            result = np.ma.array(resdat, mask=mask, copy=False)
        if is_scalar:
            result = result[0]
        if self.func is None :
            return result
        else:
            return self.func(result)

# In what follows is a set of functions that map the domain [0,1] to [0,1]  (for palette purposes)

def raised_cosine(x):
    """ Returns a raised cosine of np.pi*x
        i.e. (-cos(np.pi*x)+1)/2.
    """
    return (-np.cos(np.pi*x)+1)/2

def mirror_sqrt(x):
    """ Returns the mirrored sqrt of x 
       sqrt( | 2 * (x -0.5) |)* sign(x-0.5) +1)/2 
    """
    return    (np.sqrt( np.abs( 2 * (x -0.5) ))* np.sign(x-0.5) +1)/2 
def raised_sqrtcosine(x):
    """ Returns a raised cosine of np.pi*x
    """
    return (np.sign(x-0.5) * np.sqrt(np.abs(np.sin(np.pi*(x-0.5)))) +1 )/2.
def raised_squarecosine(x):
    """ Returns a raised cosine of np.pi*x
    """
    return (np.sign(x-0.5) * (np.abs(np.sin(np.pi*(x-0.5))))**2 +1 )/2.

#colormap functions taken from https://gist.githubusercontent.com/KerryHalupka
# see  https://towardsdatascience.com/beautiful-custom-colormaps-with-matplotlib-5bab3d1f0e72


def hex_to_rgb(value):
    '''
    Converts hex to rgb colours
    value: string of 6 characters representing a hex colour.
    Returns: list length 3 of RGB values'''
    value = value.strip("#") # removes hash symbol if present
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_dec(value):
    '''
    Converts rgb to decimal colours (i.e. divides each value by 256)
    value: list (length 3) of RGB values
    Returns: list (length 3) of decimal values'''
    return [v/256 for v in value]


def get_continuous_cmap(color_list, float_list=None):
    ''' creates and returns a color map that can be used in heat map figures.
        If float_list is not provided, colour map graduates linearly between each color in hex_list.
        If float_list is provided, each color in hex_list is mapped to the respective location in float_list. 
        
        Parameters
        ----------
        hex_list: list of hex code strings or rgb triplets
        float_list: list of floats between 0 and 1, same length as hex_list. Must start with 0 and end with 1.
        
        Returns
        ----------
        colour map'''
    mcolors = mpl.colors
    #CHECK IF color_list is a list of rgb triplets or hex string
    rgb_list = color_list
    for i,ic in enumerate(rgb_list):
        if type(ic) is str: rgb_list[i] = hex_to_rgb(ic)
    rgb_list = [rgb_to_dec(i) for i in rgb_list]
    #rgb_list = [rgb_to_dec(hex_to_rgb(i)) for i in hex_list]
    if float_list:
        pass
    else:
        float_list = list(np.linspace(0,1,len(rgb_list)))
        
    cdict = dict()
    for num, col in enumerate(['red', 'green', 'blue']):
        col_list = [[float_list[i], rgb_list[i][num], rgb_list[i][num]] for i in range(len(float_list))]
        cdict[col] = col_list
    cmp = mcolors.LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=256)
    return cmp

def fancy_cmap():
    hex_list = ['#0091ad', '#3fcdda', '#83f9f8', '#d6f6eb', '#fdf1d2', '#f8eaad', '#faaaae', '#ff57bb']
    return get_continuous_cmap(hex_list)




def show_cmap(cmapin,  figsize = ( 4 , 1) ,**kwargs):

    def plot_cmap(cmap,ax):
        col_map = plt.get_cmap(cmap)
        plt.mpl.colorbar.ColorbarBase(ax,cmap=col_map, orientation = 'horizontal')

    fig,ax = plt.subplots(figsize=figsize, **kwargs)
    plt.mpl.colorbar.ColorbarBase(ax,cmap=cmapin, orientation = 'horizontal')
    plt.show()

def show_available_cmaps(nrows=4, ncols=8 ,  figsize = ( 4 , 1) ,**kwargs):

    figsize = (figsize[0]*ncols,figsize[1]*nrows)
    def plot_cmap(cmap,ax):
        col_map = plt.get_cmap(cmap)
        plt.mpl.colorbar.ColorbarBase(ax,cmap=col_map, orientation = 'horizontal')

    i=0
    n=ncols*nrows
    for imap in plt.colormaps():
        if i%n == 0 : 
            #plt.tight_layout()
            fig,ax = plt.subplots(nrows,ncols,figsize=figsize, **kwargs)
            j=0
            ax=ax.flatten()
        
        print(imap)
        plot_cmap(imap,ax[j])
        ax[j].set_title(imap)
        i+=1
        j+=1
    plt.show()


def contrast_cmap(cmap,contrast=0.5):
    from matplotlib.colors import ListedColormap


# Get the colormap colors, multiply them with the factor "a", and create new colormap
    my_cmap = cmap(np.arange(cmap.N))
    my_cmap[:,0:3] *= contrast 
    return ListedColormap(my_cmap)

