from bs4 import BeautifulSoup
from typing import Union
import re
import argparse

def html_to_discord_markdown(input_data: Union[str, BeautifulSoup]) -> str:
    """
    Converts HTML to Discord-flavored Markdown.
    
    Args:
        input_data (str or BeautifulSoup): The HTML string or BeautifulSoup object to convert.
    
    Returns:
        str: The converted Markdown string.
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

    # Process only the contents of <body> if present
    if soup.body:
        soup = soup.body.extract()

    # Replace <b> and <strong> with **bold**
    for tag in soup.find_all(['b', 'strong']):
        tag.replace_with(f"**{tag.get_text()}**")

    # Replace <i> and <em> with *italic*
    for tag in soup.find_all(['i', 'em']):
        tag.replace_with(f"*{tag.get_text()}*")

    # Replace <u> with __underline__
    for tag in soup.find_all('u'):
        tag.replace_with(f"__{tag.get_text()}__")

    # Replace <s> with ~~strikethrough~~
    for tag in soup.find_all('s'):
        tag.replace_with(f"~~{tag.get_text()}~~")

    # Replace <code> with `inline code`
    for tag in soup.find_all('code'):
        tag.replace_with(f"`{tag.get_text()}`")

    # Replace <br> and <br/> with newlines
    for tag in soup.find_all('br'):
        tag.replace_with("\n")

    # Replace <a> with [text](url)
    for tag in soup.find_all('a'):
        href = tag.get('href', '')
        tag.replace_with(f"[{tag.get_text()}]({href})")

    # Convert the soup object to a string
    markdown = soup.get_text()

    # Remove extra whitespace
    markdown = re.sub(r'\s+', ' ', markdown).strip()

    return markdown

def main(input_file: str, output_file: str) -> None:
    """
    Reads HTML content from an input file, converts it to Discord-flavored Markdown, 
    and writes it to an output file.
    
    Args:
        input_file (str): Path to the input file containing HTML content.
        output_file (str): Path to the output file to write the Markdown content.
    """
    try:
        # Read HTML content from the input file
        with open(input_file, 'r', encoding='utf-8') as infile:
            html_content = infile.read()

        # Convert HTML to Discord-flavored Markdown
        markdown_content = html_to_discord_markdown(html_content)

        # Write Markdown content to the output file
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(markdown_content)

        print(f"Conversion complete. Markdown written to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Use argparse for command-line argument parsing
    parser = argparse.ArgumentParser(description="Convert HTML to Discord-flavored Markdown.")
    parser.add_argument("input_file", type=str, help="Path to the input file containing HTML content.")
    parser.add_argument("output_file", type=str, help="Path to the output file to write the Markdown content.")
    
    args = parser.parse_args()
    main(args.input_file, args.output_file)