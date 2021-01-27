function codeAddress() {
    $('#modal_rules').modal('show')
}

window.onload = codeAddress;
$('.carousel').carousel({
    interval: false
})


function disableRuleButton() {
    let check_button = document.getElementById('blankCheckbox')
    document.getElementById('FirstCloseButton').disabled = !check_button.checked;
    document.getElementById('SecondCloseButton').disabled = !check_button.checked;
}

function enable_price_button() {
    let first_price_container = document.getElementById('four_hundred_btn')
    let second_price_container = document.getElementById('five_hundred_btn')
    let some_shit = first_price_container.classList.contains('chosen_price_button') === true || second_price_container.classList.contains('chosen_price_button') === true
    document.getElementById('go_on_first').disabled = !some_shit;
}


function enable_date_button() {
    let input_value = $('#date_input').val()
    document.getElementById('go_on_second').disabled = !input_value;
}

function enable_data_button() {
    let name_value = $('#user_name').val()
    let phone_value = $('#user_phone').val()
    document.getElementById('go_on_forth').disabled = !name_value && !phone_value
    if (!document.getElementById('go_on_forth').disabled) {
        sendingData()
        $('#modal_farewell').modal('show')
     }
}


let newSelectedDate; // undefined


$('.price-card').click(function () {
    user_input['price'] = this.getElementsByTagName('h1')[0].textContent.slice(0, 3)
    $('.price-card').removeClass('chosen_price_button');
    $(this).addClass('chosen_price_button');
});


$('.close_price').click(function () {
    $('#modal_price').modal('hide')
});

function update_date() {
    newSelectedDate = $('#datetimepicker1').datepicker('getFormattedDate'); // Update newSelectedDate value.
    user_input['date'] = newSelectedDate
}
(function($) {
  $.fn.inputFilter = function(inputFilter) {
    return this.on("input keydown keyup mousedown mouseup select contextmenu drop", function() {
      if (inputFilter(this.value)) {
        this.oldValue = this.value;
        this.oldSelectionStart = this.selectionStart;
        this.oldSelectionEnd = this.selectionEnd;
      } else if (this.hasOwnProperty("oldValue")) {
        this.value = this.oldValue;
        this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
      } else {
        this.value = "";
      }
    });
  };
}(jQuery));

$(document).ready(function() {
  $("#user_phone").inputFilter(function(value) {
    return /^\d*$/.test(value);    // Allow digits only, using a RegExp
  });
  $("#user_name").inputFilter(function(value) {
  return /^[аАбБвВгГдДеЕёЁжЖзЗиИйЙкКлЛмМнНоОпПрРсСтТуУфФхХцЦчЧшШщЩъЪыЫьЬэЭюЮяЯіІїЇґҐєЄ]*$/i.test(value); });
});




let user_input = {
    'price': null,
    'date': null,
    'time': null,
    'name': null,
    'phone': null
}


function sendingData() {
    user_input['name'] = $('#user_name').val();
    user_input['phone'] = $('#user_phone').val()
    let http = new XMLHttpRequest();
    let post_data = JSON.stringify(user_input);
    http.open("POST", '/submit_form', true);
    http.setRequestHeader('Content-type', 'application/json; charset=utf-8');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            console.log(http.responseText);
        }
    };
    http.send(post_data)
    // });
}

function grey_not_available_time(not_available_times) {
    let time_buttons = $('.time_button')
    for (let time_button in Array.from(time_buttons)) {
        let time_button_text = time_buttons[time_button].textContent
        let button_element = $(`button:contains(${time_button_text})`)
        if (not_available_times.includes(time_button_text)) {
            button_element.addClass('grey');
            button_element.css("pointer-events", "none");
        } else {
            button_element.removeClass('grey');
            button_element.css("pointer-events", "auto");
        }
    }
}

$('.time_button').click(function () {
    $('.time_button').removeClass('coral');
    $(this).addClass('coral');
    user_input['time'] = $(this).text()
    return user_input['time']
});

function enable_time_button() {
    let is_coral = $('.time_button').hasClass('coral')
    document.getElementById('go_on_third').disabled = !is_coral;
}


function sendDate(user_date) {
    let http = new XMLHttpRequest();
    let post_data = JSON.stringify({'date': user_date});
    http.open("POST", '/get_times_by_date', true);
    http.setRequestHeader('Content-type', 'application/json; charset=utf-8');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            let not_available_times = JSON.parse(http.responseText)['not_available_time']
            grey_not_available_time(not_available_times)
        }
    };
    http.send(post_data);
    // });
}


