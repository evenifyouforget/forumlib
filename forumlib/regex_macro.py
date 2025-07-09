import re
import argparse

class MacroProcessor:
    def __init__(self):
        # Stores (compiled_regex_pattern, replacement_string) tuples
        # The replacement string will have $N converted to \N
        self.macros = []

    def process_text(self, input_text):
        """
        Processes the input text, applies C-like macros (all treated as regex),
        and returns the result as a string.
        """
        output_lines = []
        lines = input_text.splitlines(keepends=True) # Keep newlines for accurate output

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('#define'):
                self._handle_define(stripped_line)
            else:
                processed_line = self._apply_macros(line)
                output_lines.append(processed_line)
        return "".join(output_lines)

    def _handle_define(self, line):
        """
        Parses a #define line and stores the macro.
        Both the 'name' (pattern) and 'value' (replacement) are treated as regex.
        Expected format: #define <REGEX_PATTERN> <REPLACEMENT_STRING_WITH_GROUPS>
        """
        parts = line.split(maxsplit=2)
        if len(parts) == 3:
            pattern_str = parts[1]
            replacement_str = parts[2]

            try:
                # Compile the pattern immediately to catch errors early
                compiled_pattern = re.compile(pattern_str)
                # Standardize backreferences: $1 -> \1 for re.sub
                # \g<1> is preferred in Python, but \1 is also common and often works
                # We'll allow both $1 and \1 in the macro definition value.
                standardized_replacement = replacement_str.replace('$', '\\')
                self.macros.append((compiled_pattern, standardized_replacement))
            except re.error as e:
                print(f"Error: Invalid regex pattern '{pattern_str}' in '#define {line}'. Macro ignored. Error: {e}")
            except Exception as e:
                print(f"Unexpected error processing macro '{line}': {e}")
        else:
            print(f"Warning: Malformed #define line ignored: {line}")

    def _apply_macros(self, line):
        """
        Applies all currently defined macros (regex patterns) to the given line.
        """
        current_line = line
        # Apply macros in the order they were defined
        for pattern, replacement in self.macros:
            current_line = pattern.sub(replacement, current_line)
        return current_line

# --- Main execution with argparse ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process text file with C-like macros, all treated as regex.")
    parser.add_argument("input_filepath", help="Path to the input text file.")
    parser.add_argument("output_filepath", help="Path to the output text file.")

    args = parser.parse_args()

    # Create a dummy input file if it doesn't exist for demonstration
    try:
        with open(args.input_filepath, 'r') as f:
            pass # Just try to open to see if it exists
    except FileNotFoundError:
        print(f"Input file '{args.input_filepath}' not found. Creating a sample one.")
        input_content = """
#define \\bfoo\\b bar
#define \\bhello\\b world
This is foo and hello.
#define package<(.+?)> It --> \\1 <-- is now in a box!
Here is a package<software> and another package<library>.
#define (\\d{3})-(\\d{3})-(\\d{4}) Phone: (\\1) \\2-\\3
Call me at 123-456-7890.
My old number was 987-654-3210.
#define (.+?)_ID (\\1)_Identifier
User_ID and Product_ID.
#define \\bNUMBER\\b Count
#define Count TOTAL
NUMBER is high.
"""
        with open(args.input_filepath, "w") as f:
            f.write(input_content.strip())
        print(f"Sample content written to '{args.input_filepath}'.")

    # Read input from the specified file
    try:
        with open(args.input_filepath, 'r') as infile:
            input_text_content = infile.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_filepath}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        exit(1)

    processor = MacroProcessor()
    processed_text = processor.process_text(input_text_content)

    # Write output to the specified file
    try:
        with open(args.output_filepath, 'w') as outfile:
            outfile.write(processed_text)
        print(f"Processing complete. Result written to '{args.output_filepath}'.")

        # Display the content of the output file
        print(f"\n--- Content of {args.output_filepath} ---")
        print(processed_text)
        print("----------------------------")

    except Exception as e:
        print(f"Error writing output file: {e}")
        exit(1)