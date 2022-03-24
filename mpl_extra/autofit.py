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
    show_rect=False,
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
    if width < 0 or height < 0:
        raise ValueError('`width` and `height` should be a number >= 0.')
    
    if transform is None:
        transform = txtobj.get_transform()
    
    # Get the width and height of the box in pixels.
    width_in_pixels, height_in_pixels = dist2pixels(transform, width, height)
    
    render = txtobj.axes.get_figure().canvas.get_renderer()
    rotation = txtobj.get_rotation()
    fontsize = txtobj.get_fontsize()
    
    # Set the rotation of the text to be zero so that the bbox reflects the 
    # width and height of the rendered text
    bbox = txtobj.get_window_extent(render)
    
    adjusted_fontsize = min(fontsize * width_in_pixels / bbox.width,
                            fontsize * height_in_pixels / bbox.height)
    
    txtobj.set_fontsize(adjusted_fontsize)
    
    if show_rect: 
        # Get the position of the text in pixels.    
        x0, y0 = txtobj.get_position()
        ha, va = txtobj.get_horizontalalignment(), txtobj.get_verticalalignment()
        
        # Transform the text position into the position in the current coordinates.
        x0, y0 = transform.inverted().transform(
            txtobj.get_transform().transform((x0, y0))
        )
        
        xa0 = {
            'center': x0 - width / 2,
            'left': x0,
            'right': x0 - width,
        }[ha]
        ya0 = {
            'center': y0 - height / 2,
            'bottom': y0,
            'top': y0 - height,
            'baseline': y0,
            'center_baseline': y0 - height / 2,
        }[va]
        
        rect = mpatches.Rectangle((xa0, ya0), width, height, angle=rotation,
                                  fill=False, ls='--', transform=transform)
        txtobj.axes.add_patch(rect)
        
        return txtobj, rect
        
    return txtobj
        
        
        
def dist2pixels(transform, dist, *dists):
    """Get the distance in pixels for a specific distance with the transformer
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
    results = []
    
    for i in range(0, len(params), 2):
        point = params[i:i+2]
        end_point = point + (0,) if len(point) == 1 else point
        end_point = transform.transform(end_point)
        results.extend((end_point - start_point)[:-1] if len(point) == 1 else (end_point - start_point))
         
    return results


def pixels2dist(transform, dist, *dists):
    """The inverse function of dist2pixels.

    Parameters
    ----------
    transform : Transform
        The transformer to use
    dist : float
        The distance in pixels
        
    Other Parameters
    ----------------
    *dists: float
    
    Returns
    -------
    list of float, corresponding to the arguments passed into the function.
    """
    return dist2pixels(transform.inverted(), dist, *dists)