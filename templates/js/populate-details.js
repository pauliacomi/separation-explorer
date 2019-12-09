var indices = cb_data.source.selected.indices;
if (indices.length > 0) {

    const idx = indices[0];
    tp = tp.replace('@ID', cb_data.source.data['labels'][idx]);
    tp = tp.replace('@temp', cb_data.source.data['temp'][idx]);
    tp = tp.replace('@doi', cb_data.source.data['doi'][idx]);

    var det = document.getElementById('iso-details')
    det.style.display = 'flex';
    det.innerHTML = tp;
}