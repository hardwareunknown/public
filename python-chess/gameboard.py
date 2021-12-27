import chess_config as config


def print_board(height, width, color, position, pieces):
    """ Prints a game board with square spaces with "height" rows and
        "width" columns.

        color and position are tuples, and piece a list, that populate
        the respective information into the squares starting from the
        top left, filling each column from left to right, before moving
        down to the next row.

        Colors use a 1-character designation. These fill the blank area
        within each square to help mimic the actual coloration of a game
        board. This is purely an aesthetic choice; you could hard-code
        " " into this argument if you don't care about the spaces
        looking different. ex. For chess, one might use "#" for white,
        and " " for black, assuming a dark themed IDE with light color
        printed text.

        Positions use 2-character designations containing a row and
        column ID. These appear at the bottom right corner of each
        square. ex. A1, B1, C1, A2, B2, C2, A3, B3, C3 for a 3x3 game
        board.

        Pieces use 3-character designations. These are be kept as a
        dictionary so that as the board is re-printed between successive
        turns, the dictionary can be updated to the current piece.
        ex. For chess (from the perspective of the white-side player)
        the leftmost white pawn could be represented by "WP1", and the
        rightmost black rook could be "BR2".
        """
    # Multiplying a list by an integer n creates a new list
    # by concatenating the original list n times.
    #
    # .join concatenates elements of a list, with a separator b/t each.
    top = "┌" + "┬".join(["─"*9]*width) + "┐\n"
    middle = "├" + "┼".join(["─"*9]*width) + "┤\n"
    bottom = "└" + "┴".join(["─"*9]*width) + "┘"
    print(top +
          middle.join(
              ("|" + "|".join([f' {" "}  {color[col + row*width]}  {" "} '
                               for col in range(width)]) + "|\n") +
              ("│" + "│".join(f' {color[col + row*width]} '
                              f'{pieces[config.col[col] + config.row[row]]}'
                              f' {color[col + row*width]} '
                              for col in range(width)) + "│\n") +
              ("|" + "|".join([f' {" "}  {color[col + row*width]} '
                               f'{position[col + row*width]} '
                               for col in range(width)]) + "|\n")
              # range(n) gives a sequence of n elements, with values
              # starting at 0 and ending at n-1 (effectively a list).
              #
              # The for loop below means each element of the range list
              # has its value fed into the index "row". The row'th index
              # element of the list then has its value replaced by
              # whatever is in front of "for" (ie. the string containing
              # the pipes "|").
              #
              # For height 0, an empty list is made, thus no pipe string
              # is added to the list, creating a squashed game board.
              #
              # For height 1, the list [0] is made, which then becomes a
              # single element list with a value of pipe string ["|||"].
              # Since the list being joined only has the one pipe string
              # element, there is no place to add "middle" as a
              # separator, thus we get a single row game board.
              #
              # For height 2, the list ["|||", "|||"] is made. Now, two
              # elements are present in the list, meaning middle.join
              # has place for a separator and "middle" is added between
              # the two pipe strings. This gives us a double row game
              # board.
              #
              # Repeat this process for a game board of height n,
              # noticing that there will be n-1 "middle" separators in
              # the final game board.
              for row in range(height)) +
          bottom)


if __name__ == "__main__":
    height = 3
    width = 3
    color = ("B", "W", "B", "W", "B", "W", "B", "W", "B")
    position = ("A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3")
    pieces = ["one", "two", "thr", "for", "fiv", "six", "svn", "ate", "nin"]
    print_board(height, width, color, position, pieces)
