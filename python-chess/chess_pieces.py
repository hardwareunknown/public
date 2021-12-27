""" Defines piece classes used in chess, including data and legal moves,
    and creates objects from those classes to be used in chess.py
    """
import chess_config as config
# TODO import abc module and make Piece an abstract class to get rid of
#   warnings?
# TODO EXP (EXPERIMENTAL):
#   OpenSpace self.color = "blank"


class Piece:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if self.color == "white":
            self.color_id = "W"
        elif self.color == "black":
            self.color_id = "B"
        else:
            print('Please enter "white" or "black" for color.')
        self.display = self.color_id + self.unit + str(self.num_id)
        self.current_col_index = config.col.index(self.current_space[0])
        self.current_row_index = config.row.index(self.current_space[1])

    # TODO uncomment this after testing (only commented out so it wouldn't
    #  print anything as I tested piece movement, and thus "Taking"/__del__
    #  when a Piece object replaced another)... should likely code these
    #  messages into the game flow itself rather than relying on __del__,
    #  as references to the piece objects may be around for a time due to a
    #  delayed garbage collection, thus not triggering the taken messages at
    #  the appropriate time.... However, moved WN2 to F3, BP5 to E5,
    #  then WN2 onto E5 with the code enabled and no mention of the taking
    #  occurred... for some reason it does not appear to be deleting the
    #  reference to the piece... likely the issue described above

    # def __del__(self):
    #     if self.color == "white":
    #         print(f"Black takes white {self.piece_type} {self.num_id}.")
    #     else:
    #         print(f"White takes black {self.piece_type} {self.num_id}.")

    def __str__(self):
        return self.display
        # if self.piece_type == "king":
        #     return f"{self.color.capitalize()} {self.piece_type}, " \
        #            f"current position: {self.current_space}"
        # else:
        #     return f"{self.color.capitalize()} {self.piece_type} " \
        #            f"{self.num_id}, current " \
        #            f"position: {self.current_space}"

    def __repr__(self):
        return self.display + "_Obj"


class Pawn(Piece):
    def __init__(self, color, num_id, start_space, current_space):
        # Sign of row_vector assures that each side's pawns can only
        # move forward from the perspective of the associated player.
        if color == "white":
            self.start_row_index = 6
            self.row_vector = -1
        else:
            self.start_row_index = 1
            self.row_vector = 1
        data = {
            "color": color,
            "num_id": num_id,
            "start_space": start_space,
            "current_space": current_space,
            "piece_type": "pawn",
            "unit": "P",
            "has_moved": False,
            "last_turn_moved": None,
            "two_space_move": False,
            "promoted": False
        }
        super().__init__(**data)

    def legal_move(self):
        possible_moves = []
        # Add diagonal capture movements. These will be blocked off in
        # move_blocked() if there is no enemy piece there, while
        # allowing the move if there is no piece there currently BUT en
        # passant is available.
        for col_vector in (-1, 1):
            if 0 <= self.current_col_index + col_vector <= 7 \
                    and 0 <= self.current_row_index + self.row_vector <= 7:
                possible_moves.append(
                    config.col[self.current_col_index + col_vector] +
                    config.row[self.current_row_index + self.row_vector]
                )
            # TODO remove this commented if, provided the move_blocked
            #  function prevents pawns from diagonal movement if a piece is not
            #  there
            # Pawn diagonal capture: col[...] + row[...] returns space
            # ID (ex. B2) of the space diagonally forward left or
            # forward right of the pawn, from the respective player's
            # perspective. board_pos[...] returns the index of that
            # space within the current_pieces_L list.
            # current_pieces_L[...] then returns whatever is currently
            # at that space. If it is not an open_space (ie. there is a
            # piece there) and the player's color_id is not present
            # in the piece ID (ie. it is an enemy piece), then the
            # diagonal move can be performed. The for loop above allows
            # us to check this for both of the forward diagonal spaces.
            # We do not check the typical 0 <= col[...] + row[...] <= 7
            # relationship because this particular if statement is
            # confined within current_pieces_L, all elements of which we
            # know exist.
            # TODO make sure that this live updates with the values of
            #  pieces on board.values... don't want it to just pull from the
            #  bare config file and have it be a static dictionary.
            #  Potentially use a median file like main.py to pull data from
            #  into both chess.py and chess.pieces... rather than trying to
            #  circular communicate between the two modules.
            #
            # if board[
            #     config.col[self.current_col_index + col_vector]
            #      + config.row[self.current_row_index + self.row_vector]
            #     ] != OpenSpace \
            #         and self.color_id not in current_pieces_L[board_pos[
            #     config.col[self.current_col_index + col_vector]
            #      + config.row[self.current_row_index + self.row_vector]
            #     ]]:
            #     possible_moves.append(
            #         (config.col[self.current_col_index + col_vector]
            #          + config.row[self.current_row_index + self.row_vector]
            #     )
        # Single space move forward if pawn has already moved
        if self.has_moved \
                and 0 <= self.current_row_index + self.row_vector <= 7:
            possible_moves.append(
                config.col[self.current_col_index]
                + config.row[self.current_row_index + self.row_vector]
            )
        # Two space move forward allowed if pawn has not yet moved
        else:
            for vector in (self.row_vector, 2 * self.row_vector):
                possible_moves.append(
                    config.col[self.current_col_index]
                    + config.row[self.current_row_index + vector]
                )
        return possible_moves


