function togglePlay() {
    $(":not(.hidden) > * > audio, :not(.hidden) > * > video").each(function(){
        if (this.paused ? this.play() : this.pause());
    });
}

function hydrateMediaSource(el) {
    var dataSrc = el.getAttribute("data-src");
    var dataSrcset = el.getAttribute("data-srcset");
    if (dataSrc) {
        el.setAttribute("src", dataSrc);
        el.removeAttribute("data-src");
    }
    if (dataSrcset) {
        el.setAttribute("srcset", dataSrcset);
        el.removeAttribute("data-srcset");
    }
    var dataSizes = el.getAttribute("data-sizes");
    if (dataSizes) {
        el.setAttribute("sizes", dataSizes);
        el.removeAttribute("data-sizes");
    }
}

function initLazyMedia() {
    var lazy = document.querySelectorAll("[data-src], [data-srcset]");
    if (!lazy.length) return;

    if (!("IntersectionObserver" in window)) {
        lazy.forEach(hydrateMediaSource);
        return;
    }

    var io = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                hydrateMediaSource(entry.target);
                io.unobserve(entry.target);
            }
        });
    }, { rootMargin: "200px 0px", threshold: 0.1 });

    lazy.forEach(function(el) { io.observe(el); });
}

document.addEventListener("DOMContentLoaded", initLazyMedia);

// Enable keyboard navigation for gallery
$(document).keydown(function(e) {
    var handled = true;
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
    default:
        handled = false;
    }
    if (handled) e.preventDefault();
});

$('video').click(function(){ togglePlay(); });
