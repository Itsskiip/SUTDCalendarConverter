import re
from datetime import date, time, timedelta

def parse_date(date_str) -> date:
    return date(*map(int, date_str.split('/')[::-1]))

def parse_time(time_str) -> time:
    '''Supports both 24H and 12H formats.
    Assuming there are no midnight classes, this conversion should work fine'''
    hours, minutes = time_str.split(':')
    hours = int(hours)
    if not minutes.isnumeric():
        if minutes[-2:] == 'PM' and hours != 12:
            hours += 12 
        minutes = minutes[:2]
    
    minutes = int(minutes)
    
    return time(hours, minutes)
            
def parse_data(pasted_str) -> list[dict]:
    '''Converts the raw copied text from SUTD portal's List View schedule page to a machine-understandable format.'''
    flags = re.DOTALL + re.MULTILINE

    #Regex for time and date formats respectively
    time_re = r'\d\d?:\d\d(?:[AP]M)?'
    date_re = r'\d\d\/\d\d\/\d{4}'

    #Regex for individual class entries
    type_data_re = \
        r'(?P<day>\w{2}) ' \
        fr'(?P<start_time>{time_re}) - (?P<end_time>{time_re})\s+' \
        r'(?P<loc>[^\n]+)\s+' \
        r'(?P<lecturers>^.*?)\s+' \
        fr'(?P<start_date>{date_re}) - (?P<end_date>{date_re})\W+'
    
    #Regex for course data types (e.g. CBL/Lecture)
    course_data_re = r'(?:\d{4})\s+(?:[A-Z]{2}\d\d)\s+(?P<type>[^\n]+)\s+(?P<type_data>(?:' + type_data_re + ')+)'

    #Top level Regex (e.g. Course code, name)
    courses_re = r'(?P<code>\d{2} .\d{3}\w*) - (?P<course>[^\n]+).+?(?P<course_data>(?:' + course_data_re + ')+)'
    
    weekday_map = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')

    course_matches = re.finditer(courses_re, pasted_str, flags)

    courses = []
    for course_match in course_matches:
        course = {'code': course_match['code'].replace(' ', ''), 
                'name': course_match['course'],
                'type': dict()}
        course_type_matches = re.finditer(course_data_re, course_match['course_data'], flags)
        
        if not course_type_matches:
            raise ValueError(f"Unable to parse {course['name']}.")
        
        for type_match in course_type_matches:
            class_matches = re.finditer(type_data_re, type_match['type_data'], flags)

            if not class_matches:
                raise ValueError(f"Unable to parse {course['name']} - {type_match['type']}.")

            class_matches = [m.groupdict() for m in class_matches]
            
            for d in class_matches:
                #Some classes may have multiple profs, this splits them into a list instead
                d['lecturers'] = [name.removesuffix(',') for name in d['lecturers'].splitlines()]
                
                #Convert start & end dates from DD/MM/YY to MM/DD/YY
                d['start_date'] = parse_date(d['start_date'])
                d['end_date'] = parse_date(d['end_date'])

                #Convert day of week to an integer
                d['day'] = weekday_map.index(d['day'])

                #Seperate the time number from AM/PM (e.g. 12:00AM -> 12:00 AM)
                d['start_time'] = parse_time(d['start_time'])
                d['end_time'] = parse_time(d['end_time'])

            course['type'][type_match['type']] = class_matches
        courses.append(course)

    if len(courses) == 0:
        raise ValueError(f"Unable to parse any courses.")
    
    return courses

