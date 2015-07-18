var MAX_WIDTH = 800.0;
var MAX_HEIGHT = 600.0;

function resizeImage(img){
    var width = img.width;
    var height = img.height;
    var canvas = $('<canvas>');
    canvas.css({"display": "none"})
    $('body').append(canvas)
    var scale = Math.min(MAX_HEIGHT/height, MAX_WIDTH/width)
    if(scale < 1){
        height *= scale;
        width *= scale;
    }

    canvas.attr('width', width);
    canvas.attr('height', height);

    var raw_canvas = canvas.get(0);
    var ctx = raw_canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, width, height)
    var dataurl = raw_canvas.toDataURL("image/jpeg");
    canvas.remove()
    return dataurl
}

$(document).ready(function(){
    $('#images').on('change', 'input[type="file"]', function(e){
        // bail out if the browser doesn't support the filereader
        try {
            new FileReader();
        } catch(e) {
            return
        }

        // now that we have a reference to the files, reset the input so the
        // full-res images aren't posted too
        var files = $(this).get(0).files;
        $(this).attr("type", "text");
        $(this).attr("type", "file");
        $(this).get(0).value = "";
        $('#previews').html("");

        for(var i = 0; i < files.length; i++){
            var file = files[i];
            if(file){
                var reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onloadend = function (index, element, e) {
                    var append_to = element.closest(".formset-row").find(".preview");
                    var encoded_image = element.closest(".formset-row").find(".datauri");
                    var preview = $("<img />");
                    append_to.html(preview);
                    preview.attr('src', this.result);
                    encoded_image.val(resizeImage(preview.get(0)))
                    preview.attr("width", 100)
                }.bind(reader, i, $(this))
            }
        }
    })
});
