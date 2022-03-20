# -*- coding: utf-8 -*-

import matplotlib.patches as mpatches
import matplotlib.text as mtext
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from mpl.extension.extension import extension

# Refrence https://stackoverflow.com/questions/48079364/wrapping-text-not-working-in-matplotlib
# and https://stackoverflow.com/questions/50742503/how-do-i-get-the-height-of-a-wrapped-text-in-matplotlib
class WrapText(mtext.Text):
    def __init__(self,
                 x=0, y=0, text='',
                 width=0,
                 **kwargs):
        mtext.Text.__init__(self,
                 x=x, y=y, text=text,
                 wrap=True,
                 **kwargs)
        self.width = width  # in screen pixels. You could do scaling first

    def _get_wrap_line_width(self):
        return self.width
    
    def get_lines_num(self):
        lines_length = [len(l) for l in self._get_wrapped_text().split('\n')]
        ratio = max(lines_length) / sum(lines_length)
        return len(lines_length), ratio
    

class WrapAnnotation(mtext.Annotation):
    def __init__(self,
                 text, xy,
                 width, **kwargs):
        mtext.Annotation.__init__(self, 
                                  text=text,
                                  xy=xy,
                                  wrap=True,
                                  **kwargs)
        self.width = width
        
    def _get_wrap_line_width(self):
        return self.width
    
    def get_lines_num(self):
        lines_length = [len(l) for l in self._get_wrapped_text().split('\n')]
        ratio = max(lines_length) / sum(lines_length)
        return len(lines_length), ratio


def text_with_autofit(self, txt, xy, width, height, *, 
                      transform=None, 
                      ha='center', va='center',
                      wrap=False, show_rect=False,
                      min_size=1, adjust=0,
                      **kwargs):
    if transform is None:
        if isinstance(self, Axes):
            transform = self.transData
        if isinstance(self, Figure):
            transform = self.transFigure
        
        
    x_data = {'center': (xy[0] - width/2, xy[0] + width/2), 
            'left': (xy[0], xy[0] + width),
            'right': (xy[0] - width, xy[0])}
    y_data = {'center': (xy[1] - height/2, xy[1] + height/2),
            'bottom': (xy[1], xy[1] + height),
            'top': (xy[1] - height, xy[1])}
    
    (x0, y0) = transform.transform((x_data[ha][0], y_data[va][0]))
    (x1, y1) = transform.transform((x_data[ha][1], y_data[va][1]))
    # rectange region size to constrain the text
    rect_width = x1 - x0
    rect_height = y1- y0
    
    fig = self.get_figure() if isinstance(self, Axes) else self
    dpi = fig.dpi
    rect_height_inch = rect_height / dpi
    fontsize = rect_height_inch * 72

    if isinstance(self, Figure):
        if not wrap:
            text = self.text(*xy, txt, ha=ha, va=va, transform=transform, 
                             fontsize=min_size, 
                             **kwargs)
        else:
            fontsize /= 2
            text = WrapText(*xy, txt, width=rect_width, ha=ha, va=va,
                            transform=transform, fontsize=fontsize,
                            **kwargs)
            self.add_artist(text)
            
    if isinstance(self, Axes):
        if not wrap:
            text = self.annotate(txt, xy, ha=ha, va=va, xycoords=transform,
                                 **kwargs)
        else:
            fontsize /= 2
            text = WrapAnnotation(txt, xy, ha=ha, va=va, xycoords=transform,
                                  width=rect_width, 
                                  **kwargs)
            self.add_artist(text)
    
    adjust = adjust
    while fontsize > min_size:
        text.set_fontsize(fontsize)
        bbox = text.get_window_extent(fig.canvas.get_renderer())
        line_num, ratio = text.get_lines_num() if wrap else (1,1)
        bbox_width = adjust * bbox.width * ratio
        bbox_height = bbox.height * line_num
        if bbox_width <= rect_width and bbox_height <= rect_height:
            while bbox_width <= rect_width and bbox_height <= rect_height:
                fontsize += 1
                text.set_fontsize(fontsize)
                bbox = text.get_window_extent(fig.canvas.get_renderer())
                line_num, ratio = text.get_lines_num() if wrap else (1,1)
                bbox_height = bbox.height * line_num
                bbox_width = adjust * bbox.width * ratio
            else:
                fontsize -= 1
                break;
        
        fontsize /= 2      
    
    text.set_fontsize(fontsize if fontsize > min_size else min_size)
    
    if show_rect and isinstance(self, Axes):   
        rect = mpatches.Rectangle((x_data[ha][0], y_data[va][0]), 
                                  width, height, fill=False, ls='--')
        self.add_patch(rect)
        
    return text

@extension(Figure)
class FigureExt:
    def text_with_autofit(self, txt, xy, width, height, *, 
                          transform=None, 
                          ha='center', va='center',
                          wrap=False, show_rect=False,
                          min_size=1, adjust=0,
                          **kwargs):
        return text_with_autofit(self, txt, xy, width, height, 
                              transform=transform, 
                              ha=ha, va=va,
                              wrap=wrap, show_rect=show_rect,
                              min_size=min_size, adjust=adjust,
                              **kwargs)
    
@extension(Axes)
class AxesExt:
    def annotate_with_autofit(self, txt, xy, width, height, *, 
                              transform=None, 
                              ha='center', va='center',
                              wrap=False, show_rect=False,
                              min_size=1, adjust=0,
                              **kwargs):
        return text_with_autofit(self, txt, xy, width, height, 
                              transform=transform, 
                              ha=ha, va=va,
                              wrap=wrap, show_rect=show_rect,
                              min_size=min_size, adjust=adjust,
                              **kwargs)
    
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(constrained_layout=True)
    
    ax.set_xlim([0,10])
    ax.set_ylim([0,10])
    
    txt = ax.annotate_with_autofit('Hello, World! How are you?', (5,5), 5, 2,
                            show_rect=True, wrap=True, 
                            ma='left', fontweight='bold', 
                            adjust=1)
    #txt.set_text('你好世界！ 你 过得 怎样？')
    
    plt.show()


