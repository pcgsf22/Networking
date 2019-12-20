UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3


class Snake:
    # pos = (x, y), where x is the col offset, and y is the row offset.
    def __init__(self, pos, rows, cols):
        self.rows, self.cols = rows, cols
        self.body = [pos]
        self.dx, self.dy = 0, 1

    def _update_dir(self, dir):
        """ Update the direction."""
        if dir == RIGHT:
            self.dx, self.dy = 1, 0
        if dir == LEFT:
            self.dx, self.dy = -1, 0
        if dir == UP:
            self.dx, self.dy = 0, -1
        if dir == DOWN:
            self.dx, self.dy = 0, 1

    def move(self, apple):
        """ Move one step method."""
        x, y = self.body[0]
        nx, ny = (x + self.dx) % self.cols, (y + self.dy) % self.rows
        if not (0 <= nx < self.cols) or not (0 <= ny < self.rows):
            return False
        if (nx, ny) in self.body:
            return False
        self.body.insert(0, (nx, ny))
        if not (nx, ny) == apple:
            self.body.pop()
        return True

    def head(self):
        """ Return the head of the snake."""
        return self.body[0]
