# Such an extremely specific application, who is this for?

Me.
But a more useful answer is, someone who wants to make beautiful professional-level posts in the FC community, presumably for high budget events.

The inputs are HTML extended with a few customizations, and the outputs are a BBCode file (FC forum flavour) and a Markdown file (Discord flavour).

The distinct components of the text processor are:

* A regex-based macro/replacement system
* Linking in (inserting contents of) external CSS files
* Inlining CSS styles onto elements
* Removing elements that cannot be seen
* Generating BBCode from the HTML
* Generating Markdown from the HTML

## Example usage

(on Windows)

```sh
py .\forumlib\regex_macro.py -i .\samples\regex_macro\in.txt -o .\samples\regex_macro\out.txt
py .\forumlib\css_layout_tools.py .\samples\css_tools\in.html .\samples\css_tools\out.html
py .\forumlib\css_layout_tools.py .\samples\css_tools\in_with_link.html .\samples\css_tools\out_with_link.html
py .\forumlib\html_to_bbcode.py .\samples\html_to_bbcode\in.html .\samples\html_to_bbcode\out.bbcode.html
py .\forumlib\html_to_markdown.py .\samples\html_to_markdown\in.html .\samples\html_to_markdown\out.md
```

## Support

100% of basic features are working.

I can't make guarantees if you're trying to be fancy:

* Markdown only supports a very limited subset of HTML, and definitely no styling
* The forum doesn't support many of the more fancy HTML tags, or blocks them, likewise with some styles
* The library itself will choke on the most complicated CSS usage

That said, the example is like 90% correct, in theory, not that the forum or Discord actually support all these elements and styles.

## AI code disclaimer

I figured this was another fine time to test the capabilities of AI coding assistants, so I did quite a bit of vibe coding.
In the end, the AI was a little disappointing, though it wasn't useless either.

Mostly AI:

* `css_layout_tools.py`
* `html_to_bbcode.py`
* `html_to_markdown.py`
* All of the HTML examples
