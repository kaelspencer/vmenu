window.onload = function() {
    scrollUp = document.getElementById('scroll-up');
    scrollDown = document.getElementById('scroll-down');
    scroller = document.getElementById('scroller');
    if (scrollUp === null || scrollDown === null || scroller === null) {
        throw "Can't find the correct objects.";
    }
    delta = 300;

    scrollUp.onclick = function() {
        scroll(scroller, delta);
        return false;
    };

    scrollDown.onclick = function() {
        scroll(scroller, -1 * delta);
        return false;
    };
};

function scroll(scroller, delta) {
    cur = scroller.style.marginTop === '' ? 0 : parseInt(scroller.style.marginTop);
    cur += delta;
    if (cur > 0){
        cur = 0;
    }

    scroller.style.marginTop = cur;
}
