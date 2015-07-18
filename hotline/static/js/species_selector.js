$(document).ready(function(){

    // when a category is selected, we need to change up the species field
    $('body').on('change', '#id_reported_category', function(e){
        var category_id = $(this).val();
        if(category_id){
            $('#reported-species').show()

            // hide all the species and then foreach species in that category, show it
            var species_ids = category_id_to_species_id[category_id];
            $('#id_reported_species option').hide()
            for(var i = 0; i < species_ids.length; i++){
                $('#id_reported_species option[value="' + species_ids[i] + '"]').show();
            }

            // the first option is the "Unknown" option, so it should always be visible
            $('#id_reported_species option:first').show()
            // if the species that was selected was hidden, reset to the "Unknown" option
            if($('#id_reported_species option:selected').css("display") == "none"){
                $('#id_reported_species').val("");
            }
        } else {
            $('#reported-species').hide()
        }
    });
    $('#id_reported_category').change()
});
