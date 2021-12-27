import chess_config as config
from gameboard import print_board
import chess_pieces as pieces

# TODO add "en passant is not available", "there is no piece there" (for
#  diagonal pawn movements), and "you have already moved your king"/"you
#  have already moved that rook" messages to the move_blocked responses,
#  to give more context, also change pawns moving to diagonal spaces without
#  pieces on them to read "that is an illegal move" rather than "that space
#  is blocked"... as it is confusing with no piece on that space.... more a
#  stylistic thing as "blocked" here simply means the piece would be
#  capable of the move, there is just no piece there to take. This
#  contrasts with trying to move a knight to an adjacent space, where the
#  move is truly illegal

# TODO General:
#  After moving WP4 to D4 on the first move, WKG attacked_spaces does not
#  update to include D2

white_player = pieces.Player("white")
black_player = pieces.Player("black")
board = pieces.on_board
turn_count = 0
promoted_pieces = []
w_attacked_spaces = config.white_attacked_spaces
b_attacked_spaces = config.black_attacked_spaces


def pieces_remaining():
    """ Returns a list of display attributes (labels) from all of the pieces
        currently left on the board. This will be used to check if a
        player's piece_choice still remains, or if it has been taken.
        """
    remaining_pieces_objects = list(board.values())
    remaining_pieces = {"displays": [], "objects": []}
    for piece in remaining_pieces_objects:
        if piece.piece_type is not None:
            remaining_pieces["displays"].append(piece.display)
            remaining_pieces["objects"].append(piece)
    return remaining_pieces


def choose_piece(player, remaining_pieces):
    """ Asks a player for which piece they would like to move. This can
        be either the full piece label (ex. "WS1", "BKG") or a player
        can simply enter the piece label without their color ID
        (ex. "S1", "KG").
        """
    while True:
        piece_choice = input("What piece would you like to move?: ").strip() \
            .upper()
        if len(piece_choice) < 3:
            piece_choice = player.color_id + piece_choice
        if piece_choice not in pieces.game_pieces:
            print("That piece does not exist.")
            continue
        elif player.color_id not in piece_choice:
            print("That is not your piece.")
            continue
        elif piece_choice not in remaining_pieces["displays"]:
            print("That piece has been taken.")
            continue
        else:
            break
    return piece_choice


def find_current_piece(piece_choice):
    """ Takes in the string piece_choice and returns the associated
        Piece object. This can then be used to check attributes of that
        object.
        """
    remaining_pieces_objects = list(board.values())
    piece_choice_obj = next(obj for obj in remaining_pieces_objects
                            if obj.display == piece_choice)
    return piece_choice_obj


def where_to_move(player, piece_choice_obj):
    """ Asks the player where they would like to move their chosen piece
        to and returns this as the variable move_to, a string.

        The player enters where they would like to move to using
        the plain text space ID, ie. "A1", "C8", "H4". There is no need
        for proper chess notation as this game is meant to be as easy as
        possible for anybody to play. This is why there are separate
        inputs for piece and destination.
        """
    legal_moves = piece_choice_obj.legal_move()
    while True:
        move_to = input(f"Where would you like to move "
                        f"{piece_choice_obj.display} to? (X to cancel):"
                        ).strip().upper()
        if move_to == "X":
            break
        elif move_to not in board.keys():
            print("That space does not exist.")
            continue
        elif move_to == piece_choice_obj.current_space:
            print(f"{piece_choice_obj.display} is already on {move_to}.")
            continue
        elif move_to not in legal_moves:
            print("That is an illegal move.")
            continue
        elif move_blocked(player, piece_choice_obj, move_to):
            print("That space is blocked.")
            continue
        else:
            break
    return move_to


def confirm_move(piece_choice, move_to):
    """ Asks the player to confirm their chosen piece and location to
        move the piece to. It returns either "y" or "n".
        """
    while True:
        confirmation = input(f"You would like to move {piece_choice} to "
                             f"{move_to}, is that correct? (y/n): """
                             ).strip().lower()
        if confirmation not in ["y", "n"]:
            print('Invalid response. Please respond with "y" for yes or "n" '
                  'for no.')
            continue
        else:
            break
    return confirmation


