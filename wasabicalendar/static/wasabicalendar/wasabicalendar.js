/**
 * @file wasabicalendar.js
 * @brief A javascript file that controls mostly AJAX feature
 * of the web application Wasabicalendar.
 * 
 * Functions include loading page with udpate of calendar and tag, switching
 * to prev/next week, and get task info.
 * 
 * The HTML to calendar are generated frequently based on server response.
 *
 * @author Jiayi Wang <jiayiwan@andrew.cmu.edu>
 */

"use strict"

/**
 * @brief Send a new request to load all calendar info in response to
 * the function call in window.onload in calendar page view
 *
 * loadPage is called every 1000 ms to fetch calendar info
 */
function loadPage() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return
        updatePage(xhr)
    }

    // fetch calendar json with current calendar id
    let cal_id = document.getElementById("cal_id")
    let cid = cal_id.value
    let week_info = document.getElementById("week_info")
    let week = week_info.value
    xhr.open("GET", `wasabicalendar/get-cal-list?cal_id=${cid}&week=${week}`)
    xhr.send()
}

/**
 * @brief Update calendar page view in response to server's xhr
 * response after loadPage()
 *
 * @param[in] xhr: XHR response that contains JSON response
 * of calendar block info + task info for current week.
 */
function updatePage(xhr) {
    if (xhr.status == 200) { // if status is normal
        let response = JSON.parse(xhr.responseText)
        updateTag(response)
        updateCalendar(response)
        // update week info
        let week_info = document.getElementById("week_info")
        let week = response['week']
        week_info.value = week[0]
        updateCalHead(week)
    }

    // cannot connect to server
    if (xhr.status == 0) {
        displayError("Cannot connect to server")
    }

    // response in incorrect format
    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    // error response from server
    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }
}

/**
 * @brief Update calendar header by setting wkday innerHTML
 *
 * @param[in] week: a list of date in current week
 */
function updateCalHead(week) {
    const weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday',
                      'Saturday','Sunday']
    // loop through all days in week
    for (let i = 0; i < 7; i++) {
        let curDay = week[i]
        let curBlock = document.getElementById("wkday_"+i)
        let curWkday = weekdays[i]
        curBlock.innerHTML = curWkday + "<br>" + curDay
    }
}

/*
  @ brief: update HTML of tags list using AJAX
*/
function updateTag(response) {
    let tag_data = response['tags']
    let list = document.getElementById("my_tags_go_here")
    var tagHTML = ""
    for (let i = 0; i < tag_data.length; i++) {
        let item = tag_data[i]
        tagHTML += ("<li style=\"color:" + item.color + 
        ";text-shadow:-1px 0 black, 0 1px black, 1px 0 black, 0 -1px black;\">")
                + item.name + "</li>"
    }
    list.innerHTML = tagHTML
}


/**
 * @brief Update calendar content by setting new innerHTML
 *
 * @param[in] response: entire JSON response from server
 * data field contains all list of blocks and tasks to display
 */
function updateCalendar(response) {
    // adds each new block to the list
    let taskBlocks = response['data'] // tasks

    var finalHTML = "<div class=\"week\">"
    finalHTML += makeHour() // make Hour for 4-15min time slots
    for (let i = 0; i<taskBlocks.length; i++) {
        // access current block number
        var curDayBlock = taskBlocks[i]
        for (let j = 0; j < curDayBlock.length; j++) {
            var curTimeBlock = curDayBlock[j]
            var curNum = 0
            var inBlock = false
            try {
                curNum = curTimeBlock['block'][0]
                inBlock = curTimeBlock['block'][1]
            } catch {
                curNum = 0
                inBlock = false
            }
    
            var curTasks = []
            try {
                curTasks = curTimeBlock["tasks"]
            } catch {
                curTasks = []
            }
    
            // add elements to list
            var curGrid = makeCalendarGrid(i, 96*i+j, curNum, inBlock, curTasks)
            finalHTML += curGrid;
        }
    }
    finalHTML += "</div>" // finish front calendar week div
    let cal = document.getElementById("front_content")
    cal.innerHTML = finalHTML
}

/**
 * @brief Make hour div block HTML
 *
 * @return HTML for hour div
 */
function makeHour() {
    var res = "" // hour display HTML
    for (let i = 0; i < 24; i++) {
        res += "<div class=\"hour\">"
        res += i + ":00"
        res += "</div>"
    }
    return res
}

