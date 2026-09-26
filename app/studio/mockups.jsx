// Book Studio, listing mockups: fills copies of the owner's mockup templates (Photoshop CC 2019,
// ExtendScript = ES3: no JSON, no Array.indexOf, no String.trim). The program (mockups.py `script()`) puts
// `var JOB = {...};` in front of this text. Every path in JOB points into the utility's own run folder or
// the output folder the owner picked: the templates folder itself never appears here, the templates were
// copied before this runs. This file stays ASCII only.
//
// JOB = { status, cancel, compression, finish, cover, templates: [{ name, title, file, keepOpen,
//         fills: [{layer: [...], image}], shots: [{title, fills, save}] }] }
// JOB.cover: a copy of the book's cover picture, opened after the templates when some are left open, so the owner
// has it at hand to fit the front cover (26.09.2026); the second script closes it if he has not changed it.
// Progress goes to JOB.status as JSON; a file at JOB.cancel stops the run between pictures.
// JOB.finish: the second script of a run ("save the open ones" in the window): the templates the first one left
// open, with the front cover the owner fitted by hand, are saved as PNG and closed; nothing is opened or filled.

var CANCEL = { cancel: true };
var STATUS = { state: "running", step: 0, total: 0, title: "", saved: [], opened: [], closed: [], problems: [] };

function trim(s) {
    return String(s).replace(/^\s+|\s+$/g, "");
}

// A JSON string with everything outside printable ASCII escaped, so the status file is plain ASCII.
function quote(s) {
    var out = '"';
    for (var i = 0; i < s.length; i++) {
        var c = s.charCodeAt(i);
        if (c < 32 || c > 126 || c === 34 || c === 92) out += "\\u" + ("000" + c.toString(16)).slice(-4);
        else out += s.charAt(i);
    }
    return out + '"';
}

function toJson(v) {
    if (v === null || v === undefined) return "null";
    if (typeof v === "number" || typeof v === "boolean") return String(v);
    if (typeof v === "string") return quote(v);
    var parts = [], i;
    if (v instanceof Array) {
        for (i = 0; i < v.length; i++) parts.push(toJson(v[i]));
        return "[" + parts.join(",") + "]";
    }
    for (i in v) {
        if (v.hasOwnProperty(i)) parts.push(quote(i) + ":" + toJson(v[i]));
    }
    return "{" + parts.join(",") + "}";
}

function report() {
    var f = new File(JOB.status);
    f.encoding = "UTF-8";
    if (f.open("w")) {
        f.write(toJson(STATUS));
        f.close();
    }
}

function cancelled() {
    return new File(JOB.cancel).exists;
}

function message(e) {
    return String(e && e.message ? e.message : e) + (e && e.line ? " (line " + e.line + ")" : "");
}

// A layer by its path of names (spaces trimmed); a one-name path is found at the top of the layer list.
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

// "Replace Contents" of a smart object: the template's bend, shadows and light stay, and every linked copy
// changes with it. Selecting a layer makes a hidden one (and its group) visible: put back right after.
function replaceContents(doc, path, image) {
    var layer = findLayer(doc, path);
    if (!layer || layer.typename !== "ArtLayer" || layer.kind !== LayerKind.SMARTOBJECT) {
        throw { kind: "layer", layer: path.join("/") };
    }
    var chain = [];
    for (var p = layer; p && p.typename !== "Document"; p = p.parent) chain.push({ layer: p, visible: p.visible });
    doc.activeLayer = layer;
    var d = new ActionDescriptor();
    d.putPath(charIDToTypeID("null"), new File(image));
    executeAction(stringIDToTypeID("placedLayerReplaceContents"), d, DialogModes.NO);
    for (var i = 0; i < chain.length; i++) {
        if (chain[i].layer.visible !== chain[i].visible) chain[i].layer.visible = chain[i].visible;
    }
}

// Replacing and saving act on the ACTIVE document whatever document they are called on (seen live on
// 23.09.2026: a copy "saved" from another document held the active one's picture), so the one worked on is
// made active first.
function fill(doc, t, fills) {
    app.activeDocument = doc;
    for (var i = 0; i < fills.length; i++) {
        try {
            replaceContents(doc, fills[i].layer, fills[i].image);
        } catch (e) {
            if (e && e.kind) {
                e.template = t.name;
                throw e;
            }
            throw { kind: "place", template: t.name, layer: fills[i].layer.join("/"), detail: message(e) };
        }
    }
}

function savePng(doc, path) {
    app.activeDocument = doc;
    var o = new PNGSaveOptions();
    o.compression = JOB.compression;
    o.interlaced = false;
    doc.saveAs(new File(path), o, true, Extension.LOWERCASE); // a copy: the document itself stays unsaved
}

