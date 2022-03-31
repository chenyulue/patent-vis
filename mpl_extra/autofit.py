import math
import textwrap
import re

import matplotlib.patches as mpatches
import matplotlib.text as mtext
import matplotlib.transforms as mtrans
from matplotlib.font_manager import FontProperties, findfont, get_font
from matplotlib.backends.backend_agg import get_hinting_flag


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
    
    bbox = txtobj.get_window_extent(render)
    
    if bbox.width <= width_in_pixels:
        return txtobj
    
    words = split_words(txtobj.get_text())
    fontsizes = []
    for line_num in range(2, len(words) + 1):
        adjusted_size_txt = get_wrapped_fontsize(
            txtobj.get_text(), height_in_pixels, width_in_pixels, 
            line_num, txtobj._linespacing, dpi, txtobj.get_fontproperties()
        )
        fontsizes.append(adjusted_size_txt)
    
    # grow = True, the fontsize will be as large as possible    
    # adjusted_size, wrap_txt, _ = max(fontsizes, key=lambda x: x[0])
    # grow = False, the text will be as wide as the box
    adjusted_size, wrap_txt, _ = min(fontsizes, key=lambda x: x[2])
    txtobj.set_text('\n'.join(wrap_txt))
    txtobj.set_fontsize(adjusted_size)
    
        
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


def get_wrapped_fontsize(txt, height, width, n, linespacing, dpi, fontprops):
    words = split_words(txt)
    min_length = max(map(len, words))
    # Keep the longest word not to be broken
    wrap_length = max(min_length, len(txt) // n)
    wrap_txt = textwrap.wrap(txt, wrap_length)
    w_fontsize, delta_w = calc_fontsize_from_width(
        wrap_txt, width, dpi, fontprops
        )
    
    h_fontsize = calc_fontsize_from_height(
            height, len(wrap_txt), linespacing, dpi
            )
    
    #print('wrapped=> ', n, h_fontsize, w_fontsize, wrap_txt)
    
    return min(h_fontsize, w_fontsize), wrap_txt, delta_w
    

def split_words(txt):
    regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
    matches = re.findall(regex, txt, re.UNICODE)
    return matches

# def combine_words(words, length):
#     new_words = [
#         word + ' ' if (not is_Chinese(word[-1]) and (not is_Chinese(next_word[-1]))) else word
#         for word, next_word in zip(words, words[1:])
#     ]
#     new_words.append(words[-1])
    
#     line = []
#     lines = []
#     i = 0
#     for word in new_words:
#         line.append(word)
#         i += len(word)
#         if (i > length):
#             lines.append(''.join(line))
#             line = []
#             i = 0
    
#     # The last line
#     lines.append(''.join(line))
    
#     return lines

def is_Chinese(character):
    code_point = ord(character)
    return code_point >= 0x4e00 and code_point <= 0xfaff


def calc_fontsize_from_width(lines, width, dpi, fontprops):
    props = fontprops
    font = get_font(findfont(props))
    font.set_size(props.get_size_in_points(), dpi)
    fontsizes = []
    for line in lines:
        font.set_text(line, 0, flags=get_hinting_flag())
        w, _ = font.get_width_height()
        w = w / 64.0 # Divide the subpixels
        adjusted_size = props.get_size_in_points() * width / w 
        fontsizes.append((adjusted_size, abs(width - w)))
    
    #print('fontsize from width: ', fontsizes)
        
    return min(fontsizes, key=lambda x: x[0])

def calc_fontsize_from_height(height, n, linespacing, dpi):
    """Calculate the fontsize according to the box height and wrapped line numbers.

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
    h_pixels =  height / (n * linespacing - linespacing + 1)
    
    return pixels2points(dpi, h_pixels)
        
        
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