# @file: views.py
# @brief: backend actions used to render the pages

# start import
from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from wasabicalendar.models import Description, Tag, Task, Calendar, Block
from wasabicalendar.forms import TaskForm

import datetime
import random

import json
# finish import

# define macros
DAY_COUNT = 96
WEEK_COUNT = 7

# @brief: json error response function from AJAX example in class
# @message: an error message string that will be displayed in the html
def _my_json_error_response(message, status=200):
    response_json = '{ "error": "' + message + '" }'
    return HttpResponse(response_json, content_type='application/json', 
                        status=status)

# @brief: share the calendar with a new member
# @type id: string
# @param id: id of the calendar to which the member is invited
# @return: redirect to calendar page with the calendar id if there is no error.
@login_required
def add_member(request, id):
    if request.method != 'POST':
        request.session["message"] = ("You must use a POST request " + 
                                     "for this operation.")
        return redirect('get_calendar', id=id)
    try:
        cal = Calendar.objects.get(id=id)
    except:
        # if there is no calendar object with id
        # display "No access to the calendar" to prevent 
        # disclosing database information
        message = 'No access to the calendar'
        request.session["message"] = message
        return redirect('home')
    if 'text' not in request.POST or not request.POST["text"]:
        message = 'No username input'
        request.session["message"] = message
        return redirect('get_calendar', id=id)
    if request.user != cal.owner:
        message = "Only the owner of this calendar can invite members."
        request.session["message"] = message
        return redirect('get_calendar', id=id)
    try:
        user_to_add = User.objects.get(username=(request.POST['text']))
        if user_to_add != request.user:
            cal.members.add(user_to_add)
            cal.save()
        # if the invited user is the user themself, display the message without 
        # adding them to the member of calendar (just like what google 
        # calendar does)
        message ="invited " + request.POST['text'] + " successfully"
    except:
        # handle situation where username doesn't exist
        message ='Invalid username input'
    request.session['message'] = message
    return redirect('get_calendar', id=id)

# @brief: add a new tag for catogorize tasks with a random generated color
# @type id: int
# @param id: id of the calendar to which tag should be added
# @return: redirect to calendar page with the calendar id if there is no error.
@login_required
def add_tag(request, id):
    # error handling
    if request.method != 'POST':
        request.session["message"] = ("You must use a POST request for this" + 
                                     " operation.")
        return redirect('get_calendar', id=id)
    if not 'text' in request.POST or not request.POST['text']:
        request.session["message"] = "You must enter a tag to add."
        return redirect('get_calendar', id=id)
    if not request.POST['text'].isalnum():
        request.session["message"] = ("Tag should contain numbers and " + 
                                      "letters only.")
        return redirect('get_calendar', id=id)
    if len(request.POST['text']) > 30:
        request.session["message"] = "Tag should be less than 30 characters."
        return redirect('get_calendar', id=id)
    try:
        cal = Calendar.objects.get(id=id)
    except:
        # handle the case that calendar object with the id doesn't exist
        message ='No access to the calendar'
        request.session["message"] = message
        return redirect('home')

    # randomly generated a light color so the task topic in black font would 
    # be visible
    color = "#"+''.join([random.choice('ABCDEF') for i in range(6)])
    new_tag = Tag(name=request.POST["text"], calendar=cal, color=color)
    new_tag.save()
    cal.tags.add(new_tag)
    cal.save()
    return redirect('get_calendar', id=id)

# @brief: get all the dates in the current week given the date of a Monday
# @type week: string
# @param week: Monday date
# @returns: a list of strings representing the dates in this week
def get_current_week(week):
    # check whether week is in correct format and whether start with Monday
    try:
        beginDate = datetime.datetime.strptime(week,"%Y-%m-%d")
    except:
        return _my_json_error_response("invalid week info", status = 400)
    if beginDate.weekday() != 0:
        return _my_json_error_response("invalid week info", status = 400)
    res = [week]
    for i in range(1, WEEK_COUNT):
        endDate = beginDate + datetime.timedelta(days=i)
        res.append(endDate.strftime("%Y-%m-%d"))
    return res