if __name__ == '__main__':
    import csv
    import os

    print("Welcome to Skip's calendar creator.\nThis program will convert SUTD's calendar into a CSV file readable by Google Calendar.\n\n")
    print("To begin, carry out the following steps:")
    print("1. Navigate to SUTD MyPortal on your browser.")
    print("2. Navigate to My Menu > My Record > My Weekly Schedule.")
    print("3. Check the 'List View' radio button.")
    print("4. Select and copy all text from page by using CTRL+A, CTRL+C.")
    print("5. Save this to a text file named 'cal.txt', using notepad or another text file editor.")
    input("6. When ready, press Enter to continue.\n")

    run = True
    while run:
        try:
            print('Reading cal.txt...\n')
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
                     
            with open('cal.txt', 'r') as f:
                data = f.read()
            
            print('Parsing data...\n')
            courses = parse_data(data)

            output_ls = []

            print(f'{len(courses)} courses found.')
            for i, course in enumerate(courses):
                course['display_name'] = course['code'] + ' - ' + course['name']
                display_name = course['display_name']
                print(f'{i})\t {display_name}')

                confirmed = False
                while not confirmed:
                    name = input(f'\t\tEnter a custom name for this course, or press enter to accept the default: ')
                    if name:
                        confirmed = input(f'\t\tNew course name: "{name}", confirm? Y/n: ').lower() in ("y", "")
                        if confirmed: course['display_name'] = name
                    else:
                        confirmed = input(f'\t\tDefault course name: "{display_name}", confirm? Y/n: ').lower() in ("y", "")
                
                differentiate_types = False

                if len(course['type']) > 1:
                    ans = ' '
                    course_type = course['type']
                    while ans.lower() not in ('y', 'n', ''):
                        ans = input(f'\n\t\tMultiple types of classes "{", ".join(course_type)}" found for this course.\n'
                            '\t\tDo you want to differentiate between these types? Y/n\n'
                            '\t\t\tIf Y, the following events will be created:\n' + \
                            '\n'.join(['\t\t\t\t' + course['display_name'] + ' ' + ('Cohort' if s == 'CBL' else s) for s in course['type']]) + \
                            f'\n\t\t\tIf N, both classes will be named {display_name}: ')
                    differentiate_types = ans.lower() in ('y', '')

                for type, classes in course['type'].items():
                    for c in classes:
                        start_date: date = c['start_date']
                        start_date = start_date + timedelta((c['day'] - start_date.weekday()) % 7) #Offset the actual date in case it doesn't fall on the "Start Date"
                        end_date = c['end_date']

                        for offset in range((end_date - start_date).days // 7 + 1):
                            dte = start_date + offset * timedelta(7)
                            start_time = c['start_time']
                            end_time = c['end_time']
                            lecturers = c['lecturers']
                            loc = c['loc']
                            d = {
                                'Subject': course['display_name'],
                                'Start Date': f'{dte:%m/%d/%Y}'.upper(),
                                'Start Time': f'{start_time:%I:%M %p}',
                                'End Date': f'{dte:%m/%d/%Y}'.upper(),
                                'End Time': f'{end_time:%I:%M %p}',
                                'Description': ', '.join(lecturers),
                                'Location': loc
                            }

                            if differentiate_types:
                                d['Subject'] += ' Cohort' if type == 'CBL' else ' ' + type

                            output_ls.append(d)

            print('Generating calendar.csv...\n')

            with open('calendar.csv', 'w') as f:
                writer = csv.DictWriter(f, output_ls[0].keys(), dialect="unix")
                writer.writeheader()
                writer.writerows(output_ls)
            
            input('calendar.csv successfully generated!\n\n'
                  'Steps to be taken now:\n'
                  '\t1. Navigate to calendar.google.com\n'
                  '\t2. On the sidebar, find "Other Calendars" and click the "+" symbol next to it\n'
                  '\t3. Click "Create new calendar"\n'
                  '\t4. Set the name to whatever you want"\n'
                  '\t5. Once done, find "Import & export" on the sidebar\n'
                  '\t6. Click "Select File from Computer"\n'
                  '\t7. Under the "Add to calendar" dropbox, select your newly created calendar\n'
                  '\t8. Find and upload the newly generated file "calendar.csv" in the same directory as this script.\n')
            
            run = False
        except OSError:
            input("Error: Unable to find cal.txt. Please ensure the above steps have been completed before trying again.")
        except ValueError as e:
            input(e)