def pawn_move(piece_choice_obj):
    """ Modifies necessary attributes of Pawn object after a move."""
    # turn_count saved to check for en passant on enemy's next turn
    piece_choice_obj.last_turn_moved = turn_count
    # Pawn moved 2 spaces on initial move, used to check for en passant
    if not piece_choice_obj.has_moved \
            and piece_choice_obj.current_row_index == \
            piece_choice_obj.start_row_index \
            + (2 * piece_choice_obj.row_vector):
        piece_choice_obj.two_space_move = True
    if not piece_choice_obj.has_moved:
        piece_choice_obj.has_moved = True


def special_move_check(player, piece_choice_obj, move_to, space_vector):
    """ Checks to see if a special move (en passant or castling) has
        occurred. A dictionary is returned containing the result, as
        well as the necessary information for the perform_move function.
        """
    move_to_col_index = config.col.index(move_to[0])
    # If en passant has occurred
    if piece_choice_obj.piece_type == "pawn" \
            and move_to[0] != piece_choice_obj.current_space[0] \
            and board[move_to].piece_type is None:
        special_move_executed = True
        special_move_type = "en_passant"
        special_space_1 = en_passant(piece_choice_obj)["enemy_space"]
        special_action_1 = pieces.OpenSpace()
        special_space_2 = None
        special_action_2 = None
    # If castling has occurred
    elif piece_choice_obj.piece_type == "king" \
            and (move_to_col_index == 2
                 or move_to_col_index == 6) \
            and not piece_choice_obj.has_moved:
        special_move_executed = True
        special_move_type = "castling"
        castle_result = castle(player, piece_choice_obj, move_to, space_vector)
        special_space_1 = castle_result["castle_space"]
        special_action_1 = castle_result["castle_rook"]
        special_space_2 = castle_result["castle_rook_start"]
        special_action_2 = pieces.OpenSpace()
    else:
        special_move_executed = False
        special_move_type = None
        special_space_1 = None
        special_space_2 = None
        special_action_1 = None
        special_action_2 = None
    special_move_result = {"executed": special_move_executed,
                           "type": special_move_type,
                           "space_1": special_space_1,
                           "space_2": special_space_2,
                           "action_1": special_action_1,
                           "action_2": special_action_2
                           }
    return special_move_result


def space_shift(piece_choice_obj, move_to):
    """ Basic movement of pieces on board, and modifying piece
        attributes accordingly. "Basic" in that it does not perform
        special moves including en passant and castling.
        """
    (board[move_to], board[piece_choice_obj.current_space]) = \
        (piece_choice_obj, pieces.OpenSpace())
    piece_choice_obj.current_space = move_to
    (piece_choice_obj.current_col_index,
     piece_choice_obj.current_row_index) = \
        (config.col.index(piece_choice_obj.current_space[0]),
         config.row.index(piece_choice_obj.current_space[1]))


def perform_move(player, piece_choice_obj, move_to, space_vector):
    """ Moves Piece object to move_to space and performs any special
        move operations such as also moving the rook when castling, as
        well as taking the enemy pawn in en passant after the friendly
        pawn has moved.
        """
    special_move = special_move_check(player, piece_choice_obj,
                                      move_to, space_vector)
    if special_move["executed"] and special_move["type"] == "en_passant":
        space_shift(piece_choice_obj, move_to)
        board[special_move["space_1"]] = special_move["action_1"]
    elif special_move["executed"] and special_move["type"] == "castling":
        space_shift(piece_choice_obj, move_to)
        board[special_move["space_1"]] = special_move["action_1"]
        board[special_move["space_2"]] = special_move["action_2"]
    else:
        space_shift(piece_choice_obj, move_to)
    global turn_count
    turn_count += 1
    if piece_choice_obj.piece_type == "pawn":
        pawn_move(piece_choice_obj)
        if piece_choice_obj.current_row_index in (0, 7):
            promote_pawn(piece_choice_obj)
    elif piece_choice_obj.piece_type in ("rook", "king") \
            and not piece_choice_obj.has_moved:
        piece_choice_obj.has_moved = True


def player_move(player):
    """ Gathers player input player input on what they would like to
        move where, then executes the move.
        """
    print(f"Your turn {player}.")
    pieces_left = pieces_remaining()
    while True:
        piece_choice = choose_piece(player, pieces_left)
        piece_choice_obj = find_current_piece(piece_choice)
        move_to = where_to_move(player, piece_choice_obj)
        if move_to == "X":
            continue
        confirmation = confirm_move(piece_choice, move_to)
        if confirmation == "n":
            continue
        else:
            break
    space_vector = create_space_vector(piece_choice_obj, move_to)
    perform_move(player, piece_choice_obj, move_to, space_vector)


