# Project PHP Class Browser

A Sublime Text 2/3 plugin which provides project's PHP classes browser.

Requirements:

  * Sublime Text
  * PHP cli, obviously (php executable must be in your $PATH environment variable)

## Installation instructions:

Install with package manager or clone the repository in your packages folder

## Usage instructions:

If you are on ST2 You **must** have a Sublime Text project file saved in the root of the project.
To do this open your Project files (drag and drop the whole directory onto Sublime Text) and then save a new project by using the Project menu item.
This because the ST2 api does not let fetching data from project as ST3 api does.
For ST3 users, project_data() is used, and the file will be saved in the first folder of your project

Then enable the classes scan by adding a setting

  "scan_php_classes": true

in your project file.

After saving any file, a new file (containing the classes / method definition will be placed in the project root, named phpclass.sublime-classdb)

In the command palette you will find two new commands: "PHP Class browser: Open Browser" and "PHP Class browser: Close Browser" to open or close the class browser.
Double clicking on a function name or on a classname will open the source file on the definition line.

Suggestions on the autocomplete palette are also available ( note that it's up to you to write working or not code )

In the settings file ( under Package Settings > Project PHP ClassBrowser ) you will find preferences for:

  * "php_executable": "php" // php executable
  * "class_order": "alpha" // default class browser order: can be one of "alpha" or "definition"
  * "enable_completitions": true // enable completitions
  * "two_panels": false //use two panels

If you have many classes / functions and the loading is slow try to use the two_panels mode,
as data is loaded when needed, or try to disable completitions
