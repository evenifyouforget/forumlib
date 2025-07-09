import os
from bs4 import BeautifulSoup, Tag
import cssutils
import tinycss2 # For parsing CSS selectors and rules
from pathlib import Path # Import pathlib
import argparse # Import argparse
from cssselect import Selector # Import Selector from cssselect
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

def _get_element_specificity(selector_text):
    """Calculates the specificity of a CSS selector string."""
    # Specificity (a, b, c)
    # a = number of ID selectors
    # b = number of class selectors, attributes selectors, and pseudo-classes
    # c = number of type selectors (element names) and pseudo-elements
    
    # Use tinycss2 to parse the selector for specificity calculation
    a, b, c = 0, 0, 0
    try:
        tokens = list(tinycss2.parse_component_value_list(selector_text))
        for token in tokens:
            if token.type == 'id_selector':
                a += 1
            elif token.type == 'class_selector' or \
                 token.type == 'attribute_selector' or \
                 (token.type == 'pseudo_class' and token.value not in ['first-line', 'first-letter', 'before', 'after']): # Exclude pseudo-elements
                b += 1
            elif token.type == 'type_selector' or \
                 token.type == 'pseudo_element': # Pseudo-elements count as c
                c += 1
    except Exception as e:
        # Fallback for complex selectors that tinycss2 might not fully tokenize for specificity
        print(f"Warning: Could not fully parse selector '{selector_text}' for specificity. Error: {e}")
        # Assign a basic specificity to ensure it's still processed
        if '#' in selector_text: a = 1
        elif '.' in selector_text or '[' in selector_text or ':' in selector_text: b = 1
        else: c = 1
    return (a, b, c)

