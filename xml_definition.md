# XML-Tags

## entry
### Description
Describes an entry in a mapping tag to post-process user input in field-tags.
Can hold content.
### Attributes
  - (optional) ignore = "True"
    - As long as an ignore-attribute is present, this entry will be omitted, no matter the content of the attribute.
### Parents
  - select

## field
### Description
Holds information for a user prompt and possibly a mapping to process the user input.
The name attribute of a field tag will be appended to namespace names in the script runtime.
### Attributes
  - (required) name
    - Name of this specific field
  - (required) type = "numbers" | "checks" | "text"
    - Describes how prompt-children of this field will read user input
      - numbers: Process input as list of numbers. Can be comma and/or space separated. If no comma or space was found in the input, the stirng of numbers is assumed to be a string of single-digit numbers.
      - checks: All "x" within the string will be evaluated to a "True" value, every other letter will be evaluated to "False"
      - text: Do not process user input
### Parents
  - form

## form
### Description
Holds different fields which usually will be processed by a textblock-tag.
results of textblock-tags will automatically be saved to a namespace with the
name-attribute of the form-tag.
Forms can be ignored by setting a comma-seperated list with a set-tag and a name attribute "ignore_forms".
### Attributes
  - name
    - Name to be added to the namespaces list 
### Parents
  - root

## gender
### Description
Is omitted if last user input does not match name-attribute. Used to set namespaces
for different genders
### Attributes
  - name
    - Is checked against las user input
### Parents
  - root