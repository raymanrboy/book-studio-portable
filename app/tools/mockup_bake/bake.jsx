// Pilot bake of one mockup template (Photoshop CC 2019, ExtendScript ES3, ASCII only).
// JOB = { status, items: [{template, out, passes: [{name, fills: [{layer, image}]}], truths: [{name, fills}]}] }
// The template copy is opened in 16 bit; every pass fills all the slots and saves PNG + TIFF (16 bit).
// Then the copy is opened again as it is (8 bit) and filled with the real pictures: the truth to compare with.

var STATUS = { state: "running", done: [], problems: [], times: {} };

function trim(s) { return String(s).replace(/^\s+|\s+$/g, ""); }

function report() {
    var f = new File(JOB.status);
    f.encoding = "UTF-8";
    if (!f.open("w")) return;
    var parts = [];
    for (var i = 0; i < STATUS.done.length; i++) parts.push('"' + STATUS.done[i] + '"');
    var probs = [];
    for (i = 0; i < STATUS.problems.length; i++) probs.push('"' + String(STATUS.problems[i]).replace(/["\\]/g, "'") + '"');
    var times = [];
    for (var k in STATUS.times) if (STATUS.times.hasOwnProperty(k)) times.push('"' + k + '":' + STATUS.times[k]);
    f.write('{"state":"' + STATUS.state + '","done":[' + parts.join(",") + '],"problems":[' + probs.join(",") +
            '],"times":{' + times.join(",") + '}}');
    f.close();
}

function message(e) { return String(e && e.message ? e.message : e) + (e && e.line ? " (line " + e.line + ")" : ""); }

function findLayer(container, path) {
    var layers = container.layers;
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        if (trim(layer.name) !== path[0]) continue;
        if (path.length === 1) return layer;
        if (layer.typename === "LayerSet") {
            var inner = findLayer(layer, path.slice(1));
            if (inner) return inner;
        }
    }
    return null;
}

function replaceContents(doc, path, image) {
    var layer = findLayer(doc, path);
    if (!layer) throw "no layer " + path.join("/");
    var chain = [];
    for (var p = layer; p && p.typename !== "Document"; p = p.parent) chain.push({ layer: p, visible: p.visible });
    var layer_name = layer.name;
    doc.activeLayer = layer;
    var d = new ActionDescriptor();
    d.putPath(charIDToTypeID("null"), new File(image));
    executeAction(stringIDToTypeID("placedLayerReplaceContents"), d, DialogModes.NO);
    // Photoshop renames a layer named like its old file after the new file ("COVER_" in Cover 1): put the name back
    if (doc.activeLayer.name !== layer_name) doc.activeLayer.name = layer_name;
    for (var i = 0; i < chain.length; i++) {
        if (chain[i].layer.visible !== chain[i].visible) chain[i].layer.visible = chain[i].visible;
    }
}

function fill(doc, fills) {
    app.activeDocument = doc;
    for (var i = 0; i < fills.length; i++) replaceContents(doc, fills[i].layer, fills[i].image);
}

function setFillColour(doc, name, rgb) {
    app.activeDocument = doc;
    var layer = findLayer(doc, [name]);
    if (!layer) throw "no layer " + name;
    doc.activeLayer = layer;
    var d = new ActionDescriptor(), r = new ActionReference(), f = new ActionDescriptor(), c = new ActionDescriptor();
    r.putEnumerated(stringIDToTypeID("contentLayer"), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
    d.putReference(charIDToTypeID("null"), r);
    c.putDouble(charIDToTypeID("Rd  "), rgb[0]);
    c.putDouble(charIDToTypeID("Grn "), rgb[1]);
    c.putDouble(charIDToTypeID("Bl  "), rgb[2]);
    f.putObject(charIDToTypeID("Clr "), charIDToTypeID("RGBC"), c);
    d.putObject(charIDToTypeID("T   "), stringIDToTypeID("solidColorLayer"), f);
    executeAction(charIDToTypeID("setd"), d, DialogModes.NO);
}

function savePng(doc, path, compression) {
    app.activeDocument = doc;
    var o = new PNGSaveOptions();
    o.compression = compression;
    o.interlaced = false;
    doc.saveAs(new File(path), o, true, Extension.LOWERCASE);
}

function saveTiff(doc, path) {
    app.activeDocument = doc;
    var o = new TiffSaveOptions();
    o.imageCompression = TIFFEncoding.NONE;
    o.layers = false;
    o.alphaChannels = false;
    o.byteOrder = ByteOrder.IBM;
    o.embedColorProfile = true;
    doc.saveAs(new File(path), o, true, Extension.LOWERCASE);
}

(function main() {
    var dialogs = app.displayDialogs;
    app.displayDialogs = DialogModes.NO;
    var t0 = new Date().getTime();
    try {
        report();
        for (var n = 0; n < JOB.items.length; n++) {
            var it = JOB.items[n], doc, i, t1 = new Date().getTime();
            if (it.passes.length) {
                doc = app.open(new File(it.template));
                doc.bitsPerChannel = BitsPerChannelType.SIXTEEN;
                for (i = 0; i < it.passes.length; i++) {
                    var p = it.passes[i];
                    try {
                        fill(doc, p.fills);
                        savePng(doc, it.out + "/" + p.name + ".png", 1);
                        STATUS.done.push(n + ":" + p.name);
                    } catch (e) {
                        STATUS.problems.push(n + ":" + p.name + ": " + message(e));
                    }
                    report();
                }
                doc.close(SaveOptions.DONOTSAVECHANGES);
            }
            STATUS.times["bake" + n] = new Date().getTime() - t1;
            doc = app.open(new File(it.template));
            if (it.truths16) doc.bitsPerChannel = BitsPerChannelType.SIXTEEN;
            for (i = 0; i < it.truths.length; i++) {
                var t2 = new Date().getTime();
                try {
                    fill(doc, it.truths[i].fills);
                    var cs = it.truths[i].colours || [];
                    for (var c = 0; c < cs.length; c++) setFillColour(doc, cs[c].layer, cs[c].rgb);
                    savePng(doc, it.out + "/" + it.truths[i].name + ".png", 3);
                    STATUS.done.push(n + ":" + it.truths[i].name);
                } catch (e) {
                    STATUS.problems.push(n + ":" + it.truths[i].name + ": " + message(e));
                }
                STATUS.times["truth" + n + "_" + i] = new Date().getTime() - t2;
                report();
            }
            doc.close(SaveOptions.DONOTSAVECHANGES);
        }
        STATUS.state = "done";
    } catch (e) {
        STATUS.state = "error";
        STATUS.problems.push(message(e));
    } finally {
        app.displayDialogs = dialogs;
    }
    STATUS.times.total = new Date().getTime() - t0;
    report();
})();