class Rook(Piece):
    def __init__(self, color, num_id, start_space, current_space):
        data = {
            "color": color,
            "num_id": num_id,
            "start_space": start_space,
            "current_space": current_space,
            "piece_type": "rook",
            "unit": "R",
            "has_moved": False,
            "move_vector": list(range(-7, 8))
        }
        super().__init__(**data)

    # TODO: ADD CASTLING!!!!
    # Rooks can move max spaces up, down, left, and right. This is
    # represented by adding -7 through 7 to each col index without
    # altering the row index, and then to each row index
    # without altering the col index.
    #
    # We run through each of these values in the for loop to
    # determine the resulting legal spaces. Some will be off the
    # board if the piece is close enough to an edge, however, so an
    # if statement then checks if they are legitimate spaces/on the
    # board, ie. not outside the row and col tuples. Finally, we add
    # a check to see if the row and column vectors are both 0, ie.
    # the piece hasn't moved.
    def legal_move(self):
        possible_moves = []
        for col_vector in self.move_vector:
            if 0 <= self.current_col_index + col_vector <= 7 and col_vector \
                    != 0:
                possible_moves.append(
                    config.col[self.current_col_index + col_vector]
                    + config.row[self.current_row_index]
                )
        for row_vector in self.move_vector:
            if 0 <= self.current_row_index + row_vector <= 7 and row_vector \
                    != 0:
                possible_moves.append(
                    config.col[self.current_col_index]
                    + config.row[self.current_row_index + row_vector]
                )
        return possible_moves


class Knight(Piece):
    """ Unit N is used to avoid confusion with the K in king."""

    def __init__(self, color, num_id, start_space, current_space):
        data = {
            "color": color,
            "num_id": num_id,
            "start_space": start_space,
            "current_space": current_space,
            "piece_type": "knight",
            "unit": "N",
            "move_vector": list(range(-2, 3))
        }
        super().__init__(**data)

    def legal_move(self):
        possible_moves = []
        for col_vector in self.move_vector:
            for row_vector in self.move_vector:
                if 0 <= self.current_col_index + col_vector <= 7 \
                        and 0 <= self.current_row_index + row_vector <= 7 \
                        and (col_vector != 0 and row_vector != 0) \
                        and abs(col_vector) != abs(row_vector):
                    possible_moves.append(
                        config.col[self.current_col_index + col_vector]
                        + config.row[self.current_row_index + row_vector]
                    )
        return possible_moves


