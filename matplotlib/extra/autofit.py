from typing import Optional, Literal, Union

import matplotlib.patches as mpatches
import matplotlib.text as mtext
import matplotlib.transforms as mtrans


def text_with_autofit(
    txtobj,
    width, 
    height,
    *,
    wrap=False,
    transform=None,
    show_rect = False,
):
    """Auto fitting the text object into a box of width x height by adjusting
    the fontsize automaticaly.

    Parameters
    ----------
    txtobj : Text or Annotation
        The Text or Annotation object to be auto-fitted.
    width : float
        The width of the box.
    height : float
        The height of the box.
    wrap : bool, optional
        If True, the text will be auto-wrapped into the box to get a fontsize 
        as big as possible.
    transform : Transform, optional
        The transformer for the width and height. When default to None, 
        it takes the transformer of txtobj.
    show_rect : bool, optional
        If True, show the box edge for the debug purpose. Default to False.
        
    Returns
    -------
    Text or Annotation
        The auto-fitted Text or Annotation object
    """
    if transform is None:
        transform = txtobj.get_transform()
    
    # Get the position of the text in pixels.    
    x0, y0 = txtobj.get_position()
    ha, va = txtobj.get_horizontalalignment(), txtobj.get_vercitalalignment()
    
    # Get the width and height of the box in pixels.
    width_in_pixels, height_in_pixels = length2pixels(transform, width, height)
        
        
        
def length2pixels(transform, dist, *dists):
    """Get the length in pixels for a specific length with the transformer
    specified by tranform.

    Parameters
    ----------
    transform : Transform
        The transformer to use.
    dist : float
        The distance between two points.
    
    Other Parameters
    ----------------
    *dists: float
    
    Returns
    -------
    list of float, corresponding to the arguments passed into the function.
    """    
    params = (dist,) + dists
    start_point = transform.transform((0,0))
    
    if len(dist) == 2:
        return transform.transform((params[0], params[1])) - start_point
    
    x0, y0 = start_point
    results = []
    
    for distance in params:
         x1, _ = transform.transform((distance, 0))
         results.append(x1 - x0)
         
    return results