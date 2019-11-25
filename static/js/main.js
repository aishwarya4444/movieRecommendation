$(document).ready(function () {

    $.fn.welcome = function () {
        $.ajax({
            type: 'GET',
            url: '/welcome',
            data: null,
            contentType: false,
            cache: false,
            processData: false,
            async: true,
            success: function (response) {
                resultHTML = '';
                tmpRow = '';
                $.each(response, function(id, name){
                  tmpRow = '<div class="recommend" movieid="' + id + '">' + name + '</div>';
                  resultHTML += tmpRow;
                });
                $('#welcome').hide();
                $('#recommendations').html(resultHTML);
                document.getElementById('result').removeAttribute('hidden');
                console.log('Success!');
            },
            error: function(xhr) {
                console.log('Error!');
            },
            complete: function() {
                console.log('Initial recommendations run.');
            }
        });
    }

    // Recommend
    $.fn.recommend = function (event) {
        var movieId = event.target.getAttribute('movieid');

        if(movieId === '') {
            return;
        }

        selectedMovie = event.target.innerText;
        $('#selected').html('<div><b>Selected Movie : </b>' + selectedMovie + '</div>');
        document.getElementById('selected').removeAttribute('hidden');

        $.ajax({
            type: 'POST',
            url: '/recommend',
            data: parseInt(movieId),
            contentType: false,
            cache: false,
            processData: false,
            async: true,
            success: function (response) {
                // Get and display the result
                resultHTML = '';
                tmpRow = '';
                $.each(response, function(id, name){
                  tmpRow = '<div class="recommend" movieid="' + id + '">' + name + '</div>';
                  resultHTML += tmpRow;
                });
                $('#welcome').hide();
                $('#recommendations').html(resultHTML);
                console.log('Success!');
            },
            error: function(xhr) {
                console.log('Error!');
            },
            complete: function() {
                console.log('Recommendations run.');
            }
        });
    }

    // Get results when button is clicked
    $('#recommendations').click(function (event) {
        event.stopPropagation();
        event.stopImmediatePropagation();
        $.fn.recommend(event);
    });

    $('#welcome').click(function () {
        $.fn.welcome();
    });

    // Get results when enter key is pressed
    $(window).keydown(function (event) {
        var keyCode = event.keyCode ? event.keyCode : event.which;
        if(keyCode == 13) {
            event.preventDefault();
            $.fn.predict();
        }
    });

});
