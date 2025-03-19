import curses
from collections import Counter
import textwrap

def split_text_by_key_length(text, key_length):
    return [text[i:i + key_length] for i in range(0, len(text), key_length)]

def shift_letter(letter, shift_amount):
    if letter.isalpha():
        base = ord('A') if letter.isupper() else ord('a')
        return chr((ord(letter) - base + shift_amount) % 26 + base)
    return letter

def decrypt_with_key(text, key, char_offset):
    decrypted_text = []
    key_shifts = [(ord(k.upper()) - ord('A') + char_offset) if k.isalpha() else 0 for k in key]
    for index, letter in enumerate(text):
        shift_amount = -key_shifts[index % len(key)]
        decrypted_text.append(shift_letter(letter, shift_amount))
    return ''.join(decrypted_text)

def find_common_patterns(text, key_length):
    pattern_counts = {length: [Counter() for _ in range(key_length)] for length in range(2, key_length + 1)}
    for length in range(2, key_length + 1):
        for i in range(0, len(text), key_length):
            for j in range(key_length):
                chunk = text[i + j:i + j + length]
                if len(chunk) == length:
                    pattern_counts[length][j].update([chunk])
    common_patterns = []
    for length in sorted(pattern_counts.keys(), reverse=True):
        for position, counter in enumerate(pattern_counts[length]):
            filtered_patterns = [(pattern, count) for pattern, count in counter.items() if count > 1]
            if filtered_patterns:
                common_patterns.append((length, position, filtered_patterns[:3]))
    return common_patterns

def compute_key(word_a, word_b):
    if len(word_a) != len(word_b):
        return "Words must be the same length."
    key = []
    for a, b in zip(word_a.upper(), word_b.upper()):
        plain_num = ord(a) - ord('A') + 1
        cipher_num = ord(b) - ord('A') + 1
        shift = (cipher_num - plain_num) % 26
        if shift == 0:
            shift = 26
        key_letter = chr((shift - 1) + ord('A'))
        key.append(key_letter)
    return ''.join(key).lower()

def add_split_bars(decrypted_text, key_length):
    """Insert '|' at every key_length characters in the decrypted text for visual clarity."""
    result = []
    for i in range(0, len(decrypted_text), key_length):
        segment = decrypted_text[i:i + key_length]
        result.append(segment)
    return ' | '.join(result)

def curses_main(stdscr, text, key_length, char_offset):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)  # Color for separator bar

    key = ['_' for _ in range(key_length)]
    key_index = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        max_lines = height - 14

        stdscr.addstr(0, 0, "Ciphertext (truncated):", curses.color_pair(1) | curses.A_BOLD)
        for i, line in enumerate(split_text_by_key_length(text, key_length)[:max_lines]):
            stdscr.addstr(i + 1, 0, ''.join(line), curses.color_pair(1))

        decrypted_text = decrypt_with_key(text, ''.join(key), char_offset)
        stdscr.addstr(0, 30, "Decrypted Text (truncated):", curses.color_pair(2) | curses.A_BOLD)
        for i, line in enumerate(split_text_by_key_length(decrypted_text, key_length)[:max_lines]):
            stdscr.addstr(i + 1, 30, ''.join(line), curses.color_pair(2))

        # Add split bars to the full decrypted message
        stdscr.addstr(height - 10, 0, "Full Decrypted Message (with separators):", curses.color_pair(3) | curses.A_BOLD)
        wrapped_message = add_split_bars(decrypted_text, key_length)
        wrapped_lines = textwrap.wrap(wrapped_message, width - 1)
        for i, line in enumerate(wrapped_lines[:3]):
            stdscr.addstr(height - 9 + i, 0, line, curses.color_pair(3))

        stdscr.addstr(0, 60, "Common Patterns:", curses.color_pair(4) | curses.A_BOLD)
        common_patterns = find_common_patterns(text, key_length)
        line_offset = 1
        for length, position, patterns in common_patterns:
            if line_offset >= max_lines:
                break
            stdscr.addstr(line_offset, 60, f"{length}-letter patterns (position {position + 1}):", curses.color_pair(4))
            line_offset += 1
            for pattern, count in patterns:
                if line_offset >= max_lines:
                    break
                stdscr.addstr(line_offset, 60, f"  {pattern}: {count}", curses.color_pair(4))
                line_offset += 1

        stdscr.addstr(height - 4, 0, "Enter key shifts (letters for shifts, _ for no shift):")
        key_display = ''.join(
            [f"[{c}]" if i == key_index else f" {c} " for i, c in enumerate(key)]
        )
        stdscr.addstr(height - 3, 0, key_display, curses.color_pair(2) | curses.A_BOLD)

        stdscr.addstr(height - 6, 0, "Press Ctrl + C to quit, F1 to guess a key for two words")

        stdscr.refresh()

        ch = stdscr.getch()
        if ch == 17:  # Ctrl + Q
            break
        elif ch == curses.KEY_F1:
            curses.echo()
            stdscr.move(height - 2, 0)
            stdscr.clrtoeol()
            stdscr.addstr("Enter guessed plaintext word: ", curses.color_pair(3))
            word_a = stdscr.getstr().decode('utf-8')

            stdscr.move(height - 1, 0)
            stdscr.clrtoeol()
            stdscr.addstr("Enter encrypted word: ", curses.color_pair(3))
            word_b = stdscr.getstr().decode('utf-8')
            curses.noecho()
            
            if len(word_a) == len(word_b):
                suggested_key = compute_key(word_a, word_b)
                stdscr.move(height - 2, 0)
                stdscr.clrtoeol()
                stdscr.addstr(f"Suggested key to transform '{word_a}' to '{word_b}': {suggested_key}", curses.color_pair(3))
            else:
                stdscr.move(height - 2, 0)
                stdscr.clrtoeol()
                stdscr.addstr("Words must be the same length. Try again.", curses.color_pair(3))

            stdscr.refresh()
            stdscr.getch()
        elif ch == curses.KEY_RIGHT:
            key_index = (key_index + 1) % key_length
        elif ch == curses.KEY_LEFT:
            key_index = (key_index - 1) % key_length
        elif ch == curses.KEY_BACKSPACE or ch == 127:
            key[key_index] = '_'
            key_index = (key_index - 1) % key_length
        elif 0 <= ch - ord('a') < 26 or 0 <= ch - ord('A') < 26:
            key[key_index] = chr(ch).lower()
            key_index = (key_index + 1) % key_length
        elif ch == ord('_'):
            key[key_index] = '_'
            key_index = (key_index + 1) % key_length

def main():
    text = input("Enter the ciphertext: ")
    key_length = int(input("Enter the key length: "))
    char_offset = int(input("Enter offset (0 for A+A = A, or 1 for A+A = B): "))
    curses.wrapper(curses_main, text, key_length, char_offset)

if __name__ == '__main__':
    main()