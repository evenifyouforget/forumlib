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
        tag.insert_before(f"**")
        tag.insert_after(f"**")
        tag.unwrap()

    # Replace <i> and <em> with *italic*
    for tag in soup.find_all(['i', 'em']):
        tag.insert_before(f"*")
        tag.insert_after(f"*")
        tag.unwrap()

    # Replace <u> with __underline__
    for tag in soup.find_all('u'):
        tag.insert_before(f"__")
        tag.insert_after(f"__")
        tag.unwrap()

    # Replace <s> with ~~strikethrough~~
    for tag in soup.find_all('s'):
        tag.insert_before(f"~~")
        tag.insert_after(f"~~")
        tag.unwrap()

    # Replace <code> with `inline code`
    for tag in soup.find_all('code'):
        tag.insert_before(f"`")
        tag.insert_after(f"`")
        tag.unwrap()

    # Replace <br> and <br/> with newlines
    for tag in soup.find_all('br'):
        tag.replace_with("\n")

    # Replace <a> with [text](url)
    for tag in soup.find_all('a'):
        href = tag.get('href', '')
        tag.replace_with(f"[{tag.get_text()}]({href})")
    # Insert newlines before and after <p> tags
    for tag in soup.find_all('p'):
        tag.insert_before("\n")
        tag.insert_after("\n")
        tag.unwrap()

    # Replace <ul> and <ol> with Markdown list syntax
    for tag in soup.find_all(['ul', 'ol']):
        list_items = []
        if tag.name == 'ul':
            for li in tag.find_all('li'):
                list_items.append(f"* {li.get_text()}")
        elif tag.name == 'ol':
            for index, li in enumerate(tag.find_all('li'), start=1):
                list_items.append(f"{index}. {li.get_text()}")
        tag.replace_with("\n".join(list_items))

    # Replace heading tags <h1> to <h6> with Markdown syntax
    for i in range(1, 7):
        for tag in soup.find_all(f'h{i}'):
            tag.replace_with(f"{'#' * i} {tag.get_text(strip=True)}\n")

    # Replace <table> with Markdown table syntax
    for table in soup.find_all('table'):
        rows = []
        for row in table.find_all('tr'):
            cells = [cell.get_text() for cell in row.find_all(['td', 'th'])]
            rows.append(f"| {' | '.join(cells)} |")
        # Add a separator row after the first row (assumed to be the header)
        if rows:
            num_columns = len(rows[0].split('|')) - 2  # Calculate the number of columns
            header_separator = "| " + " | ".join(["---"] * num_columns) + " |"
            rows.insert(1, header_separator)
        table.replace_with("\n".join(rows))

    # Convert the soup object to a string
    markdown = soup.get_text()

    # Preserve original spacing within text blocks
    markdown = re.sub(r'\n+', '\n', markdown).strip()

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