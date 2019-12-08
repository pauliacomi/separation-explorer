var indices = cb_data.source.selected.indices;
if (indices.length > 0) {

    const idx = indices[0];
    tp = tp.replace('@temp', cb_data.source.data['temp'][idx]);
    tp = tp.replace('@doi', cb_data.source.data['doi'][idx]);

    var det = document.getElementById('iso-details')
    det.style.display = 'block';
    var rect = cb_data.getBoundingClientRect();
    console.log(rect.top, rect.right, rect.bottom, rect.left);
    det.style.left = Number(rect.left) + Number(cb_data.geometries.sx) + Number(20) + 'px';
    det.style.top = Number(rect.top) + Number(cb_data.geometries.sy) - Number(20) + 'px';
    det.innerHTML = tp;
    
    console.log(cb_data.geometries)

    // document.getElementById('iso-details-temp').innerHTML = cb_data.source.data['temp'][idx];
    // var doi = cb_data.source.data['doi'][idx];
    // document.getElementById('iso-details-doi').innerHTML = "<a href=\"https://dx.doi.org/" + doi + "\"> link </a>";
    // document.getElementById('iso-details-isodb').innerHTML = "<a href = \"https://adsorption.nist.gov/isodb/index.php?DOI=" + doi + "#biblio\"> link </a>"
}