/**
 * @brief Make calendar grid HTML
 * set calendar HTML for current block
 * idx = index of block in the week
 * counter = number of clicked times
 * tasks = task at current time block
 *
 * @param[in] dayIdx: integer index of current day in week
 * @param[in] idx: index of block in 96*7 blocks
 * @param[in] counter: integer counter of number of selected user
 * @param[in] inBlock: true if user in block false otherwise
 * @param[in] tasks: list of task info
 * @return HTML for time slot grid div
 */
function makeCalendarGrid(dayIdx, idx, counter, inBlock, tasks){
    var res = ""
    // if mod 4 = 0 then start of an hour
    if (idx % 4 == 0) {
        res += "<div class=\"hour\">"
    }
    // grid start
    res += "<div class = \"grid\">"
    // make background block
    res += makeBlock(idx, counter, inBlock)
    // add tasks
    res += makeTasks(dayIdx, idx, tasks)
    // div end
    res += "</div>"
    // if mod 4 = 3 then end of an hour
    if (idx % 4 == 3) {
        res += "</div>"
    }
    return res
}

/**
 * @brief Make HTML for tasks 
 *
 * @param[in] dayIdx: integer index of current day in week
 * @param[in] counter: integer counter of number of selected user
 * @param[in] inBlock: true if user in block false otherwise
 * @return HTML for selected block div
 */
function makeBlock(idx, counter, inBlock) {
    var res = "<button class=\"cell_"
    var curNumStr = ""
    if (counter <= 5) {
        curNumStr = counter.toString()
    } else {
        curNumStr = "5" // upper bound the counter to 5
    }
    // add cell counter and if current user in block to res
    res += (curNumStr + "\" style=\"border-radius:0px\" value=\"" + 
            inBlock.toString())
    // add id to block
    res += "\" id=\"id_block_"+ idx + "\" "
    // add onclick function
    res += "onclick=\"flip_block(" + idx + ")\"></button>"
    return res
}

/**
 * @brief Make HTML for tasks 
 *
 * @param[in] dayIdx: integer index of current day in week
 * @param[in] idx: index of block in 96*7 blocks
 * @param[in] tasks: list of task info
 * @return HTML for time task div
 */
function makeTasks(dayIdx, idx, tasks) {
    var res = "" // final HTML text to return
    // create div/button for all five possible tasks
    for(let i = 0; i < 5; i++) {
        let curTaskList = tasks[i]
        if (0 < curTaskList.length) {
            // get current task info
            let curTask = curTaskList[0]
            let curId = curTask['id']
            let curTopic = curTask['topic']
            let curStartBlock = curTask['startBlock']
            let curEndBlock = curTask['endBlock']
            let curColor = curTask['color']

            if (dayIdx * 96 + curStartBlock == idx) {
                // start at current time
                var blockHeight = (curEndBlock - curStartBlock) * 100
                // generate HTML
                res += "<button class=\"task_" + i + "\" " // add task class
                res += ("style=\"height:" + blockHeight +"\%;background-color:"+ 
                curColor +"\" ") // add height and color
                res += "id=\"id_task_" + curId + "\" " // add id
                // add flip_task onclick function
                res += "onclick=\"flip_task(" + curId + ")\">"
                res += curTopic + "</button>"
            } else {
                // start at previous time
                res += "<div class=\"task_" + i + "\" " // add task class
                // set visibility to hidden
                res += "style=\"visibility:hidden\"></div>"
            }
        } else {
            // no task exist at this slot
            res += "<div class=\"task_" + i + "\" " // add task class
            // set visibility to hidden
            res += "style=\"visibility:hidden\"></div>"
        }
    }
    return res
}

/**
 * @brief Flip task in response to onclick
 *
 * @param[in] id: id of task
 */
function flip_task(id) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return
        get_back(xhr)
    }
    xhr.open("GET", `wasabicalendar/get-task?id=${id}`)
    xhr.send()
}

/*
 update the post page when readyState is not DONE
*/
/**
 * @brief Update the post page with xhr response from get-task
 *
 * @param[in] xhr: XHR response that contains JSON response
 * of calendar block info + task info for current week.
 */
function get_back(xhr) {
    if (xhr.status == 200) { // if status is normal
        let response = JSON.parse(xhr.responseText)
        updateBack(response)
    }

    if (xhr.status == 0) {
        displayError("Cannot connect to server")
    }

    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }
}


/**
 * @brief Update backHTML and flip after receiving task info
 *
 * @param[in] response: entire task JSON response from server
 * data field contains all task related field to be displayed
 */
