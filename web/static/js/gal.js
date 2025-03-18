function togglePlay() {
    $(":not(.hidden) > * > audio, :not(.hidden) > * > video").each(function(){
        if (this.paused ? this.play() : this.pause());
    });
}

// Enable keyboard navigation for gallery
$(document).keydown(function(e) {
    switch(e.which) {
    case 37: // left
        var href = $('.gal-prev').attr('href');
        if (href)
            window.location.href = href;
        break;
    case 39: // right
        var href = $('.gal-next').attr('href');
        if (href)
            window.location.href = href;
        break;
    case 32: // space
        togglePlay();
        break;
    case 27: // ESC
        var href = $('#albumlink').attr('href');
        window.location.href = href;
        break;
    }
    e.preventDefault();
});

$('video').click(function(){ togglePlay(); });
