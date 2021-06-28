'''
Example of arrows game. The idea is that a cyan diamond follows the red arrows.
When a square has two arrows, which arrow is red gets swapped when the diamond
walks on it.
'''

import copy
import curses
import time

class ArrowBoard:
    '''
    Class to handle board manipulations and painting.
    '''

    # Orientations
    UP = 'U'
    LEFT = 'L'
    DOWN = 'D'
    RIGHT = 'R'

    # Landmarks
    GOAL = 'G'
    START = 'S'

    def __init__(self, rows, cols, landmarks, start, arrows,
            row_height = 4, col_width = 6):
        '''
        Creates a curses pad that can hold a grid with the specified number of
        rows and columns, where each row has row_height - 1 empty cells and
        each column has col_width - 1 empty cells. Also, saves board size
        information.
        '''
        self.rows = rows
        self.cols = cols

        self.landmarks = landmarks
        self.start = start
        self.total_arrows = arrows
        self.remaining_arrows = arrows

        self.landmarks[start[0]][start[1]].append(ArrowBoard.START)

        self.row_height = row_height
        self.col_width = col_width

        self.directions = [[list() for _ in range(cols)] for _ in range(rows)]

        self.board = curses.newpad(rows * row_height + 1, cols * col_width + 1)
        self.paint_grid()
        self.paint_landmarks()

    def paint_grid(self):
        '''
        Paints a grid onto the board.
        '''

        # One less than the height and width of board in number of console
        # characters
        board_height = self.rows * self.row_height
        board_width = self.cols * self.col_width

        # Paint rows * cols number of shapes that look like
        #     ┼─────
        #     │
        #     │
        #     │
        # Automatically pick the correct style of grid point for the top left
        # character (to treat the corner and edge cases)
        for row in range(0, board_height, self.row_height):
            for col in range(0, board_width, self.col_width):
                # Deal with the top left character
                self.board.addch(row, col,
                        (curses.ACS_ULCORNER if col == 0 else curses.ACS_TTEE)
                        if row == 0 else
                        (curses.ACS_LTEE if col == 0 else curses.ACS_PLUS))
                # Paint the vertical lines
                for i in range(1, self.row_height):
                    self.board.addch(row + i, col, curses.ACS_VLINE)
                # Paint the horizontal lines
                for j in range(1, self.col_width):
                    self.board.addch(row, col + j, curses.ACS_HLINE)

        # Paint the missing right hand edge of the grid by painting shapes like
        #     ┤
        #     │
        #     │
        #     │
        for row in range(0, board_height, self.row_height):
            # We need to print ┤ unless we are in the corner, in which case we
            # use ┐
            self.board.addch(row, board_width,
                    curses.ACS_URCORNER if row == 0 else curses.ACS_RTEE)
            # Paint the vertical lines
            for i in range(1, self.row_height):
                self.board.addch(row + i, board_width, curses.ACS_VLINE)

        # Do similar for the bottom edge of the board with shapes like
        # ┴─────
        for col in range(0, board_width, self.col_width):
            self.board.addch(board_height, col,
                    curses.ACS_LLCORNER if col == 0 else curses.ACS_BTEE)
            for j in range(1, self.col_width):
                self.board.addch(board_height, col + j, curses.ACS_HLINE)

        # Finish by painting the bottom right corner with ┘. Use insch here to
        # avoid throwing an exception
        self.board.insch(board_height, board_width, curses.ACS_LRCORNER)
        return self.board

    @staticmethod
    def opposite_orientation(orientation):
        '''
        Returns the opposite orientation of the input (or None on invalid
        input).
        '''

        if orientation == ArrowBoard.UP:
            return ArrowBoard.DOWN
        if orientation == ArrowBoard.LEFT:
            return ArrowBoard.RIGHT
        if orientation == ArrowBoard.DOWN:
            return ArrowBoard.UP
        if orientation == ArrowBoard.RIGHT:
            return ArrowBoard.LEFT
        return None

    def erase_arrow(self, position, orientation):
        '''
        Resets the arrow at position in the direction of orientation to be the
        gridline.
        '''

        row = position[0]
        col = position[1]

        if orientation == ArrowBoard.UP:
            self.board.addch(row * self.row_height,
                    col * self.col_width + self.col_width // 2,
                    curses.ACS_HLINE)
        elif orientation == ArrowBoard.LEFT:
            self.board.addch(row * self.row_height + self.row_height // 2,
                    col * self.col_width,
                    curses.ACS_VLINE)
        elif orientation == ArrowBoard.DOWN:
            self.board.addch(row * self.row_height + self.row_height,
                    col * self.col_width + self.col_width // 2,
                    curses.ACS_HLINE)
        elif orientation == ArrowBoard.RIGHT:
            self.board.addch(row * self.row_height + self.row_height // 2,
                    col * self.col_width + self.col_width,
                    curses.ACS_VLINE)

    def paint_arrows(self, position):
        '''
        Paints all arrows extending from position onto the board.
        '''

        row = position[0]
        col = position[1]

        for i, orientation in enumerate(self.directions[row][col]):
            # If the orientation is the first in the list, then use a bolded
            # red style
            attributes = curses.A_BOLD | curses.color_pair(1) if i == 0 else 0

            # Paint the correct arrow in the correct orientation. Note that
            # this only really works if row_height and col_width are even
            if orientation == ArrowBoard.UP:
                self.board.addch(row * self.row_height,
                        col * self.col_width + self.col_width // 2,
                        curses.ACS_UARROW, attributes)
            elif orientation == ArrowBoard.LEFT:
                self.board.addch(row * self.row_height + self.row_height // 2,
                        col * self.col_width,
                        curses.ACS_LARROW, attributes)
            elif orientation == ArrowBoard.DOWN:
                self.board.addch(row * self.row_height + self.row_height,
                        col * self.col_width + self.col_width // 2,
                        curses.ACS_DARROW, attributes)
            elif orientation == ArrowBoard.RIGHT:
                self.board.addch(row * self.row_height + self.row_height // 2,
                        col * self.col_width + self.col_width,
                        curses.ACS_RARROW, attributes)

    def paint_all_arrows(self):
        '''
        Paints all arrows onto the board, as determined by the directions
        array.
        '''

        for row in range(self.rows):
            for col in range(self.cols):
                self.paint_arrows([row, col])

    def paint_landmarks(self):
        '''
        Paints all landmarks onto the board.
        '''

        for row in range(self.rows):
            for col in range(self.cols):
                landmark = self.landmarks[row][col]
                if ArrowBoard.START in landmark:
                    # Paint a box
                    self.board.addch(
                            row * self.row_height + self.row_height // 2 - 1,
                            col * self.col_width + self.col_width // 2 - 1,
                            curses.ACS_ULCORNER, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2 - 1,
                            col * self.col_width + self.col_width // 2,
                            curses.ACS_HLINE, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2 - 1,
                            col * self.col_width + self.col_width // 2 + 1,
                            curses.ACS_URCORNER, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2,
                            col * self.col_width + self.col_width // 2 - 1,
                            curses.ACS_VLINE, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2,
                            col * self.col_width + self.col_width // 2 + 1,
                            curses.ACS_VLINE, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2 + 1,
                            col * self.col_width + self.col_width // 2 - 1,
                            curses.ACS_LLCORNER, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2 + 1,
                            col * self.col_width + self.col_width // 2,
                            curses.ACS_HLINE, curses.color_pair(4))
                    self.board.addch(
                            row * self.row_height + self.row_height // 2 + 1,
                            col * self.col_width + self.col_width // 2 + 1,
                            curses.ACS_LRCORNER, curses.color_pair(4))
                if ArrowBoard.GOAL in landmark:
                    # Paint a checkerboard
                    for i in range(1, 4):
                        for j in range(1, 6):
                            if (i + j) % 2 == 0:
                                self.board.addch(row * self.row_height + i,
                                        col * self.col_width + j,
                                        ' ', curses.A_REVERSE)

    def paint_cursor(self, position):
        '''
        Paints the cursor as an asterisk.
        '''

        self.board.addch(position[0] * self.row_height + self.row_height // 2,
                position[1] * self.col_width + self.col_width // 2,
                '*', curses.color_pair(3))

    def erase_cursor(self, position):
        '''
        Erase the cursor so that it doesn't leave a trail.
        '''

        self.board.addch(position[0] * self.row_height + self.row_height // 2,
                position[1] * self.col_width + self.col_width // 2, ' ')

    def paint_position(self, position):
        '''
        Paints the current position as a diamond.
        '''

        self.board.addch(position[0] * self.row_height + self.row_height // 2,
                position[1] * self.col_width + self.col_width // 2,
                curses.ACS_DIAMOND, curses.color_pair(2))

    def erase_position(self, position):
        '''
        Erase the cyan diamond so that it doesn't leave a trail.
        '''

        self.board.addch(position[0] * self.row_height + self.row_height // 2,
                position[1] * self.col_width + self.col_width // 2, ' ')

    @staticmethod
    def cell_at_orientation(position, orientation):
        '''
        Return the cell coordinates if, starting at position, we were to move
        in the direction of orientation.
        '''

        position = list(position)
        if orientation == ArrowBoard.UP:
            position[0] -= 1
        elif orientation == ArrowBoard.LEFT:
            position[1] -= 1
        elif orientation == ArrowBoard.DOWN:
            position[0] += 1
        elif orientation == ArrowBoard.RIGHT:
            position[1] += 1
        return position

    def position_is_valid(self, position):
        '''
        Return whether position is within our board.
        '''

        return 0 <= position[0] < self.rows and 0 <= position[1] < self.cols

    def advance(self, position, directions=None):
        '''
        Advances position as according to directions. That is, if we are at the
        location position, we look at the corresponding list in directions. If
        the list is empty, we have no instructions, so we are done. Otherwise,
        we follow whichever direction is listed first. When the list has 2
        elements, we swap them.

        This method returns whether position changed. Note that position and
        directions will be modified.
        '''

        if directions is None:
            directions = self.directions

        direction = directions[position[0]][position[1]]

        if not direction:
            return False

        next_position = ArrowBoard.cell_at_orientation(position, direction[0])

        # If we received an invalid direction, don't do anything
        if not self.position_is_valid(next_position):
            return False

        # Swap the orientations if there are two of them
        if len(direction) == 2:
            direction[0], direction[1] = direction[1], direction[0]

        position[0], position[1] = next_position[0], next_position[1]

        return True

    def refresh(self, stdscr):
        '''
        Tell curses to update the screen (dealing with the case that the window
        is too small to fit the whole image)
        '''

        stdscr.noutrefresh()
        maxy, maxx = stdscr.getmaxyx()
        self.board.refresh(0, 0, 2, 0, maxy - 1, maxx - 1)

    def run(self, stdscr, position, delay=0.1):
        '''
        Repeatedly advance the board state until the position reaches the goal
        or until no move is possible. Also exits if q is pressed.
        '''

        position = list(position)
        original_directions = copy.deepcopy(self.directions)

        moves = 0

        delay = max(0, delay)

        # Reset the move counter
        stdscr.move(0, 0)
        stdscr.clrtoeol()

        start_time = time.time_ns()
        stdscr.timeout(0)

        while True:
            # Paint the current position
            self.paint_position(position)

            # Display the number of moves
            stdscr.addstr(0, 0, f'moves: {moves}')

            # Update the screen
            self.refresh(stdscr)

            # Wait for the user to press a key, or for delay seconds to pass
            done = False
            while (time.time_ns() - start_time) * 1e-9 \
                    < (moves + 1) * delay:
                char = stdscr.getch()

                # If q is pressed, we should exit
                if char == ord('q'):
                    done = True

                    # Reset the move counter so it is not misleading
                    moves = -1
                    break

                # If p is pressed, pause until another key is pressed
                if char == ord('p'):
                    pause_time = time.time_ns()
                    stdscr.timeout(-1)
                    stdscr.getch()
                    stdscr.timeout(0)
                    start_time += time.time_ns() - pause_time

                # If the screen is resized, we need to refresh
                if char == curses.KEY_RESIZE:
                    self.refresh(stdscr)
            if done:
                break

            # If the diamond reached the goal, exit
            if ArrowBoard.GOAL in self.landmarks[position[0]][position[1]]:
                break

            previous_position = list(position)
            self.erase_position(position)

            # If no directions are available at our position, exit
            if not self.advance(position):
                moves = -1
                break

            self.paint_arrows(previous_position)
            self.paint_position(position)

            moves += 1

        # Clear the position
        if delay > 0:
            self.erase_position(position)

        # Update the move counter in case of "bad" exit
        stdscr.move(0, 0)
        stdscr.clrtoeol()
        stdscr.addstr(0, 0, f'moves: {moves}')

        self.refresh(stdscr)

        stdscr.timeout(-1)

        # Replace the original directions
        self.directions = original_directions
        if delay > 0:
            self.paint_all_arrows()

        return moves

    def get_moves(self):
        '''
        Returns (without any animation) the number of moves the current
        directions would yield. Returns -1 if the diamond would never reach the
        goal.
        '''

        # TODO: Use Floyd's cycle detection algorithm here

    def add_orientation(self, position, orientation):
        '''
        Adds an arrow at position in the direction of orientation. If an arrow
        already exists there pointing in the opposite direction, removes that
        arrow.

        This assumes the arrow we're trying to add is valid to add.
        '''

        # First handle if an arrow already exists
        nonlocal_position \
                = ArrowBoard.cell_at_orientation(position, orientation)

        # If the nonlocal position doesn't actually exist, don't do anything
        # since we can't go in that direction anyways
        if not self.position_is_valid(nonlocal_position):
            return

        nonlocal_orientation = ArrowBoard.opposite_orientation(orientation)

        nonlocal_direction \
                = self.directions[nonlocal_position[0]][nonlocal_position[1]]
        index = nonlocal_direction.index(nonlocal_orientation) \
                if nonlocal_orientation in nonlocal_direction else None
        if index is not None:
            del nonlocal_direction[index]
            self.remaining_arrows += 1
            self.erase_arrow(nonlocal_position, nonlocal_orientation)

        # Now we can safely add the arrow
        if self.remaining_arrows > 0:
            direction = self.directions[position[0]][position[1]]
            direction.insert(0, orientation)
            self.remaining_arrows -= 1
            self.paint_arrows(position)

    def process_orientation(self, cursor, orientation):
        '''
        Adds/removes/changes an arrow to/from/on the board.
        '''

        row = cursor[0]
        column = cursor[1]

        if ArrowBoard.GOAL in self.landmarks[row][column]:
            return

        direction = self.directions[row][column]
        if not direction:
            self.add_orientation(cursor, orientation)
        elif len(direction) == 1:
            if direction[0] == orientation:
                self.erase_arrow(cursor, orientation)
                del direction[0]
                self.remaining_arrows += 1
            else:
                self.add_orientation(cursor, orientation)
        else:
            if direction[0] == orientation:
                self.erase_arrow(cursor, orientation)
                del direction[0]
                self.remaining_arrows += 1
                self.paint_arrows(cursor)
            elif direction[1] == orientation:
                direction[0], direction[1] = direction[1], direction[0]
                self.paint_arrows(cursor)
            else:
                self.erase_arrow(cursor, direction[1])
                del direction[1]
                self.remaining_arrows += 1
                self.add_orientation(cursor, orientation)

    def edit(self, stdscr):
        '''
        Enters edit mode for the board.
        '''

        cursor = [0, 0]

        # Paint the cursor
        self.paint_cursor(cursor)

        # Paint the number of arrows remaining
        stdscr.addstr(1, 0, f'arrows: {self.remaining_arrows} '
                f'({self.total_arrows - self.remaining_arrows})')

        while True:
            # Update the screen
            self.refresh(stdscr)

            # Wait for input
            char = stdscr.getch()

            # Update the cursor position with wasd
            self.erase_cursor(cursor)
            if char == ord('w') and cursor[0] > 0:
                cursor[0] -= 1
            elif char == ord('a') and cursor[1] > 0:
                cursor[1] -= 1
            elif char == ord('s') and cursor[0] < self.rows - 1:
                cursor[0] += 1
            elif char == ord('d') and cursor[1] < self.cols - 1:
                cursor[1] += 1
            self.paint_cursor(cursor)

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
                self.process_orientation(cursor, orientation)

                # Repaint the number of arrows remaining
                stdscr.move(1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(1, 0, f'arrows: {self.remaining_arrows} '
                        f'({self.total_arrows - self.remaining_arrows})')

                # Update the number of moves
                # self.run(stdscr, self.start, 0)

            # Run the animation when g is pressed
            if char == ord('g'):
                # Hide the cursor while running
                self.erase_cursor(cursor)
                self.refresh(stdscr)

                self.run(stdscr, self.start)

                # Then bring it back once we're finished
                self.paint_cursor(cursor)

            # Reset the board when r is pressed
            if char == ord('r'):
                self.directions \
                        = [[list() for _ in range(self.cols)]
                                for _ in range(self.rows)]
                self.remaining_arrows = self.total_arrows
                self.paint_grid()

                stdscr.move(1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(1, 0, f'arrows: {self.remaining_arrows} '
                        f'({self.total_arrows - self.remaining_arrows})')

            # Exit when q is pressed
            if char == ord('q'):
                break

def main(stdscr):
    '''
    The main function.
    '''

    rows = 3
    cols = 5
    landmarks = [[list() for _ in range(cols)] for _ in range(rows)]
    landmarks[2][4].append(ArrowBoard.GOAL)
    start = [0, 0]
    arrows = 999

    rows = len(landmarks)
    cols = len(landmarks[0])

    # Don't display the terminal cursor
    curses.curs_set(0)

    # Setup color support if available
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)     # Arrows
    curses.init_pair(2, curses.COLOR_CYAN, -1)    # Diamond
    curses.init_pair(3, curses.COLOR_MAGENTA, -1) # Cursor
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # Start

    arrow_board = ArrowBoard(rows, cols, landmarks, start, arrows)
    arrow_board.edit(stdscr)

curses.wrapper(main)
