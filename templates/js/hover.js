function change_on_hover(event) {
    var ds = Bokeh.documents[0].get_model_by_name(event.target.id);
    if (event.type == 'mouseenter') {
        ds.attributes.glyph.attributes.line_alpha = 0;
    }
    if (event.type == 'mouseleave') {
        ds.attributes.glyph.attributes.line_alpha = 1;
    }
    ds.change.emit();
}