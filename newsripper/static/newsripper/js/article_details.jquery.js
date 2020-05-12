/**
 * Page-specific JS for the article details page
 * v1.0.1 -- 2020-01-09
 */

(function($) {
  "use strict";

  const stickyHeader = $("#sticky-header");
  const articleHeader = $("#article-header");
  let stickyHeaderAnimateTimeout;
  const stickyHeaderAnimationTime = 200;

  $(function() {
    /** Start tooltips on the page */
    $('[data-toggle="tooltip"]').tooltip();

    /**
     * "coin" logic borrowed from: https://stackoverflow.com/a/39495483/2488147
     * Basically, running .animate on every scroll event is very intensive on the client.
     * Instead, we check the coin value to see if the animation has already been applied,
     * preventing the animation from running again when not needed.
     */
    let coin = false;
    $(window).on("scroll", function() {
      const topValue = parseInt(stickyHeader.css("top").match(/\d+/), 10);
      const currOffset = stickyHeader.offset().top - $(window).scrollTop();

      if (currOffset <= topValue && coin === false) {
        stickyHeaderOn();
        coin = true;
      } else if (coin === true && currOffset > topValue) {
        stickyHeaderOff();
        coin = false;
      }
    });

    // Initial trigger for window scroll event, so it checks the offset on page load.
    // Uses a short timeout to attempt to trigger after the event has been added.
    setTimeout(function() {
      $(window).trigger("scroll");
    }, 50);

    /** To-top button trigger */
    $(".btn-to-top").on("click", function(e) {
      e.preventDefault();
      $(this).tooltip("hide");
      $('html,body').animate({scrollTop: 0}, 350);
    });
  });

  /** Turns ON the sticky-header, animating and adjusting nearby stuff as needed. */
  function stickyHeaderOn() {
    // Hide dropdowns open in the article details (which will be hidden off screen now)
    articleHeader.find(".dropdown-toggle").dropdown("hide");
    // Clear animation timeout for safety
    clearTimeout(stickyHeaderAnimateTimeout);
    // Make the header immediately visible
    stickyHeader.css({visibility: "visible"});
    // Animate its opacity to bring it to foreground.
    stickyHeader.animate({opacity: 1}, stickyHeaderAnimationTime);
  }

  /** Turns OFF the sticky-header, animating and adjusting nearby stuff as needed. */
  function stickyHeaderOff() {
    // Hide dropdowns open in the sticky header (which will be hidden)
    stickyHeader.find(".dropdown-toggle").dropdown("hide");
    // Clear animation timeout for safety
    clearTimeout(stickyHeaderAnimateTimeout);
    // Animate stickyHeader's opacity to send to background.
    stickyHeader.animate({opacity: 0}, stickyHeaderAnimationTime);
    // Use a timeout
    stickyHeaderAnimateTimeout = setTimeout(function() {
      stickyHeader.css({visibility: "hidden"});
    }, stickyHeaderAnimationTime);
  }
})(jQuery);