def find_space_vector_direction(piece_choice_obj, move_to):
    """ A space_vector (ie. an ordered list of spaces within a piece's
        potential movement) is needed to run move_blocked(). The vector
        will be iterated over, with move_blocked() checking if there are
        pieces at any of the spaces. In order to create the space_vector
        we first use find_vector_direction() to determine the directions
        of row and column movement from current_space to move_to,
        represented as 1 and -1. These will then be used in
        create_space_vector() to iterate over spaces of the board,
        appending the results to the space_vector.
        """
    move_to_col = move_to[0]
    move_to_row = move_to[1]
    current_col_index = piece_choice_obj.current_col_index
    current_row_index = piece_choice_obj.current_row_index
    move_to_col_index = config.col.index(move_to_col)
    move_to_row_index = config.row.index(move_to_row)

    # move_to is directly above current space.
    if move_to_col_index == current_col_index \
            and move_to_row_index < current_row_index:
        space_col_direction = 0
        space_row_direction = -1
    # move_to is to the right and up from current space.
    elif move_to_col_index > current_col_index \
            and move_to_row_index < current_row_index:
        space_col_direction = 1
        space_row_direction = -1
    # move_to is directly to the right of current space.
    elif move_to_col_index > current_col_index \
            and move_to_row_index == current_row_index:
        space_col_direction = 1
        space_row_direction = 0
    # move_to is to the right and down from current space.
    elif move_to_col_index > current_col_index \
            and move_to_row_index > current_row_index:
        space_col_direction = 1
        space_row_direction = 1
    # move_to is directly below current space.
    elif move_to_col_index == current_col_index \
            and move_to_row_index > current_row_index:
        space_col_direction = 0
        space_row_direction = 1
    # move_to is to the left and down from current space.
    elif move_to_col_index < current_col_index \
            and move_to_row_index > current_row_index:
        space_col_direction = -1
        space_row_direction = 1
    # move_to is directly to the left of current space.
    elif move_to_col_index < current_col_index \
            and move_to_row_index == current_row_index:
        space_col_direction = -1
        space_row_direction = 0
    # move_to is to the left and up from current space.
    #
    # if statement would be:
    # elif move_to_col_index < current_col_index \
    #         and move_to_row_index < current_row_index:
    else:
        space_col_direction = -1
        space_row_direction = -1
    space_vector_direction = {"col_dir": space_col_direction,
                              "row_dir": space_row_direction}
    return space_vector_direction


def create_space_vector(piece_choice_obj, move_to):
    """ A space_vector (ie. an ordered list of Piece objects at the
        spaces within a piece's potential movement) is needed to run
        move_blocked(). The vector will be iterated over, with
        move_blocked() checking if there are pieces at any of the
        spaces. In order to create the space_vector we first use
        find_vector_direction() to determine the directions of row and
        column movement from current_space to move_to, represented as 1
        and -1. These will then be used in create_space_vector() to
        iterate over spaces of the board, appending the results to the
        space_vector.
        """
    space_vector_direction = find_space_vector_direction(piece_choice_obj,
                                                         move_to)
    spaces = []
    move_to_col = move_to[0]
    move_to_row = move_to[1]
    current_col_index = piece_choice_obj.current_col_index
    current_row_index = piece_choice_obj.current_row_index
    move_to_col_index = config.col.index(move_to_col)
    move_to_row_index = config.row.index(move_to_row)
    # Initialize space_col_index and space_row index at current space.
    space_col_index = current_col_index
    space_row_index = current_row_index
    if piece_choice_obj.piece_type == "knight":
        space_vector = [board[move_to]]
    else:
        # As long as the examined space to add to the space vector is not
        # the move_to space, run the loop. It will iterate space_col_index
        # and space_row_index by one space in direction of movement each
        # time. Then add that space to the spaces list. Once the loop
        # reaches the move_to space, it adds it to the list. The next round
        # of the loop has the examined space equal to the move_to space, so
        # the loop breaks.
        while space_col_index != move_to_col_index \
                or space_row_index != move_to_row_index:
            space_col_index += space_vector_direction["col_dir"]
            space_row_index += space_vector_direction["row_dir"]
            space = config.col[space_col_index] + config.row[space_row_index]
            spaces.append(space)
        space_vector = [None] * len(spaces)
        for space in spaces:
            space_vector[spaces.index(space)] = board[space]
    return space_vector


