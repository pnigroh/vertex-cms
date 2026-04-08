/**
 * Popup-based multi-image upload for PropertyImage inlines.
 *
 * Adds an "Upload Multiple Images" button above the images inline.
 * Clicking it opens a popup window that uploads files to a custom
 * Django admin endpoint via AJAX — no inline formset manipulation.
 *
 * The button is only shown when editing an existing property (i.e.
 * the URL contains a numeric property ID).
 */
(function () {
  "use strict";

  function init() {
    var group = document.getElementById("images-group");
    if (!group) return;
    if (group.querySelector(".bulk-upload-wrapper")) return;

    // Extract property ID from the URL:  /admin/properties/property/<id>/change/
    var match = window.location.pathname.match(
      /\/properties\/property\/(\d+)\/change\//
    );
    if (!match) {
      // New (unsaved) property — no ID yet.  Show a hint instead.
      var hint = document.createElement("div");
      hint.className = "bulk-upload-wrapper";
      hint.style.cssText =
        "padding:10px 12px;background:#fff8e1;border-bottom:1px solid #ffe082;" +
        "font-size:13px;color:#795548;";
      hint.textContent =
        "Save the property first to enable multi-image upload.";
      group.insertBefore(hint, group.firstChild);
      return;
    }

    var propertyId = match[1];
    var uploadUrl =
      "/admin/properties/property/" + propertyId + "/upload-images/";

    // Build button
    var wrapper = document.createElement("div");
    wrapper.className = "bulk-upload-wrapper";
    wrapper.style.cssText =
      "padding:10px 12px;background:#f0f6fa;border-bottom:1px solid #cde;" +
      "margin-bottom:0;";

    var btn = document.createElement("a");
    btn.href = "#";
    btn.textContent = "\u2795  Upload Multiple Images";
    btn.style.cssText =
      "display:inline-block;padding:8px 20px;background:#417690;color:#fff;" +
      "border-radius:4px;font-size:13px;font-weight:600;text-decoration:none;" +
      "letter-spacing:.3px;";

    btn.addEventListener("mouseenter", function () {
      this.style.background = "#205067";
    });
    btn.addEventListener("mouseleave", function () {
      this.style.background = "#417690";
    });

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var w = 620;
      var h = 560;
      var left = (screen.width - w) / 2;
      var top = (screen.height - h) / 2;
      window.open(
        uploadUrl,
        "upload_images",
        "width=" + w + ",height=" + h + ",left=" + left + ",top=" + top +
        ",resizable=yes,scrollbars=yes"
      );
    });

    wrapper.appendChild(btn);
    group.insertBefore(wrapper, group.firstChild);
  }

  // Run after all admin scripts (adminsortable2, inlines.js) have finished.
  window.addEventListener("load", init);
})();
