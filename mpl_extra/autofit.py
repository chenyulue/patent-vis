import textwrap
import re

import matplotlib.patches as mpatches
from matplotlib.font_manager import findfont, get_font
from matplotlib.backends.backend_agg import get_hinting_flag


def text_with_autofit(
    txtobj,
    width, 
    height,
    *,
    wrap=False,
    grow=False,
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
    grow : bool, optional
        If True, the wrapped text will be as large as possbile, otherwise the 
        wrapped text will be as wide as possible.
    transform : Transform, optional
        The transformer for the width and height. When default to None, 
        it takes the transformer of txtobj.
    show_rect : bool, optional
        If True, show the box edge for the debug purpose. Default to False.
        
    Returns
    -------
    Text
        The auto-fitted Text object.
    """
    if width < 0 or height < 0:
        raise ValueError('`width` and `height` should be a number >= 0.')
    
    if wrap and (txtobj.get_rotation() % 90):
        raise ValueError('`wrap` option only supports the horizontal or vertical text object.')
    
    if transform is None:
        transform = txtobj.get_transform()
    
    # Get the width and height of the box in pixels.
    width_in_pixels, height_in_pixels = dist2pixels(transform, width, height)
    
    render = txtobj.axes.get_figure().canvas.get_renderer()
    fontsize = txtobj.get_fontsize()
    dpi = txtobj.axes.get_figure().get_dpi()
    original_txt = txtobj.get_text()
    
    bbox = txtobj.get_window_extent(render)
    
    adjusted_fontsize = min(fontsize * width_in_pixels / bbox.width,
                            fontsize * height_in_pixels / bbox.height)
    
    if wrap:
        words = split_words(original_txt)
        fontsizes = []
        
        for line_num in range(2, len(words) + 1):
            adjusted_size_txt = get_wrapped_fontsize(
                original_txt, height_in_pixels, width_in_pixels, 
                line_num, txtobj._linespacing, dpi, txtobj.get_fontproperties()
                )
            fontsizes.append(adjusted_size_txt)
        
        # grow = True, the fontsize will be as large as possible    
        if grow:
            adjusted_size, wrap_txt, _ = max(fontsizes, key=lambda x: x[0])
        # grow = False, the text will be as wide as the box
        else:
            adjusted_size, wrap_txt, _ = min(fontsizes, key=lambda x: x[2])
            
        if adjusted_fontsize < adjusted_size:
            adjusted_fontsize = adjusted_size
            txtobj.set_text('\n'.join(wrap_txt))
            
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
        

# def text_with_autowrap(
#     txtobj,
#     width,
#     height,
#     *,
#     transform=None,
#     show_rect=False
# ):
 
#     import textwrap
       
#     if width < 0 or height < 0:
#         raise ValueError('`width` and `height` should be a number >= 0.')
    
#     if txtobj.get_rotation():
#         raise ValueError('`wrap` option only supports the text object with a 0 rotation.')
    
#     if transform is None:
#         transform = txtobj.get_transform()
        
#     # Get the width and height of the box in pixels.
#     width_in_pixels, height_in_pixels = dist2pixels(transform, width, height)
    
#     render = txtobj.axes.get_figure().canvas.get_renderer()
#     dpi = txtobj.axes.get_figure().get_dpi()
    
#     bbox = txtobj.get_window_extent(render)
    
#     if bbox.width <= width_in_pixels:
#         return txtobj
    
#     words = split_words(txtobj.get_text())
#     fontsizes = []
#     for line_num in range(2, len(words) + 1):
#         adjusted_size_txt = get_wrapped_fontsize(
#             txtobj.get_text(), height_in_pixels, width_in_pixels, 
#             line_num, txtobj._linespacing, dpi, txtobj.get_fontproperties()
#         )
#         fontsizes.append(adjusted_size_txt)
    
#     # grow = True, the fontsize will be as large as possible    
#     # adjusted_size, wrap_txt, _ = max(fontsizes, key=lambda x: x[0])
#     # grow = False, the text will be as wide as the box
#     adjusted_size, wrap_txt, _ = min(fontsizes, key=lambda x: x[2])
#     txtobj.set_text('\n'.join(wrap_txt))
#     txtobj.set_fontsize(adjusted_size)
    
        
#     if show_rect: 
#         # Get the position of the text bounding box in pixels.    
#         x0, y0, *_ = txtobj.get_window_extent(render).bounds
        
#         # Transform the box position into the position in the current coordinates.
#         x0, y0 = transform.inverted().transform((x0, y0))
        
#         rect = mpatches.Rectangle(
#             (x0, y0), 
#             width, 
#             height, 
#             fill=False, ls='--', transform=transform)
#         txtobj.axes.add_patch(rect)
        
#         return txtobj, rect
    
#     return txtobj


def get_wrapped_fontsize(txt, height, width, n, linespacing, dpi, fontprops):
    """Get the fontsize according to the wrapped text.

    Parameters
    ----------
    txt : str
        A string of text
    height : float
        The height of the box in pixels
    width : float
        The width of the box in pixels
    n : int
        The line numbers
    linespacing : float
        The line spacing between the wrapped text
    dpi : float
        The dpi used to calculate the fontsize.
    fontprops : FontProperties
        The font properties used to calculate the fontsize.

    Returns
    -------
    a tuple of (float, str, float)
        returns a tuple of fontsize, the corresponding wrapped text, and the 
        gap between the wrapped text and the box edge.
    """    
    words = split_words(txt)
    min_length = max(map(len, words))
    # Keep the longest word not to be broken
    wrap_length = max(min_length, len(txt) // n)
    wrap_txt = textwrap.wrap(txt, wrap_length)
    w_fontsize = calc_fontsize_from_width(
        wrap_txt, width, dpi, fontprops
        )
    
    h_fontsize = calc_fontsize_from_height(
            height, len(wrap_txt), linespacing, dpi
            )
    
    adjusted_fontsize = min(h_fontsize, w_fontsize)
    delta_w = get_line_gap_from_boxedge(wrap_txt, adjusted_fontsize, width, dpi, fontprops)
    #print('wrapped=> ', n, h_fontsize, w_fontsize, wrap_txt)
    
    return min(h_fontsize, w_fontsize), wrap_txt, delta_w


def get_line_gap_from_boxedge(lines, fontsize, width, dpi, fontprops):
    props = fontprops
    font = get_font(findfont(props))
    font.set_size(fontsize, dpi)
    gaps = []
    for line in lines:
        font.set_text(line, 0, flags=get_hinting_flag())
        w, _ = font.get_width_height()
        w = w / 64.0 # Divide the subpixels
        gaps.append(abs(w - width))
        
    return min(gaps)
    

def split_words(txt):
    """Split a hybrid sentence with some CJK characters into a list of words,
    keeping the English words not to be broken.

    Parameters
    ----------
    txt : str
        A sentence to be splitted.

    Returns
    -------
    list of str
        a list of splitted words
    """    
    regex = r"[\u4e00-\ufaff]|[0-9]+|[a-zA-Z]+\'*[a-z]*"
    matches = re.findall(regex, txt, re.UNICODE)
    return matches


def calc_fontsize_from_width(lines, width, dpi, fontprops):
    """Calculate the fontsize according to the ling width

    Parameters
    ----------
    lines : list of str
        A list of lines.
    width : float
        The box width in pixels.
    dpi : float
        The dpi used to calculate the fontsize.
    fontprops : FontProperties
        The font properties used to calculate the fontsize.

    Returns
    -------
    float
        returns the fontsize that fits all the lines into the box.
    """    
    props = fontprops
    font = get_font(findfont(props))
    font.set_size(props.get_size_in_points(), dpi)
    fontsizes = []
    for line in lines:
        font.set_text(line, 0, flags=get_hinting_flag())
        w, _ = font.get_width_height()
        w = w / 64.0 # Divide the subpixels
        adjusted_size = props.get_size_in_points() * width / w 
        fontsizes.append(adjusted_size)
    
    #print('fontsize from width: ', fontsizes)
        
    return min(fontsizes)


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