var init = function () {
    $(document).ready(function(){
      // делаем табло со списком версий прилипающим кверху при прокрутке
      $(".version-links-container").sticky({
        topSpacing:0,
        className: "version-links-container__sticky",
        wrapperClassName: "version-links-container__wrapper"
      });

      // обрабатываем клик, чтобы при прокрутке не загораживать
      // кусок changelog с выбранной версией
      var version_links_height = $('.version-links').height();

      $('.version-links__item a').click(function (ev) {
        ev.preventDefault();
        var version = $(this).text();
        var section_top = $('[name="' + version + '"]').position().top;

        var top = section_top - (version_links_height + 20);
        if ($('.version-links__sticky').length == 0) {
          // это нужно потому, что когда заголовок становится липким, то его содержимое
          // вычитается из высоты страницы, сдвигая все заголовки вверх
          top -= version_links_height + 20;
        }
        window.scroll(0, top);
      });
    
      // используем плагин, чтобы помечать ссылку с текущей версией
      $(".package-version__number a").waypoint({
        handler: function (direction) {
          $(".version-links__item").removeClass("version-links__selected-item");
          $(".version-links__item-" + this.element.text.replace(/\./g, "-")).addClass("version-links__selected-item");
        },
        offset: "30%"
      });

      intro.push({'element': $(".page-header__buttons")[0],
                  'intro': 'Use these buttons to follow new packages or report about issues.'
                 }, 1000);
    });
};

module.exports = init;
