/**
 * Newsripper app JS
 * v1.0.0 -- 2019-12-04
 */

(function($) {
  "use strict";

  $(function() {
    // Change content of the "Go" button in the navbar on click (spicy buttons).
    $("#ripper-go-btn").on("click", function() {
      let theBtn = $(this);
      const width = theBtn.width();
      // HTML here is a small border spinner in Bootstrap.
      // See: https://getbootstrap.com/docs/4.4/components/spinners/#size
      theBtn.html(`<div class="spinner-border spinner-border-sm" role="status">
        <span class="sr-only">Loading...</span>
      </div>`);
      theBtn.width(width);
    });

    // Activate any toasts loaded into the page.
    $(".toast").toast("show");

    /**
     * Add triggers to article deletion buttons to show the delete confirmation modal.
     * Each deletion link should have class "ctl-article-delete"
     * and data attributes "data-article-id" and "data-article-title".
     * "data-target", if provided, is used for the modal id to edit and show
     * (defaults to "delete-confirmation-modal").
     */
    $("body").on("click", ".ctl-article-delete", function(e) {
      e.preventDefault();
      const ctlElem = $(this);
      const articleId = ctlElem.data("article-id");
      const articleTitle = ctlElem.data("article-title");
      if (typeof articleId === "undefined") {// || typeof articleTitle === "undefined") {
        console.warn("'data-article-id' required: ", ctlElem);
        return;
      }
      if (typeof articleTitle === "undefined") {
        console.warn("'data-article-title' required", ctlElem);
        return;
      }
      let modalTarget = ctlElem.data("target");
      if (typeof modalTarget === "undefined") {
        modalTarget = "delete-confirmation-modal";
      }

      const deletionModal = $("#" + modalTarget);
      deletionModal.find("p.article-title").text(articleTitle);
      deletionModal.find("input[name=article_id]").val(articleId);
      deletionModal.modal("show");
    });


    /**
     * Add triggers to article reprocessing buttons to show the reprocess confirmation modal.
     * Each reprocessing link should have class "ctl-article-reprocess"
     * and data attributes "data-article-id" and "data-article-title".
     * "data-target", if provided, is used for the modal id to edit and show
     * (defaults to "reprocess-confirmation-modal").
     */
    $("body").on("click", ".ctl-article-reprocess", function(e) {
      e.preventDefault();
      const ctlElem = $(this);
      const articleId = ctlElem.data("article-id");
      const articleTitle = ctlElem.data("article-title");
      if (typeof articleId === "undefined") {// || typeof articleTitle === "undefined") {
        console.warn("'data-article-id' required: ", ctlElem);
        return;
      }
      if (typeof articleTitle === "undefined") {
        console.warn("'data-article-title' required", ctlElem);
        return;
      }
      let modalTarget = ctlElem.data("target");
      if (typeof modalTarget === "undefined") {
        modalTarget = "reprocess-confirmation-modal";
      }

      const reprocessingModal = $("#" + modalTarget);
      reprocessingModal.find("p.article-title").text(articleTitle);
      reprocessingModal.find("input[name=article_id]").val(articleId);
      reprocessingModal.modal("show");
    });
  });
})(jQuery);