class Bishop(Piece):
    """ S is used to differentiate from the B in black, and I looks
    like 1."""

    def __init__(self, color, num_id, start_space, current_space):
        data = {
            "color": color,
            "num_id": num_id,
            "start_space": start_space,
            "current_space": current_space,
            "piece_type": "bishop",
            "unit": "S",
            "move_vector": list(range(-7, 8))
        }
        super().__init__(**data)

    # Bishops can move max spaces diagonally. This is represented by
    # adding -7 through 7 to each col index and row index equally at
    # the same time. By having neither the col_vector or row_vector
    # equal to 0, we've eliminated up, down, left, and right motion.
    # The col_vector equal to row_vector as well as -1 * row_vector
    # constrains movement to the diagonals.
    def legal_move(self):
        possible_moves = []
        for col_vector in self.move_vector:
            for row_vector in self.move_vector:
                if 0 <= self.current_col_index + col_vector <= 7 \
                        and 0 <= self.current_row_index + row_vector <= 7 \
                        and (col_vector != 0 and row_vector != 0) \
                        and (col_vector == row_vector
                             or col_vector == -1 * row_vector):
                    possible_moves.append(
                        config.col[self.current_col_index + col_vector]
                        + config.row[self.current_row_index + row_vector]
                    )
        return possible_moves


class Queen(Piece):
    def __init__(self, color, num_id, start_space, current_space):
        data = {
            "color": color,
            "num_id": num_id,
            "start_space": start_space,
            "current_space": current_space,
            "piece_type": "queen",
            "unit": "Q",
            "move_vector": list(range(-7, 8))
        }
        super().__init__(**data)

    # Queens can move max spaces in all directions. Rather than
    # try to eliminate the regions she can't move to, we will
    # simplify things by having her move in the patterns of the
    # rook, and bishop combined.
    def legal_move(self):
        possible_moves = []
        for col_vector in self.move_vector:
            if 0 <= self.current_col_index + col_vector <= 7 \
                    and col_vector != 0:
                possible_moves.append(
                    config.col[self.current_col_index + col_vector]
                    + config.row[self.current_row_index]
                )
        for row_vector in self.move_vector:
            if 0 <= self.current_row_index + row_vector <= 7 \
                    and row_vector != 0:
                possible_moves.append(
                    config.col[self.current_col_index]
                    + config.row[self.current_row_index + row_vector]
                )
        for col_vector in self.move_vector:
            for row_vector in self.move_vector:
                if 0 <= self.current_col_index + col_vector <= 7 \
                        and 0 <= self.current_row_index + row_vector <= 7 \
                        and (col_vector != 0 and row_vector != 0) \
                        and (col_vector == row_vector
                             or col_vector == -1 * row_vector):
                    possible_moves.append(
                        config.col[self.current_col_index + col_vector]
                        + config.row[self.current_row_index + row_vector]
                    )
        return possible_moves


class King(Piece):
    def __init__(self, color, start_space, current_space):
        self.start_col_index = 4
        data = {
            "color": color,
            "num_id": "",
            "start_space": start_space,
            "current_space": current_space,
            "piece_type": "king",
            "unit": "KG",
            "has_moved": False,
            "move_vector": list(range(-1, 2))
        }
        super().__init__(**data)

    # TODO: ADD CASTLING!!!!
    # Kings can move 1 space in all directions, represented by
    # adding -1, 0, and 1 to each row and column index.
    def legal_move(self):
        possible_moves = []
        for col_vector in self.move_vector:
            for row_vector in self.move_vector:
                if 0 <= self.current_col_index + col_vector <= 7 \
                        and 0 <= self.current_row_index + row_vector <= 7 \
                        and (col_vector != 0 or row_vector != 0):
                    possible_moves.append(
                        config.col[self.current_col_index + col_vector]
                        + config.row[self.current_row_index + row_vector]
                    )
        # Castling positions
        for col_vector in (-2, 2):
            possible_moves.append(
                config.col[self.current_col_index + col_vector]
                + config.row[self.current_row_index]
            )
        return possible_moves


