container.onmouseover = container.onmouseout = handler;

function handler(event) {

    if (event.type == 'mouseover') {
        event.target.style.background = 'pink'
    }
    if (event.type == 'mouseout') {
        event.target.style.background = ''
    }
}