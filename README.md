Python script to process a text file exported from a Typepad blog into a WordPress blog.

The script is intended to redirect all references to other blog posts (in the original blog) to blog posts in the soon-to-be re-constituted blog on Wordpress, as well as to fix problems due to early Typepad formatting conventions in creating URLs such as limiting title strings to 15 characters and using underscores instead of hyphens in the conversion of title strings to URLs.

The script takes 4 arguments:
* an `input_file` (the exported Typepad file)
* an `output_file` (the file to import into Wordpress)
* an `original_base_url` (default: 'gumption.typepad.com')
* a `new_base_url` (default: 'interrelativity.com')
* a `basename_mappings_file` (default: 'basename_mappings.csv')
* a `url_replacements_file` (default: 'url_replacements.csv')

The script 
* collects all **TITLE** and _original_ **BASENAME** strings from _input_file_
* creates _new_ **BASENAME** strings by converting the title string to lowercase, removing punctutation except for hyphens, and substituting hyphens for all whitespace, saving this in a `basename_mappings` dictioonary
* substitutes URLs using the new **BASENAME** and output domain for all occurrences of URLS using the old **BASENAME** with the input domain im the input file, except for the lines in the input file that start with '**UNIQUE URL:**' (which is used by the Wordpress imnporter plugin to access the old URLls), saving these in a `url_replacements` dictionary
* saves `basename_mappings` in `basename_mappings_file`
* saves `url_replacements` in `url_replacements_file`

The function expects that each Typepad blog post reference uses the pattern `http(s)?://original_base_url/yyyy/mm/title.html` anE each Wordpress blog post will use the pattern `https://new_base_url/yyyy/mm/title` (no `'.html'`)

This worked for me, using defaults above, but no warranty is provided that it will work for others.
