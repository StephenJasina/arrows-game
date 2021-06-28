"""
Basic command line implementation of an arrows game.

A cyan diamond tries to get from the start (a green rectangle) to the
goal (a checkerboard). To do this, it follows a series of red arrows,
one at a time. The objective is to make the diamond's path as long as
possible (but still finite).

The player is allowed to place the arrows, at most one per edge. To
spice it up, cells are allowed to have *two* outgoing arrows, one of
which will be initially red. Each time the diamond exits a cell with two
arrows, which arrow is red gets toggled (think of it like a train
junction switching).
"""

import copy
import curses


class ArrowBoard:
    """Class to handle board manipulations and painting."""

    # Orientations
    UP = 'U'
    LEFT = 'L'
    DOWN = 'D'
    RIGHT = 'R'

    # Landmarks
    GOAL = 'G'
    START = 'S'
    BOULDER = 'B'

    def __init__(self, landmarks, arrows, row_height=4, col_width=6):
        """
        Initialize the game board.

        Creates a curses pad that can hold a grid with the specified
        number of rows and columns, where each row has row_height - 1
        empty cells and each column has col_width - 1 empty cells. Also,
        saves board size information.
        """
        # Size of our board
        self._rows = len(landmarks)
        self._cols = len(landmarks[0])

        # Start, goal, and obstacles
        self._landmarks = landmarks

        self._start = None
        for row in range(self._rows):
            for col in range(self._cols):
                if ArrowBoard.START in landmarks[row][col]:
                    self._start = [row, col]
                    break
            if self._start is not None:
                break

        self._total_arrows = arrows
        self._remaining_arrows = arrows

        self._landmarks[self._start[0]][self._start[1]].append(
            ArrowBoard.START)

        self._row_height = row_height
        self._col_width = col_width

        # Arrows
        self._directions = [[list() for _ in range(self._cols)]
                            for _ in range(self._rows)]

        self._board = curses.newpad(self._rows * row_height + 1,
                                    self._cols * col_width + 1)
        self._paint_grid()
        self._paint_landmarks()

    @staticmethod
    def _opposite_orientation(orientation):
        """Return the opposite orientation of the input."""
        if orientation == ArrowBoard.UP:
            return ArrowBoard.DOWN
        if orientation == ArrowBoard.LEFT:
            return ArrowBoard.RIGHT
        if orientation == ArrowBoard.DOWN:
            return ArrowBoard.UP
        if orientation == ArrowBoard.RIGHT:
            return ArrowBoard.LEFT
        return None

    @staticmethod
    def _cell_at_orientation(position, orientation):
        """
        Return the cell coordinates one space away.

        The coordinates are calculated starting at position and moving
        one space in the direction of orientation.
        """
        position = copy.deepcopy(position)
        if orientation == ArrowBoard.UP:
            position[0] -= 1
        elif orientation == ArrowBoard.LEFT:
            position[1] -= 1
        elif orientation == ArrowBoard.DOWN:
            position[0] += 1
        elif orientation == ArrowBoard.RIGHT:
            position[1] += 1
        return position

    def _position_is_valid(self, position):
        """Return whether position is within our board."""
        return 0 <= position[0] < self._rows and 0 <= position[1] < self._cols

    def _paint_grid(self):
        """Paint the grid onto the board."""
        # One less than the height and width of board in number of
        # console characters
        board_height = self._rows * self._row_height
        board_width = self._cols * self._col_width

        # Paint rows * cols number of shapes that look like
        #     ┼─────
        #     │
        #     │
        #     │
        # Automatically pick the correct style of grid point for the top
        # left character (to treat the corner and edge cases)
        for row in range(0, board_height, self._row_height):
            for col in range(0, board_width, self._col_width):
                # Deal with the top left character
                self._board.addch(
                    row, col,
                    (curses.ACS_ULCORNER if col == 0 else curses.ACS_TTEE)
                    if row == 0 else
                    (curses.ACS_LTEE if col == 0 else curses.ACS_PLUS))
                # Paint the vertical lines
                for i in range(1, self._row_height):
                    self._board.addch(row + i, col, curses.ACS_VLINE)
                # Paint the horizontal lines
                for j in range(1, self._col_width):
                    self._board.addch(row, col + j, curses.ACS_HLINE)

        # Paint the missing right hand edge of the grid by painting
        # shapes like
        #     ┤
        #     │
        #     │
        #     │
        for row in range(0, board_height, self._row_height):
            # We need to print ┤ unless we are in the corner, in which
            # case we use ┐
            self._board.addch(
                row, board_width,
                curses.ACS_URCORNER if row == 0 else curses.ACS_RTEE)
            # Paint the vertical lines
            for i in range(1, self._row_height):
                self._board.addch(row + i, board_width, curses.ACS_VLINE)

        # Do similar for the bottom edge of the board with shapes like
        # ┴─────
        for col in range(0, board_width, self._col_width):
            self._board.addch(
                board_height, col,
                curses.ACS_LLCORNER if col == 0 else curses.ACS_BTEE)
            for j in range(1, self._col_width):
                self._board.addch(board_height, col + j, curses.ACS_HLINE)

        # Finish by painting the bottom right corner with ┘. Use insch
        # here to avoid throwing an exception
        self._board.insch(board_height, board_width, curses.ACS_LRCORNER)
        return self._board

    def _erase_arrow(self, position, orientation):
        """Replace an arrow with a gridline."""
        row = position[0]
        col = position[1]

        if orientation == ArrowBoard.UP:
            self._board.addch(row * self._row_height,
                              col * self._col_width + self._col_width // 2,
                              curses.ACS_HLINE)
        elif orientation == ArrowBoard.LEFT:
            self._board.addch(row * self._row_height + self._row_height // 2,
                              col * self._col_width,
                              curses.ACS_VLINE)
        elif orientation == ArrowBoard.DOWN:
            self._board.addch(row * self._row_height + self._row_height,
                              col * self._col_width + self._col_width // 2,
                              curses.ACS_HLINE)
        elif orientation == ArrowBoard.RIGHT:
            self._board.addch(row * self._row_height + self._row_height // 2,
                              col * self._col_width + self._col_width,
                              curses.ACS_VLINE)

    def _paint_arrows(self, position):
        """Paint all necessary arrows from a position onto the board."""
        row = position[0]
        col = position[1]

        for i, orientation in enumerate(self._directions[row][col]):
            # If the orientation is the first in the list, then use a
            # bolded red style
            attributes = curses.A_BOLD | curses.color_pair(1) if i == 0 else 0

            # Paint the correct arrow in the correct orientation. Note
            # that this only really works if row_height and col_width
            # are even
            if orientation == ArrowBoard.UP:
                self._board.addch(row * self._row_height,
                                  col * self._col_width + self._col_width // 2,
                                  curses.ACS_UARROW, attributes)
            elif orientation == ArrowBoard.LEFT:
                self._board.addch(
                    row * self._row_height + self._row_height // 2,
                    col * self._col_width,
                    curses.ACS_LARROW, attributes)
            elif orientation == ArrowBoard.DOWN:
                self._board.addch(row * self._row_height + self._row_height,
                                  col * self._col_width + self._col_width // 2,
                                  curses.ACS_DARROW, attributes)
            elif orientation == ArrowBoard.RIGHT:
                self._board.addch(
                    row * self._row_height + self._row_height // 2,
                    col * self._col_width + self._col_width,
                    curses.ACS_RARROW, attributes)

    def _paint_all_arrows(self):
        """Paints all necessary arrows onto the board."""
        for row in range(self._rows):
            for col in range(self._cols):
                self._paint_arrows([row, col])

    def _paint_landmarks(self):
        """Paint all landmarks onto the board."""
        for row in range(self._rows):
            for col in range(self._cols):
                landmark = self._landmarks[row][col]
                if ArrowBoard.START in landmark:
                    # Paint a box
                    self._board.addch(
                        row * self._row_height + self._row_height // 2 - 1,
                        col * self._col_width + self._col_width // 2 - 1,
                        curses.ACS_ULCORNER, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2 - 1,
                        col * self._col_width + self._col_width // 2,
                        curses.ACS_HLINE, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2 - 1,
                        col * self._col_width + self._col_width // 2 + 1,
                        curses.ACS_URCORNER, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2,
                        col * self._col_width + self._col_width // 2 - 1,
                        curses.ACS_VLINE, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2,
                        col * self._col_width + self._col_width // 2 + 1,
                        curses.ACS_VLINE, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2 + 1,
                        col * self._col_width + self._col_width // 2 - 1,
                        curses.ACS_LLCORNER, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2 + 1,
                        col * self._col_width + self._col_width // 2,
                        curses.ACS_HLINE, curses.color_pair(4))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2 + 1,
                        col * self._col_width + self._col_width // 2 + 1,
                        curses.ACS_LRCORNER, curses.color_pair(4))
                if ArrowBoard.GOAL in landmark:
                    # Paint a checkerboard
                    for i in range(1, self._row_height):
                        for j in range(1, self._col_width):
                            if (i + j) % 2 == 0:
                                self._board.addch(row * self._row_height + i,
                                                  col * self._col_width + j,
                                                  ' ', curses.A_REVERSE)
                if ArrowBoard.BOULDER in landmark:
                    # Block off all exits/entrances
                    self._board.addch(
                        row * self._row_height,
                        col * self._col_width + self._col_width // 2,
                        curses.ACS_BLOCK, curses.color_pair(1))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2,
                        col * self._col_width,
                        curses.ACS_BLOCK, curses.color_pair(1))
                    self._board.addch(
                        row * self._row_height + self._row_height,
                        col * self._col_width + self._col_width // 2,
                        curses.ACS_BLOCK, curses.color_pair(1))
                    self._board.addch(
                        row * self._row_height + self._row_height // 2,
                        col * self._col_width + self._col_width,
                        curses.ACS_BLOCK, curses.color_pair(1))

    def _paint_cursor(self, position):
        """Paint the cursor as an asterisk."""
        self._board.addch(
            position[0] * self._row_height + self._row_height // 2,
            position[1] * self._col_width + self._col_width // 2,
            '*', curses.color_pair(3))

    def _erase_cursor(self, position):
        """Erase the cursor so that it doesn't leave a trail."""
        self._board.addch(
            position[0] * self._row_height + self._row_height // 2,
            position[1] * self._col_width + self._col_width // 2, ' ')

    def _paint_position(self, position):
        """Paint the current position as a diamond."""
        self._board.addch(
            position[0] * self._row_height + self._row_height // 2,
            position[1] * self._col_width + self._col_width // 2,
            curses.ACS_DIAMOND, curses.color_pair(2))

    def _erase_position(self, position):
        """Erase the cyan diamond so that it doesn't leave a trail."""
        self._board.addch(
            position[0] * self._row_height + self._row_height // 2,
            position[1] * self._col_width + self._col_width // 2, ' ')

    def _advance(self, position, directions=None):
        """
        Advance position as according to directions.

        That is, if we are at the location position, we look at the
        corresponding list in directions. If the list is empty, we have
        no instructions, so we are done. Otherwise, we follow whichever
        direction is listed first. When the list has 2 elements, we swap
        them.

        This method returns whether position changed. Note that position
        and directions will be modified.
        """
        if directions is None:
            directions = self._directions

        direction = directions[position[0]][position[1]]

        if not direction:
            return False

        next_position = ArrowBoard._cell_at_orientation(position, direction[0])

        # If we received an invalid direction, don't do anything
        if not self._position_is_valid(next_position):
            return False

        # Swap the orientations if there are two of them
        if len(direction) == 2:
            direction[0], direction[1] = direction[1], direction[0]

        position[0], position[1] = next_position[0], next_position[1]

        return True

    def refresh(self, stdscr):
        """
        Tell curses to update the screen.

        This deals with the case that the window is too small to fit the
        whole image.
        """
        stdscr.noutrefresh()
        maxy, maxx = stdscr.getmaxyx()
        self._board.refresh(0, 0, 2, 0, maxy - 1, maxx - 1)

    def _can_add_orientation(self, position, orientation):
        """Return whether a move is legal."""
        if not self._position_is_valid(position):
            return False

        landmark = self._landmarks[position[0]][position[1]]

        if ArrowBoard.GOAL in landmark or ArrowBoard.BOULDER in landmark:
            return False

        nonlocal_position = ArrowBoard._cell_at_orientation(
            position, orientation)

        if not self._position_is_valid(nonlocal_position):
            return False

        nonlocal_landmark = (
            self._landmarks[nonlocal_position[0]][nonlocal_position[1]])

        if ArrowBoard.BOULDER in nonlocal_landmark:
            return False

        return True

    def _add_orientation(self, position, orientation):
        """
        Add an arrow at position in the direction of orientation.

        If an arrow already exists there pointing in the opposite
        direction, that arrow is removed. This function assumes the
        arrow we're trying to add is valid to add.
        """
        # First handle if an arrow already exists
        nonlocal_position = ArrowBoard._cell_at_orientation(
            position, orientation)

        # If the nonlocal position doesn't actually exist, don't do
        # anything since we can't go in that direction anyways
        if not self._position_is_valid(nonlocal_position):
            return

        nonlocal_orientation = ArrowBoard._opposite_orientation(orientation)

        nonlocal_direction = (
            self._directions[nonlocal_position[0]][nonlocal_position[1]])
        index = (nonlocal_direction.index(nonlocal_orientation)
                 if nonlocal_orientation in nonlocal_direction else None)
        if index is not None:
            del nonlocal_direction[index]
            self._remaining_arrows += 1
            # This next line shouldn't need to be here unless we get in
            # some weird state in which _remaining_arrows is negative
            self._erase_arrow(nonlocal_position, nonlocal_orientation)
            self._paint_arrows(nonlocal_position)

        # Now we can safely add the arrow
        if self._remaining_arrows > 0:
            direction = self._directions[position[0]][position[1]]
            direction.insert(0, orientation)
            self._remaining_arrows -= 1
            self._paint_arrows(position)

    def _process_orientation(self, position, orientation):
        """Add/remove/change an arrow to/from/on the board."""
        row = position[0]
        column = position[1]

        addable = self._can_add_orientation(position, orientation)

        direction = self._directions[row][column]
        if not direction:
            if addable:
                self._add_orientation(position, orientation)
        elif len(direction) == 1:
            if direction[0] == orientation:
                self._erase_arrow(position, orientation)
                del direction[0]
                self._remaining_arrows += 1
            else:
                if addable:
                    self._add_orientation(position, orientation)
        else:
            if direction[0] == orientation:
                self._erase_arrow(position, orientation)
                del direction[0]
                self._remaining_arrows += 1
                self._paint_arrows(position)
            elif direction[1] == orientation:
                direction[0], direction[1] = direction[1], direction[0]
                self._paint_arrows(position)
            else:
                if addable:
                    self._erase_arrow(position, direction[1])
                    del direction[1]
                    self._remaining_arrows += 1
                    self._add_orientation(position, orientation)

    def _get_moves(self):
        """
        Return the number of moves the current directions would yield.

        Returns -1 if the diamond would never reach the goal. This
        function does no animation routines.
        """
        tortoise_directions = copy.deepcopy(self._directions)
        tortoise_position = copy.deepcopy(self._start)
        hare_directions = copy.deepcopy(self._directions)
        hare_position = copy.deepcopy(self._start)

        moves = 0

        while True:
            if ArrowBoard.GOAL in (
                    self._landmarks[hare_position[0]][hare_position[1]]):
                return moves

            if not self._advance(hare_position, hare_directions):
                return -1
            moves += 1

            if ArrowBoard.GOAL in (
                    self._landmarks[hare_position[0]][hare_position[1]]):
                return moves

            if not self._advance(hare_position, hare_directions):
                return -1
            moves += 1

            self._advance(tortoise_position, tortoise_directions)

            if (tortoise_position == hare_position
                    and tortoise_directions == hare_directions):
                return -1

    @staticmethod
    def _paint_moves(stdscr, moves):
        """
        Write the number of moves.

        In case moves is negative, write "infinity" instead.
        """
        stdscr.move(0, 0)
        stdscr.clrtoeol()
        stdscr.addstr(0, 0, f'moves: {moves if moves >= 0 else "infinity"}')

    def _paint_arrow_count(self, stdscr):
        """Write the number of remaining and used arrows."""
        stdscr.move(1, 0)
        stdscr.clrtoeol()
        stdscr.addstr(1, 0, f'arrows: {self._remaining_arrows} '
                      f'({self._total_arrows - self._remaining_arrows})')

    def run(self, stdscr, delay=200):
        """
        Advance the board state until the position reaches the goal.

        Terminates additionally if no move is possible, or if the `q`
        key is pressed.
        """
        position = copy.deepcopy(self._start)
        original_directions = copy.deepcopy(self._directions)

        moves = 0

        delay = max(0, delay)

        stdscr.timeout(delay)

        while True:
            # Paint the current position
            self._paint_position(position)

            # Display the number of moves
            self._paint_moves(stdscr, moves)

            # Update the screen
            self.refresh(stdscr)

            # Wait for the user to press a key, or for delay seconds to
            # pass
            char = stdscr.getch()

            # If q is pressed, we should exit
            if char == ord('q'):
                break

            # If p is pressed, pause until another key is pressed
            if char == ord('p'):
                stdscr.timeout(-1)
                stdscr.getch()
                stdscr.timeout(delay)

            # If the screen is resized, we need to refresh
            if char == curses.KEY_RESIZE:
                self.refresh(stdscr)

            # If the diamond reached the goal, exit
            if ArrowBoard.GOAL in self._landmarks[position[0]][position[1]]:
                break

            previous_position = copy.deepcopy(position)
            self._erase_position(position)

            # If no directions are available at our position, exit
            if not self._advance(position):
                moves = -1
                break

            self._paint_arrows(previous_position)
            self._paint_position(position)

            moves += 1

        # Clear the position
        if delay > 0:
            self._erase_position(position)

        self.refresh(stdscr)

        stdscr.timeout(-1)

        # Replace the original directions
        self._directions = original_directions
        if delay > 0:
            self._paint_all_arrows()

        # Update the move counter in case of "bad" exit
        self._paint_moves(stdscr, self._get_moves())

        return moves

    def edit(self, stdscr):
        """Enter edit mode."""
        cursor = [0, 0]

        # Paint the cursor
        self._paint_cursor(cursor)

        # Paint the number of arrows remaining
        self._paint_arrow_count(stdscr)

        while True:
            # Update the screen
            self.refresh(stdscr)

            # Wait for input
            char = stdscr.getch()

            # Update the cursor position with wasd
            self._erase_cursor(cursor)
            if char == ord('w') and cursor[0] > 0:
                cursor[0] -= 1
            elif char == ord('a') and cursor[1] > 0:
                cursor[1] -= 1
            elif char == ord('s') and cursor[0] < self._rows - 1:
                cursor[0] += 1
            elif char == ord('d') and cursor[1] < self._cols - 1:
                cursor[1] += 1
            self._paint_cursor(cursor)

            # Update the directions with arrows or okl;
            orientation = None
            if char == curses.KEY_UP or char == ord('o'):
                orientation = ArrowBoard.UP
            elif char == curses.KEY_LEFT or char == ord('k'):
                orientation = ArrowBoard.LEFT
            elif char == curses.KEY_DOWN or char == ord('l'):
                orientation = ArrowBoard.DOWN
            elif char == curses.KEY_RIGHT or char == ord(';'):
                orientation = ArrowBoard.RIGHT
            if orientation is not None:
                self._process_orientation(cursor, orientation)

                # Repaint the number of arrows remaining
                self._paint_arrow_count(stdscr)

                # Update the number of moves
                self._paint_moves(stdscr, self._get_moves())

            # Run the animation when g is pressed
            if char == ord('g'):
                # Hide the cursor while running
                self._erase_cursor(cursor)
                self.refresh(stdscr)

                self.run(stdscr)

                # Then bring it back once we're finished
                self._paint_cursor(cursor)

            # Reset the board when r is pressed
            if char == ord('r'):
                self._directions = [[list() for _ in range(self._cols)]
                                    for _ in range(self._rows)]
                self._remaining_arrows = self._total_arrows
                self._paint_grid()
                self._paint_landmarks()

                self._paint_arrow_count(stdscr)

            # Exit when q is pressed
            if char == ord('q'):
                self._erase_cursor(cursor)
                break


def main(stdscr):
    """Run a simple example board."""
    rows = 3
    cols = 5
    landmarks = [[list() for _ in range(cols)] for _ in range(rows)]
    landmarks[0][0].append(ArrowBoard.START)
    landmarks[1][2].append(ArrowBoard.BOULDER)
    landmarks[2][4].append(ArrowBoard.GOAL)
    arrows = 999

    # Don't display the terminal cursor
    curses.curs_set(0)

    # Setup color support if available
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)      # Arrows
    curses.init_pair(2, curses.COLOR_CYAN, -1)     # Diamond
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)  # Cursor
    curses.init_pair(4, curses.COLOR_GREEN, -1)    # Start

    arrow_board = ArrowBoard(landmarks, arrows)
    arrow_board.edit(stdscr)


if __name__ == '__main__':
    curses.wrapper(main)
