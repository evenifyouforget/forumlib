# Such an extremely specific application, who is this for?

Me.
But a more useful answer is, someone who wants to make beautiful professional-level posts in the FC community, presumably for high budget events.

The inputs are HTML extended with a few customizations, and the outputs are a BBCode file (FC forum flavour) and a Markdown file (Discord flavour).

The distinct components of the text processor are:

* A regex-based macro/replacement system
* Inlining external CSS files
* Inlining CSS styles onto elements
* Removing elements that cannot be seen
* Generating BBCode from the HTML
* Generating Markdown from the HTML

## Example usage

(on Windows)

```sh
py .\forumlib\css_layout_tools.py .\samples\css_tools\in.html .\samples\css_tools\out.html
py .\forumlib\css_layout_tools.py .\samples\css_tools\in_with_link.html .\samples\css_tools\out_with_link.html
```

## AI code disclaimer

I figured this was another fine time to test the capabilities of AI coding assistants, so I did quite a bit of vibe coding.