function updateBack(response) {
    // get info from response
    let data = response
    let id = data['id']
    let topic = data['topic']
    let link = data['link']
    let date = data['date']
    let startTime = data['startTime']
    let endTime = data['endTime']
    let description = data['description']
    let location = data['location']
    // set back HTML
    let back = document.getElementById("back_calendar") // 24*7 blocks 
    let backHTML = makeBackHTML(id, topic, description, location, link, 
                                date, startTime, endTime)
    back.innerHTML = backHTML // set back HTML to result of makeBackHTML
    back.onclick=flip_back
    back.value = id
    back.scrollIntoView() // scroll to top
    $("#calendar_container").flip('toggle'); // flip to back page
}


/**
 * @brief Make Back HTML for task id
 *
 * @param[in] id: id of task
 * @param[in] topic: topic of task
 * @param[in] des: description text of task
 * @param[in] location: location of task
 * @param[in] link: link of task
 * @param[in] date in "Y-M-D" format
 * @param[in] start time during the day
 * @param[in] end time during the day
 * @return HTML for back side of calendar div
 */
function makeBackHTML(id, topic, des, location, link, date, startTime, endTime){
    // add all values in div
    var res = "<div class=\"back_wrapper\">"
    res += "<div class=\"info_0\">TOPIC: " + topic + "</div>"
    if (des != "") {
        res += "<div class=\"info_1\">DESCRIPTION: " + des + "<div>"
    }
    if (location != "") {
        res += "<div class=\"info_2\">LOCATION: " + location + "<div>"
    }
    if (link != "") {
        res += "<div class=\"info_1\">LINK: "
        res += ("<a class=\"info_1\" target=\"_blank\" href=" + link + 
               " style=\"text-decoration:underline\">" + link + "</a></div>")
    }
    res += "<div class=\"info_2\">DATE: " + date + "</div>"
    res += "<div class=\"info_3\">START TIME: " + startTime + "</div>"
    res += "<div class=\"info_4\">END TIME: " + endTime + "</div>"
    res += ("<div class=\"info_5\"><a href=\"/modify_task/" + id + 
           "\" class=\"view_button\">Modify Task </a></div>")
    res += "</div>"
    return res
}


/**
 * @brief Flip the selected field for current block slot
 * If previously selected, now unselect the block.
 * Otherwise, select the block.
 *
 * @param[in] id: id of the block to be flipped
 */
function flip_block(id) {
    // get current block
    let block = document.getElementById("id_block_"+id)
    let blockSelectVal = block.value
    if (blockSelectVal == "true") {
        block.value = "false"
    } else {
        block.value = "true"
    } // flip the value

    let calid = document.getElementById("cal_id")
    try {
        var cal_id = parseInt(calid.value)
    } catch {
        var cal_id = 0 // invalid calendar id
    }

    // get week info
    let week_info = document.getElementById("week_info")
    let week = week_info.value
   
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        return 
    }
    // send info back to server to flip availability
    xhr.open("POST", "wasabicalendar/flip-block", true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send("csrfmiddlewaretoken="+getCSRFToken()+"&id="+id+"&cal_id="+
            cal_id+"&week="+week)
}

/**
 * @brief Flip back to front page from back page
 */
function flip_back() {
    let back = document.getElementById("back_calendar")
    let backVal = back.value
    let task = document.getElementById("id_task_" + backVal)
    task.scrollIntoView()
    $("#calendar_container").flip('toggle');
}

/**
 * @brief Send GET request to fetch previous week's data
 */
function left_click() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return
        updatePage(xhr)
    }
    let week_info = document.getElementById("week_info")
    let week = week_info.value
    let cal = document.getElementById("cal_id")
    let cid=  cal.value

    xhr.open("GET", `wasabicalendar/prev-week?cal_id=${cid}&week=${week}`)
    xhr.send()
}

/**
 * @brief Send GET request to fetch next week's data
 */
function right_click() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return
        updatePage(xhr)
    }
    let week_info = document.getElementById("week_info")
    let week = week_info.value
    let cal = document.getElementById("cal_id")
    let cid = cal.value

    xhr.open("GET", `wasabicalendar/next-week?cal_id=${cid}&week=${week}`)
    xhr.send()
}

function print_page() {
    document.body.innerHTML =  ("<div class= \"wkdays\" >" + 
    document.getElementById("current_week").innerHTML + "</div>" + 
    "<div class= \"print\" >" + 
    document.getElementById("front_content").innerHTML + "</div>")
    window.print()
    location.reload()
}

/**
 * @brief Display error and redirect to home page
 *
 * @param[in] message: error message to be displayed
 */
 function displayError(message) {
    location.href = "/"
    let errorElement = document.getElementById("id_message_msg")
    errorElement.innerHTML = message
}

/**
 * @brief Get CSRF Token for POST request
 *
 * @return CSRF token
 */
function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}