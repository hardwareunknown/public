height = 8
width = 8
col = ("A", "B", "C", "D", "E", "F", "G", "H")
row = ("8", "7", "6", "5", "4", "3", "2", "1")
# Logic of board color: odd row + odd column = black, even row + even
# column = black (if "A" was 1, "B" was 2, etc.), rest of the spaces
# are white. However, since range(n) values start at 0 rather than 1,
# odd rows/columns use % 2 == 0 and even rows/columns use % 2 != 0 to
# describe their position. row_id range is reversed due to printing
# board from top (row 8) to bottom (row 1).
board_color = tuple(" " if col_id % 2 == 0 and row_id % 2 == 0
                    or col_id % 2 != 0 and row_id % 2 != 0 else "#"
                    for col_id in range(width)
                    for row_id in reversed(range(height)))
board_pos_id = tuple([(col[col_id] + row[row_id])
                      for row_id in range(height)
                      for col_id in range(width)])
board_pos_num = tuple(range(len(board_pos_id)))
board_pos = dict(zip(board_pos_id, board_pos_num))
open_space_start = tuple(col[col_id] + row[row_id]
                         for col_id in range(width)
                         for row_id in range(2, 6))
# Start and name variables: initial letter is the piece unit ID
# start == the spaces those pieces begin a game at
# names == keys for pieces dictionary
p_start = ("A2", "B2", "C2", "D2", "E2", "F2", "G2", "H2",
           "A7", "B7", "C7", "D7", "E7", "F7", "G7", "H7"
           )
r_start = ("A1", "H1", "A8", "H8")
n_start = ("B1", "G1", "B8", "G8")
s_start = ("C1", "F1", "C8", "F8")
q_start = ("D1", "D8")
k_start = ("E1", "E8")
p_names = ("WP1", "WP2", "WP3", "WP4", "WP5", "WP6", "WP7", "WP8",
           "BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7", "BP8"
           )
r_names = ("WR1", "WR2", "BR1", "BR2")
n_names = ("WN1", "WN2", "BN1", "BN2")
s_names = ("WS1", "WS2", "BS1", "BS2")
q_names = ("WQ1", "BQ1")
k_names = ("WKG", "BKG")
white_attacked_spaces = {"WP1": ["B3"], "WP8": ["G3"],
                         "WP2": ["A3", "C3"], "WP3": ["B3", "D3"],
                         "WP4": ["C3", "E3"], "WP5": ["D3", "F3"],
                         "WP6": ["E3", "G3"], "WP7": ["F3", "H3"],
                         "WN1": ["A3", "C3"], "WN2": ["F3", "H3"]}
black_attacked_spaces = {"BP1": ["B6"], "BP8": ["G6"],
                         "BP2": ["A6", "C6"], "BP3": ["B6", "D6"],
                         "BP4": ["C6", "E6"], "BP5": ["D6", "F6"],
                         "BP6": ["E6", "G6"], "BP7": ["F6", "H6"],
                         "BN1": ["A6", "C6"], "BN2": ["F6", "H6"]}