def all_open(space_vector):
    """ Returns True if space_vector contains only open spaces."""
    return all(space.piece_type is None for space in space_vector)


def en_passant(piece_choice_obj):
    """ Checks to see if an enemy pawn can be taken via en passant. A
        dictionary is returned containing the result, as well as the
        necessary information for the perform_move function).
        """
    en_passant_friendly_space = []
    en_passant_enemy_space = []
    en_passant_enemy_object = []
    current_col_index = piece_choice_obj.current_col_index
    for col_vector in (-1, 1):
        if 0 <= current_col_index + col_vector <= 7:
            row_adjacent_obj = board[
                config.col[piece_choice_obj.current_col_index + col_vector]
                + config.row[piece_choice_obj.current_row_index]]
        else:
            continue
        # En passant conditions:
        #
        # 1) If friendly pawn is in its 5th row AND
        # 2) The adjacent space in the same row has a pawn on it AND
        # 3) That pawn is an enemy pawn AND
        # 4) The enemy piece moved two spaces on its first move AND
        # 5) The turn being played is the immediate turn following the
        # two-space move
        # THEN the enemy pawn can be taken by the friendly pawn moving
        # into the space the enemy pawn moved through (ie. the 6th row
        # space in the column of the enemy pawn. The for loop checks
        # both the left and right adjacent spaces.
        if piece_choice_obj.current_row_index == \
                piece_choice_obj.start_row_index + \
                (3 * piece_choice_obj.row_vector) \
                and row_adjacent_obj.piece_type == "pawn" \
                and piece_choice_obj.color != row_adjacent_obj.color \
                and row_adjacent_obj.two_space_move \
                and row_adjacent_obj.last_turn_moved == turn_count:
            en_passant_friendly_space.append(
                config.col[current_col_index + col_vector]
                + config.row[piece_choice_obj.current_row_index +
                             piece_choice_obj.row_vector])
            en_passant_enemy_space.append(row_adjacent_obj.current_space)
            en_passant_enemy_object.append(row_adjacent_obj)
    if len(en_passant_friendly_space) > 0:
        en_passant_available = True
    else:
        en_passant_available = False
        en_passant_friendly_space = [None]
        en_passant_enemy_space = [None]
        en_passant_enemy_object = [None]
    en_passant_result = {"available": en_passant_available,
                         "friendly_space": en_passant_friendly_space[0],
                         "enemy_space": en_passant_enemy_space[0],
                         "enemy_object": en_passant_enemy_object[0]
                         }
    return en_passant_result


