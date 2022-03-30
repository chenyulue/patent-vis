import math
import textwrap
import re

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
    fontsize = txtobj.get_fontsize()
    
    bbox = txtobj.get_window_extent(render)
    
    adjusted_fontsize = min(fontsize * width_in_pixels / bbox.width,
                            fontsize * height_in_pixels / bbox.height)
    
    txtobj.set_fontsize(adjusted_fontsize)
    
    if show_rect: 
        # Get the position of the text bounding box in pixels.    
        x0, y0, *_ = txtobj.get_window_extent(render).bounds
        
        # Transform the box position into the position in the current coordinates.
        x0, y0 = transform.inverted().transform((x0, y0))
        
        rect = mpatches.Rectangle(
            (x0, y0), 
            width, 
            height, 
            fill=False, ls='--', transform=transform)
        txtobj.axes.add_patch(rect)
        
        return txtobj, rect
        
    return txtobj
        

def text_with_autowrap(
    txtobj,
    width,
    height,
    *,
    transform=None,
    show_rect=False
):
 
    import textwrap
       
    if width < 0 or height < 0:
        raise ValueError('`width` and `height` should be a number >= 0.')
    
    if txtobj.get_rotation():
        raise ValueError('`wrap` option only supports the text object with a 0 rotation.')
    
    if transform is None:
        transform = txtobj.get_transform()
        
    # Get the width and height of the box in pixels.
    width_in_pixels, height_in_pixels = dist2pixels(transform, width, height)
    
    render = txtobj.axes.get_figure().canvas.get_renderer()
    dpi = txtobj.axes.get_figure().get_dpi()
    max_fontsize = pixels2points(
        dpi,
        height_in_pixels
        )
    
    txtobj.set_fontsize(max_fontsize)
    bbox = txtobj.get_window_extent(render)
    
    if bbox.width <= width_in_pixels:
        return txtobj
    
    line_num = 2
    aspect_ratio = bbox.width / len(txtobj.get_text()) / bbox.height  # This varies with the font!!
    while True:
        scaled_fontsize_in_pixels = calc_fontsize_in_pixels(
            height_in_pixels, 
            line_num, 
            txtobj._linespacing
            )
        pixels_per_char = aspect_ratio * scaled_fontsize_in_pixels
        wrap_length = max(1, width_in_pixels // pixels_per_char)
        wrapped_text = textwrap.wrap(txtobj.get_text(), int(wrap_length))
        
        if len(wrapped_text) <= line_num:
            break
        
        line_num += 1
        
    txtobj.set_text('\n'.join(wrapped_text))
    txtobj.set_fontsize(pixels2points(
        dpi,
        scaled_fontsize_in_pixels
    ))
        
    if show_rect: 
        # Get the position of the text bounding box in pixels.    
        x0, y0, *_ = txtobj.get_window_extent(render).bounds
        
        # Transform the box position into the position in the current coordinates.
        x0, y0 = transform.inverted().transform((x0, y0))
        
        rect = mpatches.Rectangle(
            (x0, y0), 
            width, 
            height, 
            fill=False, ls='--', transform=transform)
        txtobj.axes.add_patch(rect)
        
        return txtobj, rect
    
    return txtobj


def get_wrapped_fontsize(txt, height, width, n, linespacing, aspect_ratio):
    h_fontsize_in_pixels = calc_fontsize_in_pixels(
            height, 
            n, 
            linespacing
            )
    words = split_words(txt)
    lines = ['']
    

def split_words(txt):
    regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
    matches = re.findall(regex, txt, re.UNICODE)
    return matches

def combine_words(words):
    new_words = [
        word + ' ' if (not is_Chinese(word[-1]) and (not is_Chinese(next_word[-1]))) else word
        for word, next_word in zip(words, words[1:])
    ]
    new_words.append(words[-1])
    return ''.join(new_words)

def is_Chinese(character):
    code_point = ord(character)
    return code_point >= 0x4e00 and code_point <= 0xfaff


def calc_fontsize_in_pixels(height, n, linespacing):
    """Calculate the fontsize according to the box height and wrapped lines.

    Parameters
    ----------
    height : float
        The height of the box
    n : int
        The number of wrapped lines
    linespacing : float
        The line spacing of the text.

    Returns
    -------
    float
        The fontsize
    """    
    return height / (n * linespacing - linespacing + 1)
        
        
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


def pixels2points(dpi, pixels):
    """Convert display units in pixels to points

    Parameters
    ----------
    dpi : float
        The figure dpi
    pixels : float
        The pixel numbers

    Returns
    -------
    float
        The points for fontsize, linewidth, etc.
    """    
    inch_per_point = 1 / 72
    return pixels / dpi / inch_per_point

# Refence https://stackoverflow.com/questions/4018860/text-box-with-line-wrapping-in-matplotlib
def min_dist_inside(point, rotation, box):
    """Get the space in a given direction from `point` to the boundaries of
    `box`.

    Parameters
    ----------
    point : tuple of float
        The text start point
    rotation : float
        The text angle in degrees
    box : an object with `x0`, `y0`, `x1` and `y1` attributes
        The box region
        
    Returns
    -------
    float
        The minum distance inside the box
    """ 
    pass   