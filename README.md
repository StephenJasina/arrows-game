# Arrows Game

A game inspired by [Pathery](https://www.pathery.com) and [Trainyard Express](https://play.google.com/store/apps/details?id=com.noodlecake.trainyardexpress).

## Prerequisites
`python3` should be installed on your system. The app is currently tested on 3.9.5, but any version should work. For the best effect, use a terminal with color support.

## Execution
Use `python arrows-cli.py`. The keybinds are as follows:
* In edit mode (when the magenta asterisk is visible):
  * Use `w`, `a`, `s`, and `d` to move the cursor (denoted by a magenta asterisk)
  * Use `o`, `k`, `l`, and `;` to place down arrows. Alternatively, use the arrow keys
  * Use `r` to reset all placed arrows
  * Use `g` to enter run mode
  * Use `q` to exit the program
* In run mode (when the magenta asterisk is not visible):
  * Use `q` to stop the execution early and return to edit mode
  * Use `p` to pause the execution. Resume with any key

## Rules
A cyan diamond tries to get from the start (a green rectangle) to the goal (a checkerboard). To do this, it follows a series of red arrows, one at a time. The objective is to make the diamond's path as long as possible (but still finite).

The player is allowed to place the arrows, at most one per edge. To spice it up, cells are allowed to have *two* outgoing arrows, one of which will be initially red. Each time the diamond exits a cell with two arrows, which arrow is red gets toggled (think of it like a train junction switching).
