**QuizProg-GUI** is a graphical user interface version of [QuizProg](../../../quizprog) the console version.

## What's changed?
Here is the list of new features in QuizProg-GUI.
- A full graphical user interface with Tkinter
- Easier to use
- Compile executable file: Share your quiz to all your friends with just an executable!

Planned features:
- GUI-exclusive features: the new QPG format can contain images, videos and more that aren't possible in console QuizProg.

## Building
Use [PyInstaller](https://pypi.org/project/pyinstaller/) to build an executable.

### Adding an embeddable Python
The Compile executable file feature of QuizProg-GUI requires PyInstaller, which is impossible to bundle in a PyInstaller executable.
Therefore, QuizProg-GUI invokes PyInstaller via an embeddable (portable) Python installation.
Due to embeddable distributions only being available for Windows, compilation from a PyInstaller executable on non-Windows systems is not supported.

To create an embeddable Python for use with QuizProg-GUI:
1. Download a Windows embeddable ZIP file for your desired Python version (supported by QuizProg-GUI). Extract it to a directory of your choosing.
2. In the extracted directory, find the file `python3xx._pth` (`3xx` is your Python version, e.g. `39` for 3.9) and open it in a text editor. Uncomment `import site` by removing the `#` in front of it.
3. Download `get-pip.py` from https://bootstrap.pypa.io/get-pip.py. Run it with the embeddable Python. If the message `This script does not work on Python ...` appears, replace your existing `get-pip.py` with the URL that is printed to the console, then run the new version with the embeddable Python.
4. Install the requirements and PyInstaller using the pip you just installed in the previous step.
5. Bundle the entire contents of the embeddable Python directory into a ZIP file. (do not nest directories!)
6. Build QuizProg-GUI with your normal Python's PyInstaller, with this ZIP file added in the root. Name it `compiler_env.zip`.
