#Skip's Calendar Converter
Converts SUTD's calendar into a CSV file readable by Google Calendar.
Tested working on Python >= v3.90

Works completely on the local machine with only the python standard library.

#Usage
The script comes with a simple CLI interface to guide you through the process. 

Alternatively, after running the script, follow the steps below:

Run convert.py. A terminal window should open.

##Scraping SUTD's Schedule
1. Navigate to SUTD MyPortal on your browser.
2. Navigate to My Menu > My Record > My Weekly Schedule.
3. Check the 'List View' radio button.
4. Select and copy all text from page by using CTRL+A, CTRL+C (or equivalent).
5. Save this to a text file named 'cal.txt', using notepad or another text file editor. The file should be in the same directory/folder as the script.

Re-open the terminal window and press Enter. You can choose to rename each class in your calendar, or leave them as default.

After renaming, the script will generate a file "calendar.csv" in the same directory. You can close the terminal after this.

##Uploading to Google Calendar
1. Navigate to calendar.google.com in your browser.
2. On the sidebar, find "Other Calendars" and click the "+" symbol next to it
3. Click "Create new calendar"
4. Set the name to whatever you want"
5. Once done, find "Import & export" on the sidebar
6. Click "Select File from Computer"
7. Under the "Add to calendar" dropbox, select your newly created calendar
8. Find and upload the newly generated file "calendar.csv" in the same directory as this script.

Enjoy! If you run into any problems, please do raise an issue or fix it yourself :>