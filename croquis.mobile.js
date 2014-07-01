/*
 * croquis extension for mobile
 * by @lazykuna
 */

Croquis.addToElement = function (croquis, element) {
	element.appendChild(croquis.getDOMElement());

	// mouse event
	document.addEventListener('mousedown', function (e) {
	    croquis.down(e.clientX, e.clientY);
	    document.addEventListener('mousemove', onMouseMove);
	    document.addEventListener('mouseup', onMouseUp);
	});
	function onMouseMove(e) {
	    croquis.move(e.clientX, e.clientY);
	}
	function onMouseUp(e) {
	    croquis.up(e.clientX, e.clientY);
	    document.removeEventListener('mousemove', onMouseMove);
	    document.removeEventListener('mouseup', onMouseUp);
	}

	// touch event
	document.addEventListener('touchstart', function (e) {
	    croquis.down(e.touches[0].pageX, e.touches[0].pageY);
	    document.addEventListener('touchmove', onTouchMove);
	    document.addEventListener('touchend', onTouchUp);
	});
	var tx, ty;
	function onTouchMove(e) {
		tx = e.touches[0].pageX;
		ty = e.touches[0].pageY;
	    croquis.move(e.touches[0].pageX, e.touches[0].pageY);
	    e.preventDefault();
	}
	function onTouchUp(e) {
	    croquis.up(tx, ty);
	    document.removeEventListener('touchmove', onMouseMove);
	    document.removeEventListener('touchend', onMouseUp);
	}
};