# @brief: get all the tasks & tag information in a given calendar and a given 
# week, pass tasks, tags, and week information in a json file for JavaScript
# @type id: int
# @param id: calendar.id of the calendar whose task and tag info we want to get
# @type week: string
# @param week: week in YY-mm-dd format of the week we want to access
# @rtype: HttpResponse object
# @returns: a list of strings representing the header columns
def _get_cal_list_helper(request, id, week):
    try:
        cal = Calendar.objects.get(id=id)
    except:
        # handle the case that calendar object with the id doesn't exist
        message ='No access to the calendar'
        request.session["message"] = message
        return redirect('home')

    days = get_current_week(week)
    data = [[], [], [], [], [], [], []]
    # initailize all block = (0, false) tasks = 5 * []
    for i in range(WEEK_COUNT):
        for j in range(DAY_COUNT):
            data[i].append({"block":(0, False), "tasks":[[],[],[],[],[]]})
    # put block data
    for block_item in cal.blocks.all():
        if block_item.date in days:
            day_i = days.index(block_item.date)
            users_in_block = block_item.select_user.all()
            curr_user_in_block = False
            if request.user in users_in_block:
                curr_user_in_block = True
            data[day_i][block_item.slot]["block"] = (len(users_in_block), 
                                                    curr_user_in_block)
    # put task items in task_data in the order of start time
    for task_item in cal.tasks.order_by('startTime'):
        tDate = task_item.taskDate
        parsedDate = tDate.strftime("%Y-%m-%d")
        # if task in current week
        if parsedDate in days:
            day_i = days.index(parsedDate)
            start = task_item.startTime
            end = task_item.endTime
            parsedStart = start.strftime("%H:%M:%S")
            startList = parsedStart.split(":")
            parsedEnd = end.strftime("%H:%M:%S")
            endList = parsedEnd.split(":")
            startBlock = int(startList[0]) * 4 + int(startList[1]) // 15
            endBlock = int(endList[0]) * 4 + int(endList[1]) // 15
            color = task_item.tag.color
            # create task info dict
            taskDict = {
                "id": task_item.id,
                "topic": task_item.topic,
                "startTime": parsedStart,
                "endTime": parsedEnd,
                "startBlock": startBlock,
                "endBlock": endBlock,
                "color":color
            }
            avIdx = 0 # available index
            while (avIdx < 4):
                if data[day_i][startBlock]['tasks'][avIdx] == []:
                    break # correct avIdx
                avIdx += 1
            for j in range(startBlock, endBlock):
                curTasks = data[day_i][j]['tasks'] # list of 5 lists
                curTasks[avIdx] = [taskDict]
    # pass tag data to json file
    tag_data = []
    for t in cal.tags.all():
        tag_item = {"name": t.name,
                    "color": t.color}
        tag_data.append(tag_item)
    
    res = {'data':data, 'week':days, 'tags':tag_data}
    response_json = json.dumps(res)
    return HttpResponse(response_json, content_type='application/json')
    
#
# @brief: the action that renders back to the home page
# @returns: render to the home page html with message if in request.session
#
@login_required
def profile_action(request):
    if 'message' in request.session:
        # display the message and delete it in request.session
        message = request.session['message']
        context = {"message": message}
        del request.session['message']
    else:
        context = {}
    return render(request, 'wasabicalendar/home.html', context)

#
# @brief: create a new calendar with a default tag name in the home page
#         and render to the calendar page of the newly created calendar
# @return: redirect to the get_calendar function with the created calendar
#          id 
@login_required
def create_calendar(request):
    # json error checkes to make sure that the input calendar name does not 
    # include special characters
    if request.method != 'POST':
        request.session["message"] = ("You must use a POST request for " + 
                                    "this operation.")
        return redirect('home')
    if not 'text' in request.POST or not request.POST['text']:
        request.session["message"] = "You must enter a name for the calendar."
        return redirect('home')
    if not request.POST['text'].isalnum():
        request.session["message"] = ("Calendar name should contain numbers" + 
                                    " and letters only.")
        return redirect('home')
    if len(request.POST['text']) > 30:
        request.session["message"] = ("Calendar name should be less" + 
                                    " than 10 characters.")
        return redirect('home')

    # create new calendar with a default tag
    cal = Calendar()
    cal.owner = request.user
    cal.name = request.POST['text']
    cal.save()
    tag = Tag()
    tag.name = request.POST['text']
    tag.calendar = cal
    tag.save()
    return redirect('get_calendar', id=cal.id)


