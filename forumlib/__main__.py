import argparse
from pathlib import Path
from .regex_macro import find_apply_regex_macros
from .css_layout_tools import inline_external_css, apply_css_to_elements, remove_invisible_elements
from .html_to_bbcode import html_to_bbcode
from .html_to_markdown import html_to_discord_markdown

def main():
    parser = argparse.ArgumentParser(
                    prog='forumlib',
                    description='Process HTML files for use in FC forums')
    parser.add_argument('-i', '--in-file', type=Path, required=True, help='Input file path')
    parser.add_argument('-o', '--out-html-file', type=Path, default=None, help='Output file path for HTML')
    parser.add_argument('-b', '--out-bbcode-file', type=Path, default=None, help='Output file path for BBCode')
    parser.add_argument('-m', '--out-markdown-file', type=Path, default=None, help='Output file path for Markdown')
    parser.add_argument('-A', '--auto-output', action='store_true', help='Output all 3 with automatic names')
    parser.add_argument('-a', '--all-filters', action='store_true', help='Apply all filters (phases)')
    parser.add_argument('-r', '--regex-macro', action='store_true', help='Apply filter: regex macros')
    parser.add_argument('-l', '--link-css', action='store_true', help='Apply filter: link external CSS')
    parser.add_argument('-n', '--inline-css', action='store_true', help='Apply filter: inline CSS')
    parser.add_argument('-v', '--remove-invisible', action='store_true', help='Apply filter: remove invisible')
    args = parser.parse_args()
    
    in_file = args.in_file
    out_html_file = args.out_html_file
    out_bbcode_file = args.out_bbcode_file
    out_markdown_file = args.out_markdown_file
    if args.auto_output:
        out_html_file = out_html_file or in_file.with_suffix('.out.html')
        out_bbcode_file = out_bbcode_file or in_file.with_suffix('.out.bbcode.html')
        out_markdown_file = out_markdown_file or in_file.with_suffix('.out.md')
    
    with open(in_file) as file:
        raw = file.read()
    
    if args.all_filters or args.regex_macro:
        raw = find_apply_regex_macros(raw)
    
    if args.all_filters or args.link_css:
        raw = inline_external_css(raw, base_path=in_file.parent)
    
    if args.all_filters or args.inline_css:
        raw = apply_css_to_elements(raw)
    
    if args.all_filters or args.remove_invisible:
        raw = remove_invisible_elements(raw)
    
    if out_html_file:
        with open(out_html_file, 'w') as file:
            file.write(raw)
    
    if out_bbcode_file:
        bbcode = html_to_bbcode(raw)
        with open(out_bbcode_file, 'w') as file:
            file.write(bbcode)
    
    if out_markdown_file:
        markdown = html_to_discord_markdown(raw)
        with open(out_markdown_file, 'w') as file:
            file.write(markdown)

if __name__ == "__main__":
    main()
