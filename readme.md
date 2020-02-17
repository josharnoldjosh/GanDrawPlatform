# GanDraw
GanDraw is a collaborative drawing game that involves dialog between a Drawer and a Teller. 

## Installation

*Requires python3.*

### Mac & Linux

1. First open terminal & clone the repository
    `git clone https://github.com/josharnoldjosh/GanDrawPlatform`

2. Change directory to the cloned repository:
    `cd GanDrawPlatform/`

3. Install the requirements:
    `pip3 install -r requirements.txt`

### Windows

1. Download Anaconda: `https://www.anaconda.com/`

2. Create a new environment with `python3.6`

3. Download this repository as a `.zip`

4. Open a terminal with your new environment from the anaconda navigator

5. Type `cd GanDrawPlatform/`

6. Type `pip install -r requirements.txt`

7. Voila

# Instructions

The goal for anyone playing the game is to **collaboratively recreate a landscape image as accurately as possible.** Both the Drawer and the Teller can finish the game by communicating to each other that they've done the best they can to recreate the image, and by clicking the new game/finish game button.

## Teller
*The role of the teller is to describe the image.*

You initially give a brief description of the image. You then proceed to describe different parts of the image so that someone else can recreate the image solely from your instructions. Your goal is to help the other person, *the Drawer*, redraw the image as accurately as possible.

You can peek a set number of time(s) during the task at what the Drawer has drawn so far, to provide feedback for the Drawer to improve their image.

## Drawer
*The role of the drawer is to draw the best image they can at each turn.*

At each turn, the drawer first **draws the image to the best of his ability**, and then **downloads both the semantic map (the block colored image) and the generated, realistic image.** 

He nexts decides to either ask a question to get more information to draw a better image, ask for a potential clarification, or simply ask for another instruction.
