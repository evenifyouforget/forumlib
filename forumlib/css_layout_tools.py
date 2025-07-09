import os
from bs4 import BeautifulSoup, Tag
import cssutils
import tinycss2 # For parsing CSS selectors and rules
from pathlib import Path # Import pathlib
import argparse # Import argparse
import logging

# Suppress cssutils warnings for common CSS issues
cssutils.log.setLevel(logging.CRITICAL)

def _get_css_rules(css_string):
    """Parses a CSS string and returns a list of CSS rules."""
    rules = []
    try:
        sheet = cssutils.parseString(css_string)
        for rule in sheet.cssRules:
            if rule.type == rule.STYLE_RULE:
                rules.append(rule)
    except Exception as e:
        print(f"Warning: Could not parse CSS string. Error: {e}")
    return rules

def _get_element_specificity(element, selector_tokens):
    """Calculates the specificity of a CSS selector for a given element."""
    # This is a simplified specificity calculation (a, b, c)
    # where a = #id, b = .class, c = tag/pseudo-element
    a, b, c = 0, 0, 0

    for token in selector_tokens:
        if token.type == 'id_selector':
            if element.has_attr('id') and element['id'] == token.value:
                a += 1
        elif token.type == 'class_selector':
            if element.has_attr('class') and token.value in element['class']:
                b += 1
        elif token.type == 'type_selector':
            if element.name == token.value:
                c += 1
        # Add more selector types as needed (attributes, pseudo-classes, etc.)
    return (a, b, c)

def _matches_selector(element, selector):
    """Checks if a BeautifulSoup element matches a CSS selector.
    This is a simplified implementation and does not cover all complex CSS selectors.
    """
    try:
        tokens = list(tinycss2.parse_component_value_list(selector))
    except Exception:
        return False # Malformed selector

    # Handle simple selectors for now (tag, class, id)
    # This needs to be expanded for more complex selectors
    match = True
    for token in tokens:
        if token.type == 'type_selector':
            if element.name != token.value:
                match = False
                break
        elif token.type == 'class_selector':
            if not element.has_attr('class') or token.value not in element['class']:
                match = False
                break
        elif token.type == 'id_selector':
            if not element.has_attr('id') or element['id'] != token.value:
                match = False
                break
        # If there are multiple tokens, this simple logic might fail for combined selectors
        # e.g., 'div.my-class' vs 'div .my-class'
        # For a full implementation, a proper CSS selector engine is needed.
    return match

def inline_external_css(html_content: str, base_path: str = None) -> str:
    """
    Inlines externally referenced CSS files into the HTML document.

    Args:
        html_content (str): The HTML content as a string.
        base_path (str, optional): The base directory for resolving local CSS file paths.
                                   Defaults to the current working directory if None.

    Returns:
        str: The HTML content with external CSS inlined.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Use pathlib for base_path
    if base_path is None:
        base_path_obj = Path.cwd()
    else:
        base_path_obj = Path(base_path)

    for link_tag in soup.find_all('link', rel='stylesheet'):
        href = link_tag.get('href')
        if href:
            css_file_path_obj = None
            href_path_obj = Path(href)

            if href_path_obj.is_absolute():
                css_file_path_obj = href_path_obj
            else:
                css_file_path_obj = base_path_obj / href_path_obj

            if css_file_path_obj.exists():
                try:
                    with open(css_file_path_obj, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    new_style_tag = soup.new_tag('style')
                    new_style_tag.string = css_content
                    link_tag.replace_with(new_style_tag)
                    print(f"Inlined external CSS from: {css_file_path_obj}")
                except Exception as e:
                    print(f"Warning: Could not read or inline CSS from {css_file_path_obj}. Error: {e}")
            else:
                print(f"Warning: External CSS file not found: {css_file_path_obj}")
        else:
            print("Warning: <link rel='stylesheet'> tag found without 'href' attribute.")

    return str(soup)

def apply_css_to_elements(html_content: str) -> str:
    """
    Applies CSS from <style> tags and inline 'style' attributes directly
    to the 'style' attributes of the corresponding HTML elements.
    Removes all <style> tags after processing.

    Args:
        html_content (str): The HTML content as a string.

    Returns:
        str: The HTML content with CSS applied to element 'style' attributes.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Collect all CSS rules from <style> tags
    all_css_rules = []
    for style_tag in soup.find_all('style'):
        css_content = style_tag.string
        if css_content:
            all_css_rules.extend(_get_css_rules(css_content))
        style_tag.extract() # Remove the style tag after processing

    # Process elements in the document
    for element in soup.find_all(True): # Iterate over all tags
        # Initialize current styles for the element
        current_styles = {}
        if element.has_attr('style'):
            try:
                # Parse existing inline styles
                inline_sheet = cssutils.parseStyle(element['style'])
                for prop in inline_sheet.getProperties():
                    current_styles[prop.name] = prop.value
            except Exception as e:
                print(f"Warning: Could not parse inline style for {element.name}. Error: {e}")

        # Apply rules from collected CSS, considering specificity
        # This is a simplified cascade. A full cascade engine is very complex.
        # We'll iterate through rules and apply them if they match,
        # overwriting properties based on specificity.
        applied_styles_for_element = {}

        # Sort rules by specificity (higher specificity comes later)
        # This requires parsing selectors to get specificity
        # For simplicity, we'll just apply them in order they appear,
        # and then handle inline styles last.
        # A more robust solution would involve a dedicated CSS selector matching library
        # and a proper cascade algorithm.

        for rule in all_css_rules:
            selector = rule.selectorText
            # Using tinycss2 to parse selectors for better matching
            try:
                parsed_selector = list(tinycss2.parse_component_value_list(selector))
            except Exception:
                continue # Skip malformed selectors

            # Simplified selector matching:
            # Check if the element matches the selector
            # This is a very basic check and needs significant improvement for real-world CSS
            if _matches_selector(element, selector):
                # Get specificity for the current rule
                rule_specificity = _get_element_specificity(element, parsed_selector)

                for prop in rule.style.getProperties():
                    prop_name = prop.name
                    prop_value = prop.value
                    is_important = False # prop.important

                    # Check if this property has already been applied with higher specificity
                    # Or if it's already marked as important and this one isn't
                    if prop_name in applied_styles_for_element:
                        existing_value, existing_specificity, existing_important = applied_styles_for_element[prop_name]
                        if is_important and not existing_important:
                            applied_styles_for_element[prop_name] = (prop_value, rule_specificity, is_important)
                        elif not is_important and existing_important:
                            pass # Keep the existing important style
                        elif rule_specificity >= existing_specificity: # Apply if current rule is more specific or equally specific (last one wins)
                            applied_styles_for_element[prop_name] = (prop_value, rule_specificity, is_important)
                    else:
                        applied_styles_for_element[prop_name] = (prop_value, rule_specificity, is_important)

        # Merge applied styles into current_styles (inline styles have highest precedence)
        for prop_name, (prop_value, _, _) in applied_styles_for_element.items():
            if prop_name not in current_styles: # Don't overwrite existing inline styles
                current_styles[prop_name] = prop_value

        # Update the element's style attribute
        if current_styles:
            style_string = "; ".join([f"{k}: {v}" for k, v in current_styles.items()])
            element['style'] = style_string

    return str(soup)

