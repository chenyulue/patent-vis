
from matplotlib.container import Container

class TreemapContainer(Container):
    '''
    Container for the artist of treemap plots (e.g. created by `.Axes.bar`)

    The container contains a tuple of the *patches* themselves as well as some
    additoinal attributes.

    Attributes
    ----------
    patches: list of list of :class:`~matplotlib.patches.Rectangle`
        The artists of the rectangles corresponding to different levels
    
    datavalues: None or array-like
        The underlying data values corresponding to the bars

    levels: int
        The treemap levels
    '''
    def __init__(self, patches, texts, *, 
                 handles=None, mappable=None,
                 datavalues=None, colornorm=None,**kwargs):
        self.patches = patches
        self.texts = texts
        self.handles = handles
        self.mappable = mappable
        self.datavalues = datavalues
        self.colornorm = colornorm
        super().__init__(patches, **kwargs)