# TODO BP5 can move to D6 right off the bat... the confirmation is asked for
#  and it is not being blocked. WP4 is being blocked from C3...maybe
#  correctly, but why is it different than Bp5 to D6?
def pawn_blocked(player, piece_choice_obj, move_to, space_vector):
    """ Determines if any pieces are in the way preventing the pawn
        from moving, taking into account if the piece is an enemy piece
        and can be taken. pawn_blocked is broken out to maintain flatter
        code due to the pawn having special rules involving diagonal
        and en passant capture.
        """
    move_to_col_index = config.col.index(move_to[0])
    en_passant_check = en_passant(piece_choice_obj)
    if all_open(space_vector) \
            and move_to_col_index == piece_choice_obj.current_col_index:
        return False
    # Diagonal capture conditions:
    # 1) All pieces before the move_to are open
    # 2) There is a piece on move_to
    # 3) The piece on move_to is an enemy piece
    # 4) move_to is not in the same column as the pawn (we want
    # to restrict blocking to only affecting spaces immediately
    # in front of a pawn).
    # NOTE: This elif should also account for if the diagonal space
    # is blank, and the pawn is thus blocked from moving. The
    # condition of "and space_vector[-1] != open_space" would be
    # violated if the space was an open_space, thus the function
    # would move to the else statement, and return True (ie. the
    # pawn is blocked).
    # TODO **TEST** check if I have to add condition for if the diagonal
    #  space is blank... currently it seems that the below elif should cover
    #  that. The condition of "and space_vector[-1].piece_type is not None
    #  would be violated if the space was an open space, thus the function
    #  would move to the else statement, and return True (ie. it is
    #  blocked)
    # TODO check if below commented code must be added back as a check in
    #  the below elif... I don't believe it needs to be as for
    #  non-same-column moves (ie. diagonal capture) there is only one space
    #  in the space vector
    # all_open(space_vector[:-1]) and \
    elif space_vector[-1].piece_type is not None \
            and space_vector[-1].color != player.color \
            and move_to_col_index != piece_choice_obj.current_col_index:
        return False
    # Added 'and move_to == en_passant_check["friendly_space"]' because
    # of the following scenario:
    #
    # BP5 is at E6, WP5 moves to E5, BP4 does a two-space move to D5,
    # enabling en passant if WP5 moves this turn. WP5 decides instead to
    # move to E6. By the rules, this should be blocked. However, it is
    # allowed (See below).
    #
    # Only using en_passant_check["available"] causes pawn_blocked() to
    # return False, because en passant can be performed on BP4. Since
    # the pawn is considered not blocked, and move_to is set to E6, WP5
    # is then able to take forward, replacing BP5 on E6. Pawns can't
    # take forward, hence we check to make sure that move_to is set to
    # the en passant friendly space (ie. the player intends to actually
    # perform en passant) before we consider the move not blocked.
    elif en_passant_check["available"] \
            and move_to == en_passant_check["friendly_space"]:
        return False
    else:
        return True


def knight_blocked(player, space_vector):
    """ Determines if a knight's move is blocked, taking into account
        they can jump over other pieces.
        """
    if space_vector[-1].piece_type is not None and space_vector[-1].color \
            == player.color:
        return True
    else:
        return False


# TODO update this function once king in check/sattacked spaces is finished
#  so that king cannot castle through check
def castle(player, piece_choice_obj, move_to, space_vector):
    """ Checks to see if castling is available on the move_to side of
        the board. A dictionary is returned containing the result, as
        well as the necessary information for the perform_move function.
        """
    # TODO add conditions to prevent king from castling if it is in check or
    #  would pass through check (can't get out of check or pass through
    #  check when castling), as well as condition blocking castling if there
    #  are pieces between the king and the castle... finally check that
    #  king/rook has_moved functions work
    #
    # TODO: make sure that the castling function operates off of a space
    #  vector... if castling
    #  IS available, may just hard-code the space vector values since this
    #  function is checking if a space vector has any
    #  attacking spaces. If the king "teleports" and never "space vector
    #  checks" the spaces in between, it would only theoretically prevent
    #  moving into check, while missing going through check to get to move_to
    #
    # TODO: for moving through check ---
    #  run a space vector out for the move... if space vector contains
    #  element from team attacked spaces, king will move through check
    move_to_col_index = config.col.index(move_to[0])
    # Queenside castling
    if piece_choice_obj.current_space == piece_choice_obj.start_space \
            and move_to_col_index in (2, 3):
        # When queenside castling, add position at column B in
        # respective row to space_vector before checking if spaces are
        # open (due to rook longer distance between king and rook).
        space_vector.append(
            board[config.col[1] +
                  config.row[piece_choice_obj.current_row_index]]
        )
        castle_rook = pieces.starting_rooks[player.color]["queenside"]
        castle_rook_start = castle_rook.start_space
        castle_space = config.col[3] + \
            config.row[piece_choice_obj.current_row_index]
    # Kingside castling
    elif piece_choice_obj.current_space == piece_choice_obj.start_space \
            and move_to_col_index in (5, 6):
        castle_rook = pieces.starting_rooks[player.color]["kingside"]
        castle_rook_start = castle_rook.start_space
        castle_space = config.col[5] + \
            config.row[piece_choice_obj.current_row_index]
    else:
        castle_rook = None
        castle_rook_start = None
        castle_space = None
    if castle_rook is None:
        castle_available = False
    elif all_open(space_vector) and not piece_choice_obj.has_moved \
            and not castle_rook.has_moved:
        castle_available = True
    else:
        castle_available = False
    castle_result = {"available": castle_available,
                     "castle_rook": castle_rook,
                     "castle_rook_start": castle_rook_start,
                     "castle_space": castle_space
                     }
    return castle_result