def remove_invisible_elements(html_content: str) -> str:
    """
    Removes elements that can be statically determined to be not visible
    and can be safely removed without affecting the layout.
    This includes elements with 'display: none' or 'visibility: hidden' styles,
    and potentially empty elements without intrinsic size.

    Args:
        html_content (str): The HTML content as a string.

    Returns:
        str: The HTML content with invisible elements removed.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Elements that typically have intrinsic size even if empty
    INTRINSIC_SIZE_TAGS = ['img', 'input', 'br', 'hr', 'video', 'audio', 'canvas', 'iframe', 'object', 'embed']

    # Iterate in reverse order to safely remove elements without affecting iteration
    for element in soup.find_all(True, recursive=True):
        if not isinstance(element, Tag):
            continue

        # Check for explicit display: none or visibility: hidden
        style_attr = element.get('style', '')
        if 'display: none' in style_attr.lower() or 'visibility: hidden' in style_attr.lower():
            element.extract()
            print(f"Removed element (explicitly hidden): <{element.name}>")
            continue

        # Check for empty elements that don't have intrinsic size
        # An element is considered empty if it has no children (text or tags)
        # and is not a tag that inherently has size (like img, input)
        if not element.contents and element.name not in INTRINSIC_SIZE_TAGS:
            # Further check if it's an empty container that might affect layout
            # For simplicity, we'll remove truly empty non-intrinsic tags.
            # More complex layout effects (e.g., empty div with border) are not handled here.
            element.extract()
            print(f"Removed element (empty and no intrinsic size): <{element.name}>")
            continue

    return str(soup)

def main():
    parser = argparse.ArgumentParser(description="Process static HTML files by inlining CSS and removing invisible elements.")
    parser.add_argument("input_html_file", type=str, help="Path to the input HTML file.")
    parser.add_argument("output_html_file", type=str, help="Path to the output HTML file.")
    args = parser.parse_args()

    input_path = Path(args.input_html_file)
    output_path = Path(args.output_html_file)
    
    if not input_path.exists():
        print(f"Error: Input HTML file not found at {input_path}")
        exit(1)

    print(f"Processing HTML from: {input_path}")
    original_html = input_path.read_text(encoding='utf-8')

    # Step 1: Inline external CSS
    print("\n--- Inlining External CSS ---")
    # The base_path for inline_external_css should be the directory of the input HTML file
    inlined_html = inline_external_css(original_html, base_path=str(input_path.parent))
    print("External CSS inlined.")

    # Step 2: Apply CSS to elements
    print("\n--- Applying CSS to Elements ---")
    applied_html = apply_css_to_elements(inlined_html)
    print("CSS applied to elements.")

    # Step 3: Remove invisible elements
    print("\n--- Removing Invisible Elements ---")
    final_html = remove_invisible_elements(applied_html)
    print("Invisible elements removed.")

    # Write the final processed HTML to the output file
    output_path.write_text(final_html, encoding='utf-8')
    print(f"\nProcessed HTML saved to: {output_path}")

if __name__ == "__main__":
    main()
