# pr_and_elo

This is a Power Ranking (PR) and ELO rating system that is compatible with any game, but has been designed with the intent to be used to maintain the PR in the King K. Rool Smash Discord.

## Functionality

<ul>
  <li>Connects to a Google Sheets spreadsheet and a MySQL DB as a backup optionally</li>
  
  <li>Automatically recalculates PR and ELO for a group of players</li>
  
  <li>Keeps track of matches and sets within those matches</li>
</ul>

## Prerequisites

<ul>
  <li>Python version 3.6 or higher</li>
  <li>(optional) MySQL</li>
  <li>A blank .env file</li>
  <li>A Google Sheets set up similarly to https://docs.google.com/spreadsheets/d/1mOQm0ziJRMZ-JQPBnQmcFp6xHdyJphcGkUWqBiVeoAI/edit?usp=sharing, specifically in the ELO and Match History pages. Make sure to name those pages the correct name, otherwise this code won't work!</li>
</ul>

## Setup

<ol>
  <li>Go to the Google Sheets Quickstart (https://developers.google.com/sheets/api/quickstart/python) page and follow steps 1 and 2 ONLY. When the page prompts you to set up a project, choose a name, then pick "Desktop" for the type of application.</li>
  <li>(optional) Create a MySQL database (remember the name for step 4). You'll want to make a table elo, with columns username (primary key, string), elo (int), and pr (int). You'll also want to make a table match_history, with columns winner (string), loser (string), gw (int), and gl (int).
  <li>Create a folder on your computer where you would like to store this project. Download elo_and_pr.py or elo_and_pr_no_db.py (depending on if you want a SQL DB backup or not) (Or copy-paste it into a python file of your choosing), and move that, the credentials.json file you downloaded from step 2 of the Quickstart Guide, and your empty .env file into this folder. Alternatively, you can use thte IDE of your choice to set this up.</li>
  <li>In the .env file, you'll have to create some variables. As of now, you'll have to create five variables. An example variable looks like "HOST=localhost". You'll have to (optional) set up your MySQL database variables in this file (HOST, USERNAME_DB, PASSWORD, DB_NAME) and the spreadsheet id (SPREADSHEET_ID, found in the link to your Google Sheet between "/d" and "/edit".</li>
  <li>In Command Prompt, navigate to the folder that you made and now you can finally run this code! To get started, run this command: python elo_and_pr.py -h</li>
  <li>Congratulations! You now have a program that automatically calculates the ELO and PR for a group of people playing a certain game</li>
</ol>

## Extras

<ul>
  <li>If you dislike the ELO change from match to match, or you want to start your users at a different ELO, you can change these on line 17.</li>
  <li>If you want to change the title of a page on your spreadsheet or you want to change the layout, remember to changes lines 33 and 34, as well as the function find_elo starting on line 119</li>
  <li>Match history is saved across account resets or deletions so viewers can see why a user's ELO has changed despite the reset or deletion of another user's account</li>
</ul>