# TODO test king_blocked() (may need further development to finish)
def king_blocked(player, piece_choice_obj, move_to, space_vector):
    """ Determines if any pieces are in the way preventing the king
        from moving, taking into account if either the king or a rook
        has moved when trying to castle, and if the king is in check or
        not.
        """
    can_castle = castle(player, piece_choice_obj, move_to,
                        space_vector)["available"]
    if will_move_into_check(player, move_to):
        return True
    elif can_castle:
        return False
    elif all_open(space_vector):
        return False
    # TODO Check over following code... copied from else statement of
    #  move_blocked()
    elif all_open(space_vector[:-1]) \
            and space_vector[-1].piece_type is not None \
            and space_vector[-1].color != player.color:
        return False
    else:  # When friendly piece is at move_to
        return True


def move_blocked(player, piece_choice_obj, move_to):
    """ Determines if any pieces are in the way preventing the chosen
        piece from moving, taking into account jumping rules for the
        knight as well as if the piece is an enemy piece and can be
        taken.
        """
    # Uses functions to create a space_vector, ie. a list populated in
    # order with the Piece objects located at spaces originating from
    # the current space and out to the move_to space. Given that this
    # function works off the argument move_to, this vector originates
    # from the current position of the piece and fires out to the
    # move_to position. Keep in mind we have already checked that this
    # move is theoretically within the legal movement pattern of the
    # piece using legal_move(move_to) func. Thus, we only need to check
    # the chosen movement vector rather than each of the possible ones
    # individually.
    #
    # To check if a space is blocked, we simply need to check the
    # following scenarios:
    # 1) Is the entire vector empty? If yes, the piece is free to move
    #  to the final position of the vector. ie. Not blocked.
    # 2) Is the final position occupied by an enemy piece? If yes, the
    #  piece can move and take it. ie. Not blocked.
    # 3) Is the final position occupied by a friendly piece? If yes,
    #  piece is blocked.
    # 4) Is there a piece along the path? ie. A position other than
    #   the final position. If yes, piece is blocked.
    space_vector = create_space_vector(piece_choice_obj, move_to)
    # Different move rules since pawns can't take forward
    if piece_choice_obj.piece_type == "pawn":
        return pawn_blocked(player, piece_choice_obj, move_to, space_vector)
    # Different move rules since knights can jump
    elif piece_choice_obj.piece_type == "knight":
        return knight_blocked(player, space_vector)
    # Different move rules since kings can castle
    elif piece_choice_obj.piece_type == "king":
        return king_blocked(player, piece_choice_obj, move_to, space_vector)
    # All other pieces can move if their path is open, or if an enemy
    # piece is at the end of their path.
    else:
        if all_open(space_vector):
            return False
        elif all_open(space_vector[:-1]) \
                and space_vector[-1].piece_type is not None \
                and space_vector[-1].color != player.color:
            return False
        else:
            return True
# TODO Add reasons to blocked function... ie if a king is blocked because a
#  friendly piece is there, or if it is because it would move into check...
#  if a pawn can't move two spaces forward, or if a pawn can't move
#  diagonally without taking, etc.... make these into a list, ie. return the
#  False/True value as well as "reason":... similar to how castle() returns
#  are done with multiple variables store in one list that is returned


def promote_pawn(piece_choice_obj):
    """ Packages all promotion functions into one."""
    promote_to = promote_to_what(piece_choice_obj)
    next_num_id = find_next_num_id(promote_to)
    promote_piece(piece_choice_obj, promote_to, next_num_id)


def promote_to_what(piece_choice_obj):
    """ Asks the player what piece they would like to promote their
        pawn to, then calls the associated promotion function."""
    while True:
        promote_to = input(f"What would you like to promote"
                           f" {piece_choice_obj} to?: (Q/N/R/S)")\
            .strip().upper()
        if promote_to not in ("Q", "N", "R", "S"):
            print("That is not a legal promotion.")
            continue
        else:
            break
    return promote_to


def find_next_num_id(promote_to):
    """ Determines the next num_id attribute for the desired
        promotion."""
    initial_qnrs = list(filter(lambda piece:
                               piece.unit in ("Q", "N", "R", "S"),
                               pieces.starting_pieces.values()))
    global promoted_pieces
    similar_pieces = list(filter(lambda piece: piece.unit == promote_to,
                                 initial_qnrs + promoted_pieces))
    max_num_id = max(map(lambda piece: piece.num_id, similar_pieces))
    next_num_id = max_num_id + 1
    return next_num_id


