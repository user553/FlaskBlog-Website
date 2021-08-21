$(document).ready(function(){
    $(".heart").on('click', function() {
        let clicked_id = "#"+$(this).attr('id');
        $.ajax({
          url: '/like',
          data: {id: clicked_id},
          type: 'POST',
          success: function(data) {
            console.log('success');
            window.location.reload();
          },
          error: function(data) {
            alert("Something went wrong. Try again!")
          },
        }); 
    });
  });