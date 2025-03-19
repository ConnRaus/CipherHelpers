import curses
from collections import Counter
import re

# Function to calculate letter frequencies and percentages
def calculate_frequencies(text):
    text = text.lower()
    letter_counts = Counter(c for c in text if c.isalpha())  # Only count alphabetic chars
    total_letters = sum(letter_counts.values())
    letter_percentages = {char: (count / total_letters) * 100 for char, count in letter_counts.items()}
    return letter_counts, letter_percentages

# Function to display cipher, counts, percentages, and mappings in respective windows
def display_cipher_info(cipher_win, counts_win, mappings_win, original_text, mapping, letter_counts, letter_percentages, color_map):
    cipher_win.clear()
    counts_win.clear()
    mappings_win.clear()

    # Display the cipher text with mappings in cipher_win
    cipher_win.addstr("Cipher Text:\n\n")

    # Apply the mapping to the original text to generate the displayed text
    displayed_text = ''
    for c in original_text:
        if c.upper() in mapping:
            # Replace with mapped character, preserving case
            to_char, certain = mapping[c.upper()]
            if c.islower():
                mapped_char = to_char.lower()
            else:
                mapped_char = to_char.upper()
            displayed_text += mapped_char
        else:
            displayed_text += c

    # Display the cipher text with colors
    for idx, (c, o_c) in enumerate(zip(displayed_text, original_text)):
        if o_c.upper() in mapping:
            color_pair = color_map.get(o_c.upper(), curses.color_pair(1))
            try:
                cipher_win.addstr(c, color_pair)
            except curses.error:
                pass  # Handle cases where text exceeds window size
        else:
            try:
                cipher_win.addstr(c, curses.color_pair(3))  # Unmapped characters in white
            except curses.error:
                pass
    cipher_win.refresh()

    # Display letter frequencies and percentages in counts_win (two columns)
    counts_win.addstr("Letter Counts and Percentages:\n\n")
    letters = sorted(letter_counts.keys())
    half = (len(letters) + 1) // 2  # Split letters into two roughly equal halves
    first_half = letters[:half]
    second_half = letters[half:]

    for i in range(max(len(first_half), len(second_half))):
        line = ""
        if i < len(first_half):
            char = first_half[i].upper()
            count = letter_counts[first_half[i]]
            percentage = letter_percentages[first_half[i]]
            line += f"{char}: {count} ({percentage:.2f}%)"
        else:
            line += " " * 15  # Padding for alignment

        line += "    "  # Space between columns

        if i < len(second_half):
            char = second_half[i].upper()
            count = letter_counts[second_half[i]]
            percentage = letter_percentages[second_half[i]]
            line += f"{char}: {count} ({percentage:.2f}%)"

        try:
            counts_win.addstr(f"{line}\n")
        except curses.error:
            pass  # Handle cases where text exceeds window size
    counts_win.refresh()

    # Display current mappings in mappings_win with multi-column layout
    mappings_win.addstr("Current Mappings:\n\n")
    mapping_strings = [f"{from_char} -> {to_char}{'?' if not certain else ''}" for from_char, (to_char, certain) in sorted(mapping.items())]

    if not mapping_strings:
        mappings_win.addstr("(No mappings yet)\n")
    else:
        # Determine maximum length of mapping strings
        max_len = max(len(s) for s in mapping_strings) + 2  # Add padding

        # Calculate number of columns that can fit
        mappings_height, mappings_width = mappings_win.getmaxyx()
        column_width = max_len
        columns = max(mappings_width // column_width, 1)

        # Determine number of rows needed
        rows = (len(mapping_strings) + columns - 1) // columns

        # Arrange mappings into columns
        for row in range(rows):
            line = ""
            for col in range(columns):
                index = col * rows + row
                if index < len(mapping_strings):
                    s = mapping_strings[index]
                    from_char = s.split("->")[0].strip()
                    color_pair = color_map.get(from_char, curses.color_pair(1))
                    s_padded = s.ljust(column_width)
                    try:
                        mappings_win.addstr(s_padded, color_pair)
                    except curses.error:
                        pass
            mappings_win.addstr("\n")
    mappings_win.refresh()

# Main function that handles user input and replacements
def cipher_assist(stdscr, cipher_text):
    curses.curs_set(1)  # Enable cursor
    curses.echo()       # Allow user to see what they type
    stdscr.clear()

    original_text = cipher_text  # Keep the original text
    mapping = {}  # Store the mapping from letters to (letter, certain)
    color_map = {}  # Store color pair for each mapping

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Confirmed mappings in green
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Uncertain mappings in yellow
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Unmapped letters in white

    # Get terminal size
    height, width = stdscr.getmaxyx()

    # Define window sizes
    cipher_height = height // 2 - 5  # Top half for cipher text
    counts_height = height // 3 + 5   # Next third for letter counts
    mappings_height = height // 3 # Remaining third for mappings
    instructions_height = 3      # Bottom three lines for instructions and input

    # Create windows
    try:
        cipher_win = curses.newwin(cipher_height - 1, width, 0, 0)
        counts_win = curses.newwin(counts_height - 1, width // 2, cipher_height, 0)
        mappings_win = curses.newwin(mappings_height - 1, width // 2, cipher_height, width // 2)
        instructions_win = curses.newwin(instructions_height, width, cipher_height + counts_height, 0)
    except curses.error:
        stdscr.addstr(0, 0, "Terminal window too small. Please resize and try again.")
        stdscr.refresh()
        stdscr.getch()
        return

    while True:
        # Calculate letter frequencies
        letter_counts, letter_percentages = calculate_frequencies(original_text)
        
        # Display the cipher and letter statistics
        display_cipher_info(cipher_win, counts_win, mappings_win, original_text, mapping, letter_counts, letter_percentages, color_map)
        
        # Display instructions
        instructions_win.clear()
        instructions = "Type 'A->B' to add/update mappings, 'remove A' or 'rm A' to remove mappings, or 'q' to quit."
        instructions_win.addstr(0, 0, instructions, curses.A_BOLD)
        instructions_win.addstr(1, 0, "Input: ")
        instructions_win.refresh()
        
        # Get user input
        instructions_win.move(1, len("Input: "))
        instructions_win.refresh()
        try:
            user_input = instructions_win.getstr(1, len("Input: ")).decode('utf-8').strip()
        except curses.error:
            user_input = ''

        if user_input.lower() == 'q':
            break  # Exit if user types 'q'

        # Handle removal commands
        remove_match = re.match(r'^(remove|rm)\s+([A-Za-z])$', user_input, re.IGNORECASE)
        if remove_match:
            cmd, char = remove_match.groups()
            char = char.upper()
            if char in mapping:
                del mapping[char]
                if char in color_map:
                    del color_map[char]
                feedback = f"Mapping for '{char}' removed."
            else:
                feedback = f"No existing mapping for '{char}'."
            instructions_win.addstr(2, 0, feedback, curses.A_BOLD)
            instructions_win.refresh()
            curses.napms(1000)
            continue  # Skip to next iteration

        # Handle mapping inputs like "A->B" or "A->B?"
        mapping_match = re.match(r'^([A-Za-z])->([A-Za-z])(\?)?$', user_input)
        if mapping_match:
            from_char, to_char, uncertain = mapping_match.groups()
            from_char = from_char.upper()
            to_char = to_char.upper()
            certain = not bool(uncertain)
            
            # Prevent mapping a character to itself
            if from_char == to_char:
                feedback = f"Cannot map character '{from_char}' to itself."
                instructions_win.addstr(2, 0, feedback, curses.A_BOLD)
                instructions_win.refresh()
                curses.napms(1000)
                continue
            
            # Check if to_char is already mapped by another character
            already_mapped = False
            for key, (val, _) in mapping.items():
                if val == to_char and key != from_char:
                    already_mapped = True
                    break
            
            if already_mapped:
                feedback = f"Character '{to_char}' is already mapped from another character. Cannot map '{from_char}' to '{to_char}'."
                instructions_win.addstr(2, 0, feedback, curses.A_BOLD)
                instructions_win.refresh()
                curses.napms(1000)
                continue  # Skip to next iteration
            
            # Check if from_char is already mapped
            if from_char in mapping:
                # Remapping scenario
                mapping[from_char] = (to_char, certain)
                feedback = f"Mapping updated: {from_char} -> {to_char}{'?' if not certain else ''}"
            else:
                # Adding new mapping
                mapping[from_char] = (to_char, certain)
                feedback = f"Mapping added: {from_char} -> {to_char}{'?' if not certain else ''}"
            
            # Assign color based on certainty
            if certain:
                color_map[from_char] = curses.color_pair(1)  # Green for certain
            else:
                color_map[from_char] = curses.color_pair(2)  # Yellow for uncertain
            
            instructions_win.addstr(2, 0, feedback, curses.A_BOLD)
            instructions_win.refresh()
            curses.napms(1000)
            continue  # Skip to next iteration
        else:
            feedback = "Invalid input format. Use 'A->B', 'A->B?', 'remove A', or 'rm A'."
            instructions_win.addstr(2, 0, feedback, curses.A_BOLD)
            instructions_win.refresh()
            curses.napms(1000)
            continue  # Skip to next iteration

    # Goodbye message
    instructions_win.clear()
    instructions_win.addstr(0, 0, "Goodbye!", curses.A_BOLD)
    instructions_win.refresh()
    curses.napms(1000)

# Wrapper for curses
def main():
    cipher_text = input("Enter the cipher text: ")  # Initial input outside curses
    curses.wrapper(lambda stdscr: cipher_assist(stdscr, cipher_text))

if __name__ == "__main__":
    main()