def promote_piece(piece_choice_obj, promote_to, next_num_id):
    """ Performs requested promotion, replacing the pawn with the
        desired piece object."""
    if promote_to == "Q":
        promoted_piece = pieces.Queen(piece_choice_obj.color, next_num_id,
                                      piece_choice_obj.current_space,
                                      piece_choice_obj.current_space)
    elif promote_to == "N":
        promoted_piece = pieces.Knight(piece_choice_obj.color, next_num_id,
                                       piece_choice_obj.current_space,
                                       piece_choice_obj.current_space)
    elif promote_to == "R":
        promoted_piece = pieces.Rook(piece_choice_obj.color, next_num_id,
                                     piece_choice_obj.current_space,
                                     piece_choice_obj.current_space)
    else:
        promoted_piece = pieces.Bishop(piece_choice_obj.color, next_num_id,
                                       piece_choice_obj.current_space,
                                       piece_choice_obj.current_space)
    (promoted_piece.current_col_index, promoted_piece.current_row_index) = \
        (config.col.index(piece_choice_obj.current_space[0]),
         config.row.index(piece_choice_obj.current_space[1]))
    global promoted_pieces  # TODO is "global" necessary?
    piece_choice_obj.promoted = True
    promoted_pieces.append(promoted_piece)
    board[piece_choice_obj.current_space] = promoted_piece
    pieces.game_pieces.append(promoted_piece.display)


# TODO: Finish this function. Will need to modify turn_count and turn_count
#  of pawns as well to make sure that en passant rules still come into effect
#  properly, then reverse perform_move's actions
#   https://www.quora.com/How-would-you-make-an-undo-function-in-Python
def undo_last_move():
    pass


def redo_last_move():
    pass


# TODO pawns begin with diagonal attacks... but when WP4 moves to D3,
#  the attacks on D3 don't go away... fix this... currently pawn function
#  does not work because of this
def find_attacked_spaces(piece):
    """ Determines the spaces attacked by an individual piece (ie. which
        moves a piece can make to take an enemy piece)."""
    legal_moves = piece.legal_move()
    if piece.color == "white":
        player = white_player
    else:
        player = black_player
    # Most pieces can take an enemy piece using any legal move. Only
    # exception is for pawns, since they cannot take forward, so we must
    # isolate only the diagonal spaces as attacked_spaces. We do this by
    # first filtering for diagonal_spaces, then filtering again for any
    # allowed moves remaining.
    if piece.piece_type == "pawn":
        diagonal_spaces = list(filter(
            lambda space: space[0] != piece.current_space[0], legal_moves))
        attacked_spaces = list(filter(
            # Filtering for open spaces and spaces occupied by an enemy
            # piece, ie. the spaces a pawn is truly attacking
            lambda space: board[space].piece_type is None or (board[
                space].piece_type is not None and board[space].color !=
                player.color), diagonal_spaces))
    else:
        attacked_spaces = list(filter(lambda space: not move_blocked(
            player, piece, space), legal_moves))
    return attacked_spaces


def update_attacked_spaces():
    """ Determines the spaces attacked by all pieces on the board,
        updating each color's attacked spaces list accordingly. These
        are then compared to a king's position/moves to see if a king
        has been placed into check, or is about to move into/through
        check."""
    remaining_pieces = pieces_remaining()
    for piece in remaining_pieces["objects"]:
        attacked_spaces = find_attacked_spaces(piece)
        if piece.color == "white":
            w_attacked_spaces.update({piece.display: attacked_spaces})
        else:
            b_attacked_spaces.update({piece.display: attacked_spaces})
# TODO add method to switch/update to new piece's attacked positions after
#  promotion of a pawn... ie. switch from diagonal single space attack with
#  pawn to queen attack, etc. Is this covered simply by
#  update_attacked_spaces() running after a move is made?

