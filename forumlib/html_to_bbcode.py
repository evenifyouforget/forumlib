from bs4 import BeautifulSoup
from bs4.element import Comment
from typing import Union
import argparse

def html_to_bbcode(input_data: Union[str, BeautifulSoup]) -> str:
    """
    Converts HTML to BBCode by replacing angle brackets with square brackets.
    Strips outer <!DOCTYPE>, <html>, removes HTML comments, and processes only the contents of <body> if present.
    
    Args:
        input_data (str or BeautifulSoup): The HTML string or BeautifulSoup object to convert.
    
    Returns:
        str: The converted BBCode string.
    """
    # Check if input_data is a BeautifulSoup object; if not, parse it
    if isinstance(input_data, BeautifulSoup):
        soup = input_data
    else:
        soup = BeautifulSoup(input_data, 'html.parser')

    # Remove <!DOCTYPE> if present
    if soup.contents and soup.contents[0].name is None and soup.contents[0].string.startswith("DOCTYPE"):
        soup.contents.pop(0)

    # Remove <html> tag if present
    if soup.html:
        soup = soup.html.extract()

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Process only the contents of <body> if present
    if soup.body:
        soup = soup.body.extract()

    # Convert all tags by replacing angle brackets with square brackets
    bbcode = str(soup).replace('<', '[').replace('>', ']').replace("\n", "").strip()

    return bbcode

def main(input_file: str, output_file: str) -> None:
    """
    Reads HTML content from an input file, converts it to BBCode, and writes it to an output file.
    
    Args:
        input_file (str): Path to the input file containing HTML content.
        output_file (str): Path to the output file to write the BBCode content.
    """
    try:
        # Read HTML content from the input file
        with open(input_file, 'r', encoding='utf-8') as infile:
            html_content = infile.read()

        # Convert HTML to BBCode
        bbcode_content = html_to_bbcode(html_content)

        # Write BBCode content to the output file
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(bbcode_content)

        print(f"Conversion complete. BBCode written to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Use argparse for command-line argument parsing
    parser = argparse.ArgumentParser(description="Convert HTML to BBCode.")
    parser.add_argument("input_file", type=str, help="Path to the input file containing HTML content.")
    parser.add_argument("output_file", type=str, help="Path to the output file to write the BBCode content.")
    
    args = parser.parse_args()
    main(args.input_file, args.output_file)