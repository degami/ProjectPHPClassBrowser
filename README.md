# Project PHP Class Browser

A Sublime Text 2 plugin which provides project's PHP classes browser.

Requirements:

  * Sublime Text 2
  * PHP cli, obviously

## Usage instructions:

You must have a Sublime Text project file saved in the root of the project.
To do this open your Project files (drag and drop the whole directory onto Sublime Text) and then save a new project by using the Project menu item.

Then enable the classes scan by adding a setting

  "scan_php_classes": true

in your project file.

After saving any file, a new file (containing the classes / method definition will be placed in the project root, named phpclass.sublime-classdb)

In the command palette you will find two new commands: "PHP Class browser: Open Browser" and "PHP Class browser: Close Browser" to open or close the class browser.
Double clicking on a function name or on a classname will open the source file on the definition line.

Suggestions on the autocomplete palette are also available ( note that it's up to you to write working or not code )