def _compare_specificity(spec1, spec2):
    """Compares two specificity tuples. Returns True if spec1 is higher or equal, False otherwise."""
    for i in range(3):
        if spec1[i] > spec2[i]:
            return True
        if spec1[i] < spec2[i]:
            return False
    return True # Equal specificity

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
    soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser for cssselect compatibility
    
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
    soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser for cssselect compatibility

    # Collect all CSS rules from <style> tags and store with their specificity
    all_css_rules_with_specificity = []
    for style_tag in soup.find_all('style'):
        css_content = style_tag.string
        if css_content:
            for rule in _get_css_rules(css_content):
                selector_text = rule.selectorText
                # Skip rules with pseudo-classes like :hover as they cannot be statically applied
                if ':' in selector_text and not (':nth-child' in selector_text or ':nth-of-type' in selector_text): # Basic exclusion
                    # print(f"Skipping dynamic pseudo-class selector: {selector_text}")
                    continue
                try:
                    specificity = _get_element_specificity(selector_text)
                    all_css_rules_with_specificity.append((rule, specificity, selector_text))
                except Exception as e:
                    print(f"Warning: Could not parse selector '{selector_text}' for specificity. Error: {e}")
        style_tag.extract() # Remove the style tag after processing

    # Sort rules by specificity (lower specificity first, so higher specificity overwrites)
    # If specificity is equal, order in stylesheet (which is preserved by append before sort) matters.
    all_css_rules_with_specificity.sort(key=lambda x: x[1])

    # Process elements in the document
    for element in soup.find_all(True): # Iterate over all tags
        # Initialize final styles for the element
        # This will store (value, specificity, is_important) for each property
        final_styles_for_element = {}

        # 1. Apply existing inline styles (highest precedence, specificity (1,0,0), considered important)
        if element.has_attr('style'):
            try:
                inline_sheet = cssutils.parseStyle(element['style'])
                for prop in inline_sheet.getProperties():
                    # Inline styles are always paramount, assign (1,0,0) specificity and important=True
                    final_styles_for_element[prop.name] = (prop.value, (1,0,0), True) 
            except Exception as e:
                print(f"Warning: Could not parse initial inline style for {element.name}. Error: {e}")

        # 2. Apply rules from collected CSS, considering specificity and !important
        for rule, rule_specificity, selector_text in all_css_rules_with_specificity:
            try:
                # Use cssselect to find matching elements
                # select() returns a list of matching elements. If 'element' is in it, it matches.
                # This is far more robust than custom matching.
                if element in soup.select(selector_text):
                    for prop in rule.style.getProperties():
                        prop_name = prop.name
                        prop_value = prop.value
                        is_important = False # prop.important

                        existing_data = final_styles_for_element.get(prop_name)

                        if existing_data:
                            existing_value, existing_specificity, existing_important = existing_data
                            
                            # Rule: !important declarations override non-important ones
                            if is_important and not existing_important:
                                final_styles_for_element[prop_name] = (prop_value, rule_specificity, is_important)
                            elif not is_important and existing_important:
                                pass # Keep the existing important style
                            # If both are important or both are not important, compare specificity
                            elif _compare_specificity(rule_specificity, existing_specificity):
                                final_styles_for_element[prop_name] = (prop_value, rule_specificity, is_important)
                        else:
                            final_styles_for_element[prop_name] = (prop_value, rule_specificity, is_important)
            except Exception as e:
                # Catch specific cssselect errors if selector is not supported by cssselect
                print(f"Warning: Selector '{selector_text}' caused an error during matching: {e}")


        # 3. Handle inheritance (simplified for common properties)
        # Iterate over properties in final_styles_for_element
        # If a property is inheritable and not set on current element, check parent
        # This is a very basic form of inheritance. A full implementation is complex.
        INHERITABLE_PROPERTIES = ['color', 'font-family', 'font-size', 'font-weight', 'line-height', 'text-align', 'visibility']
        
        for prop_name in INHERITABLE_PROPERTIES:
            if prop_name not in final_styles_for_element: # If property not explicitly set on this element
                parent = element.find_parent()
                while parent:
                    parent_style_attr = parent.get('style')
                    if parent_style_attr:
                        try:
                            parent_inline_sheet = cssutils.parseStyle(parent_style_attr)
                            for p_prop in parent_inline_sheet.getProperties():
                                if p_prop.name == prop_name:
                                    # Inherit with very low specificity so it can be easily overridden
                                    final_styles_for_element[prop_name] = (p_prop.value, (0,0,0), False)
                                    break
                        except Exception:
                            pass # Ignore malformed parent styles
                    parent = parent.find_parent()


        # Update the element's style attribute
        if final_styles_for_element:
            style_string_parts = []
            for prop_name, (prop_value, _, is_important) in final_styles_for_element.items():
                # Ensure !important is added if necessary
                style_string_parts.append(f"{prop_name}: {prop_value}{' !important' if is_important else ''}")
            element['style'] = "; ".join(style_string_parts)
        else:
            # If no styles applied and it previously had a 'style' attribute, remove it
            if 'style' in element.attrs:
                del element['style']

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
    soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser

    # Elements that typically have intrinsic size even if empty
    INTRINSIC_SIZE_TAGS = ['img', 'input', 'br', 'hr', 'video', 'audio', 'canvas', 'iframe', 'object', 'embed']

    # Iterate in reverse order to safely remove elements without affecting iteration
    for element in soup.find_all(True, recursive=True):
        if not isinstance(element, Tag):
            continue

        # Check for explicit display: none or visibility: hidden
        style_attr = element.get('style', '')
        if 'display: none' in style_attr.lower():
            element.extract()
            print(f"Removed element (display: none): <{element.name}>")
            continue
        elif 'visibility: hidden' in style_attr.lower():
            element.extract()
            print(f"Removed element (visibility: hidden): <{element.name}>")
            continue

        # Check for empty elements that don't have intrinsic size
        # An element is considered empty if it has no children (text or tags)
        # and is not a tag that inherently has size (like img, input)
        # Also check for explicit width/height styles to avoid removing styled empty divs
        if not element.contents and element.name not in INTRINSIC_SIZE_TAGS:
            style_props = cssutils.parseStyle(style_attr)
            has_explicit_size = False
            for prop in style_props.getProperties():
                if prop.name in ['width', 'height', 'min-width', 'min-height']:
                    if prop.value.strip() not in ['auto', '0', '0px', '0em', '0%']: # Consider non-zero explicit sizes
                        has_explicit_size = True
                        break
            
            if not has_explicit_size:
                element.extract()
                print(f"Removed element (empty and no intrinsic/explicit size): <{element.name}>")
                continue

    return str(soup)

if __name__ == "__main__":
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