class OpenSpace:
    def __init__(self):
        self.display = "   "
        self.color = "blank"  # TODO EXP... pawn_blocked 2nd and condition
        self.piece_type = None
        self.unit = None

    def __str__(self):
        return self.display

    def __repr__(self):
        return "Open space"


class Player:
    def __init__(self, color):
        self.color = color
        self.color_id = color[0].capitalize()
        #   TODO Is commented section necessary? Originally unused in chess.py
        # if color == "white":
        #     self.space_row_vector = -1
        # else:
        #     self.space_row_vector = 1

    def __str__(self):
        return f"{self.color} player"

    def __repr__(self):
        return f"Player object, color: {self.color}"


# Create all Piece and OpenSpace objects
pawns = []
for color in ("white", "black"):
    for num_id in range(1, 9):
        if color == "white":
            shift = 0
        else:
            shift = 8
        pawns.append(Pawn(color, num_id, config.p_start[num_id - 1 + shift],
                     config.p_start[num_id - 1 + shift])
                     )

rooks = []
for color in ("white", "black"):
    for num_id in range(1, 3):
        if color == "white":
            shift = 0
        else:
            shift = 2
        rooks.append(Rook(color, num_id, config.r_start[num_id - 1 + shift],
                          config.r_start[num_id - 1 + shift])
                     )

knights = []
for color in ("white", "black"):
    for num_id in range(1, 3):
        if color == "white":
            shift = 0
        else:
            shift = 2
        knights.append(Knight(color, num_id,
                              config.n_start[num_id - 1 + shift],
                              config.n_start[num_id - 1 + shift])
                       )

bishops = []
for color in ("white", "black"):
    for num_id in range(1, 3):
        if color == "white":
            shift = 0
        else:
            shift = 2
        bishops.append(Bishop(color, num_id,
                              config.s_start[num_id - 1 + shift],
                              config.s_start[num_id - 1 + shift])
                       )

queens = []
for color in ("white", "black"):
    num_id = 1
    if color == "white":
        shift = 0
    else:
        shift = 1
    queens.append(Queen(color, num_id, config.q_start[shift],
                        config.q_start[shift])
                  )

kings = []
for color in ("white", "black"):
    if color == "white":
        shift = 0
    else:
        shift = 1
    kings.append(King(color, config.k_start[shift], config.k_start[shift]))

#
open_spaces = []
for space in range(0, 33):
    open_spaces.append(OpenSpace())

# Assign starting positions to piece and open space objects
pawns_d = dict(zip(config.p_start, pawns))
rooks_d = dict(zip(config.r_start, rooks))
knights_d = dict(zip(config.n_start, knights))
bishops_d = dict(zip(config.s_start, bishops))
queens_d = dict(zip(config.q_start, queens))
kings_d = dict(zip(config.k_start, kings))
open_spaces_d = dict(zip(config.open_space_start, open_spaces))

# Create dictionaries for looking up pieces
starting_pieces = {**pawns_d, **rooks_d, **knights_d, **bishops_d, **queens_d,
                   **kings_d}
starting_rooks = {"white": {"queenside": rooks[0], "kingside": rooks[1]},
                  "black": {"queenside": rooks[2], "kingside": rooks[3]}}

# Create dictionary of all spaces and the current objects occupying them to
# pull .display attributes from in order to print the board
on_board = {**starting_pieces, **open_spaces_d}

# Acquire all .display values of piece objects for reference purposes
pieces_list = list(starting_pieces.values())
game_pieces = []
for piece in range(len(pieces_list)):
    game_pieces.append(pieces_list[piece].display)
