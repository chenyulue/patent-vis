from typing import Optional, Literal

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.text import Annotation
from matplotlib.transforms import Transform, Bbox


def text_set_autofit(
    ax: plt.Axes,
    txt,
    xy: tuple[float, float],
    width: float, height: float,
    *,
    transform: Optional[Transform] = None,
    ha: Literal['left', 'center', 'right'] = 'center',
    va: Literal['left', 'center', 'right'] = 'center',
    **kwargs,
):
    if transform is None:
        transform = ax.transData

    #  Different alignments give different bottom left and top right anchors.
    x, y = xy
    xa0, xa1 = {
        'center': (x - width / 2, x + width / 2),
        'left': (x, x + width),
        'right': (x - width, x),
    }[ha]
    ya0, ya1 = {
        'center': (y - height / 2, y + height / 2),
        'bottom': (y, y + height),
        'top': (y - height, y),
    }[va]
    a0 = xa0, ya0
    a1 = xa1, ya1

    x0, y0 = transform.transform(a0)
    x1, y1 = transform.transform(a1)
    # rectangle region size to constrain the text in pixel
    rect_width = x1 - x0
    rect_height = y1 - y0

    fontsize = txt.get_fontsize()
    
    bbox: Bbox = txt.get_window_extent(ax.get_figure().canvas.get_renderer())
    print(txt.get_text(), bbox.width)
    adjusted_size = fontsize * rect_width / bbox.width
    txt.set_fontsize(adjusted_size)

    return txt

def text_with_autofit(
    ax: plt.Axes,
    txt: str,
    xy: tuple[float, float],
    width: float, height: float,
    *,
    transform: Optional[Transform] = None,
    ha: Literal['left', 'center', 'right'] = 'center',
    va: Literal['left', 'center', 'right'] = 'center',
    show_rect: bool = False,
    **kwargs,
):
    if transform is None:
        transform = ax.transData

    #  Different alignments give different bottom left and top right anchors.
    x, y = xy
    xa0, xa1 = {
        'center': (x - width / 2, x + width / 2),
        'left': (x, x + width),
        'right': (x - width, x),
    }[ha]
    ya0, ya1 = {
        'center': (y - height / 2, y + height / 2),
        'bottom': (y, y + height),
        'top': (y - height, y),
    }[va]
    a0 = xa0, ya0
    a1 = xa1, ya1

    x0, y0 = transform.transform(a0)
    x1, y1 = transform.transform(a1)
    # rectangle region size to constrain the text in pixel
    rect_width = x1 - x0
    rect_height = y1 - y0

    fig: plt.Figure = ax.get_figure()
    dpi = fig.dpi
    rect_height_inch = rect_height / dpi
    # Initial fontsize according to the height of boxes
    fontsize = rect_height_inch * 72

    text: Annotation = ax.annotate(txt, xy, ha=ha, va=va, xycoords=transform, **kwargs)

    # Adjust the fontsize according to the box size.
    text.set_fontsize(fontsize)
    bbox: Bbox = text.get_window_extent(fig.canvas.get_renderer())
    adjusted_size = fontsize * rect_width / bbox.width
    text.set_fontsize(adjusted_size)

    if show_rect:
        rect = mpatches.Rectangle(a0, width, height, fill=False, ls='--')
        ax.add_patch(rect)

    return text


def on_draw(event):
	import matplotlib as mpl
	fig = event.canvas.figure
	
	for ax in fig.axes:
		for artist in ax.get_children():
			if isinstance(artist, mpl.text.Text):
				text_set_autofit(ax, artist, (0.5, 0.5), 0.4, 0.4)
				
	
	func_handles = fig.canvas.callbacks.callbacks[event.name]
	fig.canvas.callbacks.callbacks[event.name] = {}
	
	fig.canvas.draw()
	
	fig.canvas.callbacks.callbacks[event.name] = func_handles

def main() -> None:
    fig, ax = plt.subplots(2, 1)

    # In the box with the width of 0.4 and the height of 0.4 at (0.5, 0.5), add the text.
    text_with_autofit(ax[0], "Hello, World! How are you?1", (0.5, 0.5), 0.4, 0.4, show_rect=True)

    # In the box with the width of 0.6 and the height of 0.4 at (0.5, 0.5), add the text.
    text_with_autofit(ax[1], "Hello, World! How are you?2", (0.5, 0.5), 0.6, 0.4, show_rect=True)
    
    fig.canvas.mpl_connect('draw_event', on_draw)
    
    plt.show()


if __name__ == '__main__':
    main()