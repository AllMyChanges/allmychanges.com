var init = function () {
    $(document).ready(function(){
        // делаем табло со списком версий прилипающим кверху при прокрутке
        var container = $(".version-links-container");
        var parent = container.parent();
        var duplicate = container.clone();
        duplicate.addClass('version-links-container__hidden');
        duplicate.appendTo(parent);
        
        $(".version-links-container__hidden").sticky({
            topSpacing:0,
            className: "version-links-container__sticky",
            wrapperClassName: "version-links-container__wrapper"
        });

        // обрабатываем клик, чтобы при прокрутке не загораживать
        // кусок changelog с выбранной версией
        var version_links_height = $('.version-links').height();

        $('.version-links__item a').click(function (ev) {
            ev.preventDefault();
            // item was clicked @sticky
            var clicked_version = $(this).text().split(' ')[0];
            // searching version description in release notes
            var section_top = $('[name="' + clicked_version + '"]').position().top;

            // scrolling down
            var top = section_top - (version_links_height + 20);
            window.scroll(0, top);

            // removing highlight from all versions
            // we are doing this via timer to run this code after
            // callback from 'waypoint' plugin will be called
            
            var highlight_right_version = () => {
                // highlighting right version @sticky
                $(".version-links__item").removeClass("version-links__selected-item");
                // and put it to the clicked one
                var version_with_dashes = clicked_version.replace(/\./g, "-");
                var list_item = $(".version-links__item-" + version_with_dashes);
                list_item.addClass("version-links__selected-item");
            }
            setTimeout(highlight_right_version, 100);
            
        });
        
        // используем плагин, чтобы помечать ссылку с текущей версией
        $(".package-version__number a").waypoint({
            handler: function (direction) {
                // waypoint handler was called @sticky
                // remove highlight from all versions
                $(".version-links__item").removeClass("version-links__selected-item");
                // and put it to the one which user scrolled to
                var version = this.element.text;
                var version_with_dashes = version.replace(/\./g, "-");
                var current_version = $(".version-links__item-" + version_with_dashes);
                current_version.addClass("version-links__selected-item");
            },
            offset: "30%"
        });

        intro.push(
            {
                'element': $(".page-header__buttons")[0],
                'intro': 'Use these buttons to follow new packages or report about issues.'
            },
            1000
        );
    });
};

module.exports = init;