// One template: open the copy, put in what stays the same, then one picture per spread. Returns the
// document when it is left open for the owner.
function runTemplate(t) {
    var doc;
    try {
        doc = app.open(new File(t.file));
    } catch (e) {
        STATUS.problems.push({ kind: "open", template: t.name, detail: message(e) });
        STATUS.step += 1 + t.shots.length;
        report();
        return null;
    }
    try {
        fill(doc, t, t.fills);
    } catch (e) {
        STATUS.problems.push(e);
        if (!t.keepOpen) doc.close(SaveOptions.DONOTSAVECHANGES);
        STATUS.step += 1 + t.shots.length;
        report();
        return t.keepOpen ? doc : null;
    }
    STATUS.step += 1;
    report();
    for (var i = 0; i < t.shots.length; i++) {
        var shot = t.shots[i];
        if (cancelled()) {
            if (!t.keepOpen) doc.close(SaveOptions.DONOTSAVECHANGES);
            throw CANCEL;
        }
        STATUS.title = shot.title;
        report();
        try {
            fill(doc, t, shot.fills);
            savePng(doc, shot.save);
            STATUS.saved.push(shot.save);
        } catch (e) {
            STATUS.problems.push(e && e.kind ? e : { kind: "save", template: t.name, file: shot.save, detail: message(e) });
        }
        STATUS.step += 1;
        report();
    }
    if (t.keepOpen) {
        STATUS.opened.push(t.name);
        return doc;
    }
    doc.close(SaveOptions.DONOTSAVECHANGES);
    return null;
}

function samePath(a, b) {
    return String(a).replace(/\\/g, "/").toLowerCase() === String(b).replace(/\\/g, "/").toLowerCase();
}

// A template the first script left open: by its copy's path, else by its file name (a Save As elsewhere).
function findOpen(t) {
    var byName = null;
    // No "/" inside a regex's [...]: Photoshop's ExtendScript reads it as the regex's end ("Error 25: Expected: )",
    // the owner's screen, 26.09.2026) where any browser or Node accepts it, so the name is cut without one.
    var wanted = String(t.file).replace(/\\/g, "/");
    var name = wanted.substring(wanted.lastIndexOf("/") + 1);
    for (var i = 0; i < app.documents.length; i++) {
        var doc = app.documents[i], path = "";
        try {
            path = doc.fullName.fsName;
        } catch (e) {} // a document never saved has no file
        if (path && samePath(path, t.file)) return doc;
        if (!byName && doc.name === name) byName = doc;
    }
    return byName;
}

// The book's cover beside the templates the owner finishes (only when some are left open).
function openCover() {
    try {
        app.open(new File(JOB.cover));
        STATUS.coverOpened = true;
    } catch (e) {
        STATUS.problems.push({ kind: "open", template: "Cover", detail: message(e) });
    }
}

// The cover the first script opened: closed with the templates, only by its own path and only when the owner has
// not changed it (a changed one stays open, his work is never thrown away).
function closeCover() {
    for (var i = 0; i < app.documents.length; i++) {
        var doc = app.documents[i], path = "";
        try {
            path = doc.fullName.fsName;
        } catch (e) {}
        if (path && samePath(path, JOB.cover)) {
            try {
                if (doc.saved) {
                    doc.close(SaveOptions.DONOTSAVECHANGES);
                    STATUS.coverClosed = true;
                }
            } catch (e) {}
            return;
        }
    }
}

function finishOpen() {
    STATUS.total = JOB.templates.length;
    report();
    for (var i = 0; i < JOB.templates.length; i++) {
        var t = JOB.templates[i], shot = t.shots[0];
        if (cancelled()) throw CANCEL;
        STATUS.title = t.title;
        report();
        var doc = findOpen(t);
        if (!doc) {
            STATUS.problems.push({ kind: "closed", template: t.name });
        } else {
            try {
                savePng(doc, shot.save);
                STATUS.saved.push(shot.save);
                doc.close(SaveOptions.DONOTSAVECHANGES); // the picture holds the owner's work; the copy may go
                STATUS.closed.push(t.name);
            } catch (e) {
                STATUS.problems.push({ kind: "save", template: t.name, file: shot.save, detail: message(e) });
            }
        }
        STATUS.step += 1;
        report();
    }
    if (JOB.cover) closeCover();
}

(function main() {
    var dialogs = app.displayDialogs;
    var first = null;
    app.displayDialogs = DialogModes.NO;
    try {
        if (JOB.finish) {
            finishOpen();
        } else {
            for (var i = 0; i < JOB.templates.length; i++) STATUS.total += 1 + JOB.templates[i].shots.length;
            report();
            for (i = 0; i < JOB.templates.length; i++) {
                if (cancelled()) throw CANCEL;
                STATUS.title = JOB.templates[i].title;
                report();
                var kept = runTemplate(JOB.templates[i]);
                if (kept && !first) first = kept;
            }
            if (first && JOB.cover) openCover();
        }
        STATUS.state = "done";
    } catch (e) {
        if (e === CANCEL) {
            STATUS.state = "cancelled";
        } else {
            STATUS.state = "error";
            STATUS.detail = message(e);
        }
    } finally {
        app.displayDialogs = dialogs;
    }
    if (first) {
        try {
            app.activeDocument = first; // the owner starts with the first template he finishes by hand
        } catch (e) {}
    }
    report();
})();
