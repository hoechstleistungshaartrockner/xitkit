import re

# Matches checkbox format: [status_char]rest_of_line
CHECKBOX_PATTERN = re.compile(r'^\[(.)\](.*)$')

# Matches priority format after checkbox: space + priority_chars + space + description
# Groups: (priority_chars, description_with_spaces)
# Priority chars can be: dots + exclamation marks OR exclamation marks + dots (but not both sides)
PRIORITY_PATTERN = re.compile(r'^ ((?:[.]*[!]+|[!]+[.]*))( .*)$')

# Matches due date format: -> YYYY[-/][MM[-/]DD] or -> YYYY-W## or -> YYYY-Q#
# Supports various date formats as specified in the syntax guide
# Must be preceded by space, punctuation, or start of line (but not hyphen/slash to avoid conflicts)
DUE_DATE_PATTERN = re.compile(r'(?:^|(?<=[\s\(\)\[\]:;,.!?]))-> (\d{4}(?:[-/](?:W\d{2}|Q[1-4]|\d{1,2}(?:[-/]\d{1,2})?))?)(?=\s|[^\w/-]|$)')

# Matches tag format: #tag_name or #tag_name=value
# Supports Unicode characters for international tag names
# Groups: (tag_name, quoted_value_double, quoted_value_single, unquoted_value)
TAG_PATTERN = re.compile(r'#([a-zA-Z\u00C0-\u017F\u0400-\u04FF\u4e00-\u9fff\u10A0-\u10FF\w_-]+)(?:=(?:"([^"]*)"|\'([^\']*)\'|([a-zA-Z\u00C0-\u017F\u0400-\u04FF\u4e00-\u9fff\u10A0-\u10FF\w_-]*)))?')

# Matches continuation lines: exactly 4 spaces + content
CONTINUATION_PATTERN = re.compile(r'^    (.*)$')

# Matches section headers: lines do not start with a check box and contain at least one non-whitespace character
SECTION_HEADER_PATTERN = re.compile(r'^[^\[\s].*$')

# Matches blank lines (empty or whitespace only)
BLANK_LINE_PATTERN = re.compile(r'^\s*$')

# Status symbols for visual representation - using square bracket format
STATUS_SYMBOLS = {
    'OPEN': '[ ]',
    'DONE': '[x]',
    'ONGOING': '[@]',
    'OBSOLETE': '[~]',
    'INQUESTION': '[?]'
}

# Valid status values
VALID_STATUSES = {'OPEN', 'ONGOING', 'DONE', 'OBSOLETE', 'INQUESTION'}