# TODO finish this
# def is_in_check(player):
#     """ Determines if the King is in check."""
#     for all pieces (of one color) on board:
#         find attacked spaces
#         team_attacked_spaces.append(find attacked spaces) # update instead?
#         # for those pieces which already have a dictionary entry
#     """ For finding if a king is in check, 1st continually find all legal
#         moves (attacked spaces) of each piece. Add each of those to an entry
#         in a dictionary. Must recheck all pieces each turn, since movement
#         of one can blockeither enemy or friendly pieces. If a piece is
#         taken, then remove its entry from the dictionary, i.e. Re opening
#         those spaces to the king. Continue to update the spaces, And when
#         the king is selected then simply perform a check Similar to legal
#         move or move blocked from the database dictionary of spaces that
#         are potentially covered by those pieces. Make sure special
#         conditions are accounted for such as pawns only taking diagonally.
#         To check if king is in check after opposing piece moves, simply run
#         the is_in_check function and print a message. To check if king will
#         be moving into check on his turn, add the exception to the
#         where_to_move function"""
#     pass
# TODO somehow force this or an associated function to check if a move made
#  does not eliminate the check condition... ie. is_in_check is still True
#  after a move_to choice... then prevent that move. This may need to be
#  done within move_blocked


def will_move_into_check(player, move_to):
    if player.color == "white":
        enemy_attacked_spaces = b_attacked_spaces
    else:
        enemy_attacked_spaces = w_attacked_spaces
    if move_to in enemy_attacked_spaces:
        return True
    else:
        return False

    #TODO this function isn't preventing king from moving into check... make
    # it soe that it does


def is_victory(player):
    pass


def is_draw():
    # Check the legal moves function for the king, then see if the king is
    # blocked because of it being in check or passing through check at all
    # spaces.. ie. move_blocked = True for each element of legal_moves,
    # then the king has been checkmated
    #
    # https://www.thesprucecrafts.com/types-of-draws-in-chess-611536
    pass


# TODO finish this function once the actual robots work... likely this should
#  be a separate module
def reset_robots():
    pass


def save_game():
    # Export board positions, pieces, current player move, all piece states,
    # attacked spaces, etc. and any other data to a text file, later to be
    # imported
    pass


def ask_to_load_game():
    # Ask player to input if they want to load a game or start a new one
    #
    # Add to play_chess()
    pass


def load_game():
    # Load in exported text file so the game can update to the previous saved
    # state
    pass


# TODO update this after figuring out how to confirm if a king is in check
#  or not... ie. update is_in_check func, etc.
def play_chess():
    # TODO **TEST** include function to clear piece lists and then re-create
    #  all pieces beforehand? ie. reset the pieces so that all of the piece
    #  lists are not tacking on extra pieces beyond the starting pieces between
    #  sessions. This may not be an issue if the computer turns on and off and
    #  you are playing on the screen, however maybe it is an issue if you
    #  simple start a new game when the actual robots are involved? This may
    #  not be a problem, as re-running the program would like clear
    #  everything. This will need to be done anyway once a game is
    #  completed.
    while True:
        print_board(config.height, config.width, config.board_color,
                    config.board_pos_id, board)
        update_attacked_spaces()
        player_move(white_player)
        print_board(config.height, config.width, config.board_color,
                    config.board_pos_id, board)
        update_attacked_spaces()
        # if is_in_check(black_player):
        #     print("Check, black.")
        # elif is_victory(white_player):
        #     print("Checkmate black. White wins! Congratulations!")
        #     break
        # elif is_draw():
        #     print("It's a draw!")
        #     break
        player_move(black_player)
        # if is_in_check(white_player):
        #     print_board(config.height, config.width, config.board_color,
        #                 config.board_pos_id, board)
        #     print("Check, white.")
        # elif is_victory(black_player):
        #     print_board(config.height, config.width, config.board_color,
        #                 config.board_pos_id, board)
        #     print("Checkmate white. Black wins! Congratulations!")
        #     break
        # elif is_draw():
        #     print_board(config.height, config.width, config.board_color,
        #                 config.board_pos_id, board)
        #     print("It's a draw!")
        #     break


# TODO: Cleanup nested for loops, comments of sections, add variables for
#  simple transformations like " new_col_index = current_col_index + col_vector"
#  function calls, Combine "current space" stuff into function def current_space(style)
#   or perhaps find_space(style, piece_choice, move_to) or similar
#   where style describes what you want to have returned... the current piece
#   there, the ID (A1) the column ID (A), the row ID (1) the
#   current_row_index, or the current_col_index,
play_chess()
