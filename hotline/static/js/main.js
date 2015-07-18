$(document).ready(function(){
    /* when a new formset is to be added, clone the first formset-row (which
     * acts as a template), replace all the __prefix__ placeholders, and append
     * it after the last formset-row. Make sure to update the management form
     * TOTAL_FORMS field
     */
    $('.formset-adder').on('click', function(e){
        e.preventDefault();
        var formset = $(this).closest(".formset");
        var copy = formset.find('.formset-row:first').clone(true, true);
        // figure out what number to use for this new formset
        var n = formset.find('.formset-row').length - 1; // minus 1 because of the hidden empty_form
        // update the name/ids on the clone
        copy.html(copy.html().replace(/__prefix__/g, n))
        // add it to the formset
        formset.find('.formset-row:last').after(copy);
        copy.show()

        // update the django management form so it knows a new form was added
        var total_forms = formset.find('*[name$="TOTAL_FORMS"]');
        total_forms.val(1+parseInt(total_forms.val(), 10))

        // fire off a custom event to notify listeners that something was added
        $(this).trigger("formset:added");
    })

    // make the deleted formset rows pretty when they are deleted
    $('.formset').on('click', '.delete-field input[type=checkbox]', function(e){
        $(this).closest('.formset-row').toggleClass("formset-row-deleted");
    });
    $('.formset-row:has(.delete-field input[type=checkbox]:checked)').addClass("formset-row-deleted")

    $('.nav-tabs a').click(function(){
        Cookies.set('tab', $(this).attr('href'), {path: window.location.pathname})
    });
    $('.nav-tabs a:first, .nav-tabs a[href="' + Cookies.get('tab') + '"]').click();
});