# @brief: get the calendar model with the input cal id and get the current date
#         time to put into the context. If the user is not the owner of the user
#         and is not invited to the calendar, the error message would appear and
#         the user will be redirected to home
# @type id: int
# @return: render to the calendar page of the given calendar id
def get_calendar(request, id):
    try:
        cal = Calendar.objects.get(id=id)
    except:
        # handle the case where calendar object with the id doesn't exist
        message ='No access to the calendar'
        request.session["message"] = message
        return redirect('home')
    today = datetime.date.today()
    # YY-mm-dd
    monday = today - datetime.timedelta(days=today.weekday())

    d = monday.strftime("%Y-%m-%d")

    context = {"id": id, "week_info": d, "calendar": cal}

    # if the user does not get access to the calendar, will redirect to home
    if request.user not in cal.members.all() and request.user != cal.owner:
        request.session['message'] = "No access to the calendar"
        return redirect('home')

    if 'message' in request.session:
        message = request.session['message']
        del request.session['message']
        context["message"] = message
    return render(request, 'wasabicalendar/cal_page.html', context)

# @brief: function called after clicking on "create task" button
# @param id: the id of the calendar that will be used to create task in
# @type id: int
# @returns: render the create task page, or redirect to home or calpage if 
# there is an error
@login_required
def new_task(request, id):
    if request.method == 'GET':
        try:
            calendar = Calendar.objects.get(id=id)
        except:
            # handle the case where calendar object with the id doesn't exist
            message ='No access to the calendar'
            request.session["message"] = message
            return redirect('home')
        if (request.user not in calendar.members.all() and 
           request.user != calendar.owner):
            # if the user doesn't have access to the calendar contains the task
            request.session['message'] = "No access to the calendar"
            return redirect('home')
        # create a task form with the given calendar to initialize tag choices
        form = TaskForm(calendar=calendar)
        context = {'form': form, 'calendar': calendar}
        # display message in request.session
        if 'message' in request.session:
            message = request.session['message']
            context['message'] = message
            del request.session['message']
        return render(request, 'wasabicalendar/createtask.html', context)
    else:
        # if doesn't access this page using a get request, redirect to the 
        # calendar page and display an error message
        request.session['message'] = "Please access this page with a GET request"
        return redirect('get_calendar', id=id)

# @brief: function called after clicking on "modify task" button
# @param id: the id of the task that will be modified
# @type id: int
# @returns: render the modify task page, or redirect to home if there is an error
@login_required
def modify_task(request, id):
    try:
        task = Task.objects.get(id=id)
    except:
        # handle the case where task object with the id doesn't exist       
        message ='No access to the task'
        request.session["message"] = message
        return redirect('home')

    calendar = task.calendar

    if request.method != 'GET':
        # if the page is not accessed with a get request
        request.session['message'] = "Please access this page with a GET request"
        return redirect('home')
    if (request.user not in calendar.members.all() and 
        request.user != calendar.owner):
        # if the user doesn't have access to the calendar contains the task
        request.session["message"] = "No access to the task"
        return redirect('home')
    # prefill the form
    form = TaskForm({ 'topic': task.topic,
                        'tag': task.tag.id,
                        'description': task.description.text, 
                        'location': task.description.location, 
                        'link': task.description.link, 
                        'taskDate': task.taskDate, 
                        'startTime': task.startTime, 
                        'endTime': task.endTime}, calendar=calendar)

    # store update time in an hidden field for time stamp
    context = {"form": form, "task": task, "update_time": str(task.update_time)}
    
    # display message in request.session
    if 'message' in request.session:
        message = request.session['message']
        context['message'] = message
        del request.session['message']
    return render(request, 'wasabicalendar/modifytask.html', context)


