import random, copy
from Tkinter   import *

def ensure_playing(f):
    def inner(self, *args, **kwargs):
        if not self.playing:
            return None
        else:
            return f(self, *args, **kwargs)
    return inner


class Tetris:

    box_size    = 20
    rows        = 22
    cols        = 12
    game_width  = cols * box_size
    game_height = rows * box_size
    x_margin    = 2 * box_size
    y_margin    = 2 * box_size
    win_width   = 2 * x_margin + game_width + 120
    win_height  = 2 * y_margin + game_height
    col_zero    = x_margin
    row_zero    = y_margin
    
    pieces = {'S': [(1, 0),(1, 1),(0, 1),(0, 2)],
              'T': [(1, 0),(0, 1),(1, 1),(1, 2)],
              'I': [(1, 0),(1, 1),(1, 2),(1, 3)],
              'Q': [(1, 1),(1, 2),(0, 1),(0, 2)],
              'L': [(0, 0),(1, 0),(1, 1),(1, 2)],
              'J': [(0, 2),(1, 0),(1, 1),(1, 2)],
              'Z': [(0, 0),(0, 1),(1, 1),(1, 2)]}
    
    colors = ['blue', 'yellow', 'green', 'orange', 'purple', 'red']

    class Piece:
        def __init__(self, rects, color, name):
            self.rects = rects
            self.color = color
            self.name  = name
    
    def __init__(self):
        self.root = Tk()
        self.root.geometry('{width}x{height}'.format(width=Tetris.win_width,
                                                     height=Tetris.win_height))
        self.root.resizable(width = False, height = False)
        self.root.title('Tetris')
        self.root.bind('<Up>',    self._on_up)
        self.root.bind('<Down>',  self._on_down)
        self.root.bind('<Left>',  self._on_left)
        self.root.bind('<Right>', self._on_right)
        self.root.bind('<space>', self._on_space)
        
        self._init_ui()
        self._play_game()

    def _init_ui(self):
        self.canvas = Canvas(self.root, bg = 'black', width = 480, height = 500)
        self.canvas.create_rectangle(Tetris.row_zero - 5,
                                     Tetris.col_zero - 5,
                                     Tetris.row_zero + Tetris.game_width  +5,
                                     Tetris.col_zero + Tetris.game_height +5,
                                     fill = '', outline= 'blue', width = 5)

        horiz = Tetris.col_zero + Tetris.box_size * Tetris.cols + 20
        self.canvas.pack()

    def _play_game(self):
        """
        Reset the game and clear memory 
        """
        self.bottom  = {}
        self.playing = True
        self.paused  = False
        self.score   = 0
        self.gravity = 500
        self._next_piece = self._get_new_piece()
        self._set_falling()
        self._drop()
        self._refresh_score()
        self._refresh_falling()
        self._refresh_bottom()

    def _set_falling(self):
        """
        Reset falling piece and next piece
        """
        self._falling    = self._next_piece
        self._next_piece = self._get_new_piece()
        self._center_piece(self._falling)
        self._refresh_next()

    def _get_new_piece(self):
        """
        Get a new piece at random 
        """
        name  = random.choice(Tetris.pieces.keys())
        color = random.choice(Tetris.colors)
        return self.Piece(Tetris.pieces[name], color, name)

    def _center_piece(self, piece, x0=None, y0=None):
        """
        Center piece on canvas 
        """
        if not x0:
            x0 = 1
        if not y0:
            y0 = -1 + Tetris.cols / 2.0
        piece.rects = [(x + x0, y + y0) for x, y in piece.rects]
    
    @ensure_playing
    def _on_up(self, event):
        """
        Handle up click 
            - Rotate the piece if possible 
        """
        vals = self._get_rotated(self._falling)
        if vals:
            self._falling.rects = vals

    @ensure_playing
    def _on_down(self, event):
        """
        Handle down click 
            - Move piece all the way to bottom if possible 
        """
        while True:
            vals = self._get_translated(self._falling, dx=1, dy=0)
            if not vals:
                break 
            self._falling.rects = vals
            
    @ensure_playing
    def _on_left(self, event):
        """
        Handle left click
            - Should move falling piece one unit left if possible
        """
        vals = self._get_translated(self._falling, dx=0, dy=-1)
        if vals:
            self._falling.rects = vals

    @ensure_playing
    def _on_right(self, event):
        """
        Handle right click
            - Should move falling piece one unit right if possible 
        """
        vals = self._get_translated(self._falling, dx=0, dy= 1)
        if vals:
            self._falling.rects = vals

    @ensure_playing
    def _on_space(self, event):
        """
        Handle spacebar click
            - Should pause or unpause the game depending on state of self.paused
        """
        self.paused = not self.paused
        if self.paused:
            self._refresh_falling()

    def _drop(self):
        """
        Drop piece down one row, and update according to fps
            - First check that we can drop, 

        Note: inside this method, dx should always be 1. Piece will start to fall faster
              at score mod(400) == 0 by shortening time between _drop execution
        """
        if self.playing:
            vals = self._get_translated(self._falling, dx=1, dy=0)
            #`_get_translated` might have changed the value of `self.playing`.
            #TODO: will `_process_bottom` ever change `self.playing`?
            if self.playing and not vals:
                self._process_bottom()
            if self.playing and vals:
                self._falling.rects = vals
    
        self.root.after(self.gravity, self._drop)

    def _process_bottom(self):
        """
        If we've hit bottom, iterate through rows and drop if we have a complete row
        """
        for x, y in self._falling.rects:
            self.bottom[x, y] = self._falling.color

        for x in range(Tetris.rows):
            self._drop_row(x)
        
        self._refresh_bottom()
        self._set_falling()

    def _check_complete(self, row):
        """
        Check if a row is really complete
        """
        for y in range(Tetris.cols):
            if (row, y) not in self.bottom:
                return False
        return True

    def _drop_row(self, row):
        """
        Drop a row if it's complete. We do this by deleteting from the self.bottom
            - We have to reverse sort the drop keys to correctly drop a row
        """
        if not self._check_complete(row):
            return
        
        drop = set()
        for x, y in self.bottom.keys():
            if x == row:
                del self.bottom[x, y]
            if x  < row:
                drop.add((x, y))

        for x, y in sorted(drop, key = lambda t: -t[0]):
            if (x + 1, y) in self.bottom:
                continue
            
            color = self.bottom.pop((x, y))
            self.bottom[x + 1, y] = color
            
        self.score += 50
        self._refresh_score()

    def _get_rotated(self, piece, right = True):
        """
        Perform a rotation about the third coordinate
            - To rotate, we subtract fixed point, apply T(x,y) = (-y,x), finally add back fixed point
            - Squares (piece Q) cannot be rotated
            - Disregard rotation if it will violate bottom or left/right barriers
        """
        if piece.name == 'Q':
            return None
        
        tmp = []
        x0, y0 = piece.rects[2]
        for x, y in piece.rects:
            
            u, v = x - x0, y - y0
            u, v = -v, u
            
            if not right:
                v *= -1
                u *= -1
                
            u += x0
            v += y0
            if u < 0 or u > Tetris.rows - 1:
                return None
            if v < 0 or v > Tetris.cols - 1:
                return None
            if (u, v) in self.bottom:
                return None 
            
            tmp.append((u, v))
        return tmp

    def _get_translated(self, piece, dx=0, dy=0):
        """
        Perform a translation, T(x,y) = (x+dx,y+dy)
            - Disregard rotation if it will violate bottom or left/right barriers
        """
        tmp = []
        for x, y in self._falling.rects:
            u, v = x + dx, y + dy
            if u < 0 or u > Tetris.rows - 1:
                return None
            if v < 0 or v > Tetris.cols - 1:
                return None
            if (u, v) in self.bottom:
                if u < 4:
                    self.playing = False
                return None
            
            tmp.append((u, v))
        return tmp

    @ensure_playing
    def _draw_rectangle(self, x, y, color, tag, canvas, padx = 0, pady = 0):
        """
        Draw a game piece rectangle 
        """
        rect = canvas.create_rectangle(
            Tetris.row_zero + y * Tetris.box_size + pady,
            Tetris.col_zero + x * Tetris.box_size + padx,
            Tetris.row_zero + y * Tetris.box_size + Tetris.box_size + pady,
            Tetris.col_zero + x * Tetris.box_size + Tetris.box_size + padx,
            fill = color, outline = 'black'
        )

        self.canvas.pack()
        canvas.itemconfig(rect, tags = tag)

    @ensure_playing
    def _refresh_bottom(self):
        """
        Update bottom, each time falling piece hits bottom
        """
        self.canvas.delete('bottom')
        for x, y in self.bottom:
            color = self.bottom[x, y]
            self._draw_rectangle(x, y, color, 'bottom', self.canvas)

        self.root.after(200, self._refresh_falling)

    @ensure_playing
    def _refresh_falling(self):
        """
        Update the current falling piece
            - Should only be called every 'self.gravity' miliseconds
        """
        self.canvas.delete('falling')
        for x, y in self._falling.rects:
            self._draw_rectangle(x, y, self._falling.color, 'falling', self.canvas)
        
        self.root.after(200, self._refresh_falling)

    @ensure_playing
    def _refresh_score(self):
        """
        Update the game score, if we've completed a row
            - Should only be called when we have a complete row
        """
        horiz = Tetris.col_zero + Tetris.box_size * Tetris.cols + 20
        Label(self.canvas, text='Score: ' + str(self.score), fg = 'white', bg = 'black').place(y=Tetris.y_margin, x=horiz)
        if self.score > 0 and self.score % 200 == 0:
            self.gravity -= 100
            
    @ensure_playing
    def _refresh_next(self):        
        """
        Update the next piece in the right most part of the canvas
            - Should only be called when we've hit bottom
        """
        self.canvas.delete('next_piece')
        next_copy = copy.deepcopy(self._next_piece)
        horiz = Tetris.col_zero + Tetris.box_size * Tetris.cols + 20
        Label(self.canvas, text='Next Piece ', fg = 'white', bg = 'black').place(y=Tetris.y_margin + 20, x=horiz)

        for x, y in next_copy.rects:
            self._draw_rectangle(x, y, next_copy.color, 'next_piece', self.canvas, padx = 50, pady = horiz)

    def mainloop(self):
        self.root.mainloop()

if __name__ == '__main__':
    Tetris().mainloop()    # only one file...don't have to worry about tkinter executing on separate thread