# @brief: function called after submitting form in create calendar page
# @param id: the id of the calendar that will be used to create task
# @type id: int
# @returns: render back to calendar page or display error message in the 
#           create calendar page
@login_required
def create_task(request, id):
    try:
        calendar = Calendar.objects.get(id=id)
    except:
        # handle the case where calendar object with the id doesn't exist
        request.session['message'] ='No access to the calendar'
        return redirect('home')

    if request.method != 'POST':
        # cannot create a task with a get request
        request.session['message'] = "Please access this page with a POST request"
        return redirect('get_calendar', id=id)

    if (request.user not in calendar.members.all() and 
        request.user != calendar.owner):
        # if the user doesn't have access to the calendar contains the task
        request.session['message'] = "No access to the calendar"
        return redirect('home')

    form = TaskForm(request.POST, calendar=calendar)
    context = {"form": form, "calendar": calendar}
    if not form.is_valid():
        context["message"] = "Invalid Form"
        return render(request, 'wasabicalendar/createtask.html', context)
    
    # round minutes to multiple of 15
    startTime = form.cleaned_data['startTime']
    endTime = form.cleaned_data['endTime']
    roundedStartTime = datetime.time(startTime.hour,(startTime.minute//15)*15,0)
    
    if endTime.minute % 15 > 0:
        newMin = ((endTime.minute//15)+1)*15
        newHour = endTime.hour
        if newMin >= 60:
            newMin -= 60
            newHour += 1
    else:
        newMin = endTime.minute
        newHour = endTime.hour
    if newHour == 24:
        newHour = 23
        newMin = 45
    roundedEndTime = datetime.time(newHour,newMin,0)

    # case that task only occupied the last block
    if roundedStartTime == roundedEndTime:
        context["message"] = "Task cannot begin after 11:45PM"
        return render(request, 'wasabicalendar/modifytask.html', context)
    
    # count overlap, if any 15 minutes slot has > 5 tasks, create an error message 
    # and let user reenter the infotmation
    timeblock = dict()
    for t in calendar.tasks.all():
        if t.id != id:
            if t.taskDate == form.cleaned_data['taskDate']:
                # check overlap block:
                block = datetime.timedelta(minutes=15)
                st = datetime.datetime.combine(t.taskDate, roundedStartTime)
                et = datetime.datetime.combine(t.taskDate, roundedEndTime)
                while (st != et):
                    if t.startTime <= st.time() and t.endTime > st.time():
                        if st not in timeblock:
                            timeblock[st] = 1
                        else:
                            timeblock[st] += 1
                    st += block
    for key in timeblock:
        if timeblock[key] >= 5:
            context = {'createmessage': "You can only create up to 5 overlapped tasks.", 
                        "form": form, "calendar": calendar}
            return render(request, 'wasabicalendar/createtask.html', context)
    description = Description(text=form.cleaned_data["description"],
                              location = form.cleaned_data["location"],
                              link = form.cleaned_data["link"])
    
    try:
        tag = Tag.objects.get(id=form.cleaned_data['tag'])
    except:
        # handle the case where tag doesn't exist
        request.session['message'] = 'Invalid tag'
        return redirect('new_task', id=id)
    task = Task(topic=form.cleaned_data['topic'], 
                tag=tag,
                taskDate=form.cleaned_data['taskDate'],
                startTime=roundedStartTime,
                endTime=roundedEndTime,
                description=description)
    description.save()
    task.created_by = request.user
    task.calendar = calendar
    task.creation_time = timezone.now()
    task.updated_by = request.user
    task.update_time = timezone.now()
    task.save()
    request.session['message'] = 'Task Created'
    return redirect('get_calendar', id=id)

# @brief directly redirect back to calendar page
@login_required
def back(request, id):
    return redirect('get_calendar', id=id)


# @brief: function called after submitting form in modify calendar page
# @param id: the id of the task that will be modified
# @type id: int
# @returns: render back to calendar page or display error message in the 
#           modify calendar page
@login_required
@transaction.atomic
def modify_helper(request, id):
    try:
        task = Task.objects.select_for_update().get(id=id)
        db_update_time = task.update_time
    except:
        # handle the case when task object with the id doesn't exist
        message = 'Task does not exist'
        request.session["message"] = message
        return redirect('home')

    calendar = task.calendar

    if (request.user not in calendar.members.all() and 
        request.user != calendar.owner):
        # if user doesn't have access of the calendar the task is in
        request.session['message'] = "No access to the calendar"
        return redirect('home')

    if request.method != 'POST':
        # cannot modify a task with a get request
        request.session['message'] = "Please access this page with a GET request"
        return redirect('get_calendar', id=calendar.id)

    form = TaskForm(request.POST, calendar=calendar)

    # get update time stored in hidden field for time stamp
    hidden_update_time = request.POST['hidden_update_time_modify']

    # need to go back three directory to access the css file
    context = {"form": form, 'task': task, "useanothercss": True, 
            "update_time": hidden_update_time}
    if not form.is_valid():
        context["message"] = "Invalid Form"
        return render(request, 'wasabicalendar/modifytask.html', context)

    # check whether other users have update the task after opening the page
    if str(db_update_time) != str(hidden_update_time):
        request.session["message"] = ("Another user has modified this task." + 
                                    " Please re-enter.")
        return redirect('modify_task', id=task.id)

    # round minutes to multiple of 15
    startTime = form.cleaned_data['startTime']
    endTime = form.cleaned_data['endTime']
    roundedStartTime = datetime.time(startTime.hour,(startTime.minute//15)*15,0)
    
    if endTime.minute % 15 > 0:
        newMin = ((endTime.minute//15)+1)*15
        newHour = endTime.hour
        if newMin >= 60:
            newMin -= 60
            newHour += 1
    else:
        newMin = endTime.minute
        newHour = endTime.hour
    if newHour == 24:
        newHour = 23
        newMin = 45
    roundedEndTime = datetime.time(newHour,newMin,0)

    # case that task only occupied the last block
    if roundedStartTime == roundedEndTime:
        context["message"] = "Task cannot begin after 11:45PM"
        return render(request, 'wasabicalendar/modifytask.html', context)

    # count overlap, if any 15 minutes slot has > 5 tasks, create an error message 
    # and let user reenter the infotmation
    timeblock = dict()
    for t in calendar.tasks.all():
        if t.id != id:
            if t.taskDate == form.cleaned_data['taskDate']:
                block = datetime.timedelta(minutes=15)
                st = datetime.datetime.combine(t.taskDate, roundedStartTime)
                et = datetime.datetime.combine(t.taskDate, roundedEndTime)
                while (st != et):
                    if t.startTime <= st.time() and t.endTime > st.time():
                        if st not in timeblock:
                            timeblock[st] = 1
                        else:
                            timeblock[st] += 1
                    st += block
    for key in timeblock:
        if timeblock[key] >= 5:
            context['createmessage'] = "You can only create up to 5 overlapped tasks."
            return render(request, 'wasabicalendar/modifytask.html', context)
    try:
        tag = Tag.objects.get(id=form.cleaned_data['tag'])
    except:
        request.session['message'] = 'Invalid tag'
        return redirect('modify_task', id=task.id)
    description = task.description
    description.text = form.cleaned_data["description"]
    description.location = form.cleaned_data["location"]
    description.link = form.cleaned_data["link"]
    task.topic = form.cleaned_data['topic']
    task.tag = tag
    task.taskDate = form.cleaned_data['taskDate']
    task.startTime = roundedStartTime
    task.endTime = roundedEndTime
    task.description = description
    description.save()
    task.updated_by = request.user
    task.update_time = timezone.now()
    task.save()
    request.session['message'] = "Task updated"
    return redirect('get_calendar', id=calendar.id)


# @brief: function called after clicking delete button in modify calendar page
# @param id: the id of the task that will be deleted
# @type id: int
# @returns: render back to calendar page or display error message in the 
#           modify calendar page
@login_required
@transaction.atomic
def delete_helper(request, id):
    try:
        task = Task.objects.select_for_update().get(id=id)
        db_update_time = task.update_time
    except:
        # handle case when task with the id doesn't exist
        message = 'Task does not exist'
        request.session["message"] = message
        return redirect('home')

    calendar = task.calendar
    
    if (request.user not in calendar.members.all() and 
        request.user != calendar.owner):
        request.session['message'] = "No access to the calendar"
        return redirect('home')

    if request.method != 'POST':
        request.session['message'] = "Please access this page with a GET request"
        return redirect('get_calendar', id=calendar.id)
    
    # get update time stored in hidden field for time stamp
    hidden_update_time = request.POST['hidden_update_time_delete']
    
    # check whether other users have update the task after opening the page
    if str(db_update_time) != str(hidden_update_time):
        request.session["message"] = ("Another user has modified this task." + 
                                    " Please re-enter.")
        return redirect('modify_task', id=task.id)
        
    task.delete()
    request.session['message'] = "Task deleted"
    return redirect('get_calendar', id=calendar.id)

def get_cal_list_wrapper(request):
    if not request.user.id:
        return _my_json_error_response("You must log in", status = 401)
    if request.method != 'GET':
        return _my_json_error_response("You must use a GET request for this operation", 
                                        status=405)
    
    if not 'cal_id' in request.GET or not request.GET['cal_id']:
        return _my_json_error_response("You must have a calendar id.", status = 400)

    if not request.GET['cal_id'].isdigit() or int(request.GET['cal_id']) <= 0:
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    if (not request.GET['cal_id'].isdigit() or 
            int(request.GET['cal_id']) > Calendar.objects.all().count()):
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    if not 'week' in request.GET or not request.GET['week']:
        return _my_json_error_response("You must choose a valid week", status = 400)
    
    # retrieve week and cid info
    cid = int(request.GET['cal_id'])
    week = request.GET['week']

    try:
        startDay = datetime.datetime.strptime(week,"%Y-%m-%d")
    except:
        return _my_json_error_response("invalid week info", status = 400)
    
    if startDay.weekday() != 0:
        return _my_json_error_response("invalid week info", status = 400)

    return _get_cal_list_helper(request, cid, week)



# @brief: flip the "selected_user" field in Model for request.user
# and current block - used for availability feature
# @return: HttpRresponse with JSON data upon success execution
@login_required
def flip_block(request):
    # mark the 
    if not request.user.id:
        return _my_json_error_response("You must log in", status = 401)
    if request.method != 'POST':
        return HttpResponse({}, content_type='application/json', status=200)
    
    if not request.POST['cal_id'].isdigit() or int(request.POST['cal_id']) <= 0:
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    calid = int(request.POST['cal_id'])

    if not 'id' in request.POST or not request.POST['id']:
        return HttpResponse({}, content_type='application/json', status=200)

    if not request.POST['id'].isdigit() or int(request.POST['id']) > (DAY_COUNT*WEEK_COUNT):
        return HttpResponse({}, content_type='application/json', status=200)
    
    if not 'week' in request.POST or not request.POST['week']:
        return HttpResponse({}, content_type='application/json', status=200)
    
    if not 'csrfmiddlewaretoken' in request.POST or not request.POST['csrfmiddlewaretoken']:
        return HttpResponse({}, content_type='application/json', status=200)
    
    blockid = int(request.POST['id'])


    try:
        beginDate = datetime.datetime.strptime(request.POST['week'],"%Y-%m-%d")
    except:
        return HttpResponse({}, content_type='application/json', status=200)
    if beginDate.weekday() != 0:
        return HttpResponse({}, content_type='application/json', status=200)

    blockday = blockid // DAY_COUNT # obtain day in week
    blockslot = blockid % DAY_COUNT # obtain slot time in day

    # obtain date and time for Block model
    date = beginDate + datetime.timedelta(days=blockday)

    dateStr = date.strftime("%Y-%m-%d")
    
    # modify block availability
    try:
        cal = Calendar.objects.get(id=calid)
    except:
        return _my_json_error_response("No access to the calendar", status = 400)

    if request.user not in cal.members.all() and request.user != cal.owner:
        return _my_json_error_response("No access to the calendar", status = 400)

    blocks = cal.blocks.filter(date__exact=dateStr, slot__exact=blockslot)


    # modify date
    if blocks.count() != 0:
        curBlock = blocks[0] # get 0th element, should only contain 1
        # flip if in selectedUser
        if request.user in curBlock.select_user.all():
            curBlock.select_user.remove(request.user)
        else:
            curBlock.select_user.add(request.user)
        curBlock.save()
    else:
        # create new block
        curBlock = Block(date=dateStr, slot=blockslot, calendar=cal)
        curBlock.save()
        request.user.toblocks.add(curBlock)
        request.user.save()
    
    return HttpResponse({}, content_type='application/json', status=200)
    

# @brief: get prev week information
# @return: HttpRresponse with calendar JSON data upon success execution
@login_required
def prev_week(request):
    if not request.user.id:
        return _my_json_error_response("You must log in", status = 401)
    if request.method != 'GET':
        return _my_json_error_response("You must use a GET request for this operation", 
                                        status=405)
    
    if not 'cal_id' in request.GET or not request.GET['cal_id']:
        return _my_json_error_response("You must have a calendar id.", status = 400)

    if not request.GET['cal_id'].isdigit() or int(request.GET['cal_id']) <= 0:
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    if (not request.GET['cal_id'].isdigit() or 
        int(request.GET['cal_id']) > Calendar.objects.all().count()):
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    if not 'week' in request.GET or not request.GET['week']:
        return _my_json_error_response("You must choose a valid week", status = 400)
    
    
    
    # retrieve week and cid info
    cid = int(request.GET['cal_id'])
    week_info = request.GET['week']

    try:
        week = datetime.datetime.strptime(week_info,"%Y-%m-%d")
    except:
        return _my_json_error_response("invalid week info", status = 400)
    if week.weekday() != 0:
        return _my_json_error_response("invalid week info", status = 400)
    prevMonday = week - datetime.timedelta(days=7)
    prev_info = prevMonday.strftime("%Y-%m-%d")
    return _get_cal_list_helper(request, cid, prev_info)


# @brief: get next week information
# @return: HttpRresponse with calendar JSON data upon success execution
@login_required
def next_week(request):
    if not request.user.id:
        return _my_json_error_response("You must log in", status = 401)
    if request.method != 'GET':
        return _my_json_error_response("You must use a GET request for this operation", 
                                        status=405)
    
    if not 'cal_id' in request.GET or not request.GET['cal_id']:
        return _my_json_error_response("You must have a calendar id.", status = 400)

    if not request.GET['cal_id'].isdigit() or int(request.GET['cal_id']) <= 0:
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    if (not request.GET['cal_id'].isdigit() or 
        int(request.GET['cal_id']) > Calendar.objects.all().count()):
        return _my_json_error_response("You must use a valid calendar.", status = 400)
    
    if not 'week' in request.GET or not request.GET['week']:
        return _my_json_error_response("You must choose a valid week", status = 400)
    
       
    
    # retrieve week and cid info
    cid = int(request.GET['cal_id'])
    week_info = request.GET['week']

    try:
        week = datetime.datetime.strptime(week_info,"%Y-%m-%d")
    except:
        return _my_json_error_response("invalid week info", status = 400)
    if week.weekday() != 0:
        return _my_json_error_response("invalid week info", status = 400)

    prevMonday = week + datetime.timedelta(days=7)
    prev_info = prevMonday.strftime("%Y-%m-%d")
    return _get_cal_list_helper(request, cid, prev_info)


# @brief: get task data with task id
# @return: HttpRresponse with calendar JSON data upon success execution
@login_required
def get_task(request):
    if not request.user.id:
        return _my_json_error_response("You must log in", status = 401)
    if request.method != 'GET':
        return _my_json_error_response("You must use a GET request for this operation", 
                                    status=405)
    
    if not 'id' in request.GET or not request.GET['id']:
        return _my_json_error_response("You must have a task id.", status = 400)

    if not request.GET['id'].isdigit() or int(request.GET['id']) <= 0:
        return _my_json_error_response("You must use a valid task.", status = 400)
    

    id = int(request.GET['id'])
    try:
        task = Task.objects.get(id=id)
    except:
        return _my_json_error_response("No access to the task.", status = 400)

    
    # generate return value
    parsedStart = task.startTime.strftime("%H:%M:%S")
    parsedEnd = task.endTime.strftime("%H:%M:%S")
    parsedDate = task.taskDate.strftime("%Y-%m-%d")
    data = {
        'id':task.id,
        "topic": task.topic,
        'link':task.description.link,
        'location':task.description.location,
        'description':task.description.text,
        'date':parsedDate,
        "startTime": parsedStart,
        "endTime": parsedEnd,
    }    
    response_json = json.dumps(data)
    return HttpResponse(response_json, content_type='application/json')
