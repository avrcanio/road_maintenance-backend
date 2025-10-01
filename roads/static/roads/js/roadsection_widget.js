(function () {
    function openFullscreen(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const container = button.closest('.roadsection-widget');
        if (!container) {
            return;
        }
        const fieldId = container.dataset.fieldId;
        const moduleName = container.dataset.module;
        const fullscreenUrl = container.dataset.fullscreenUrl;
        if (!fullscreenUrl || !fieldId) {
            return;
        }
        const params = new URLSearchParams({
            field_id: fieldId,
        });
        if (moduleName) {
            params.set('module', moduleName);
        }
        const url = `${fullscreenUrl}?${params.toString()}`;
        const featuresWindow = window.open(
            url,
            `${fieldId}_map_editor`,
            'width=1280,height=900,resizable=yes,status=no,toolbar=no,menubar=no'
        );
        if (featuresWindow) {
            featuresWindow.focus();
        }
    }

    function init() {
        const buttons = document.querySelectorAll('.roadsection-open-fullscreen');
        buttons.forEach((button) => {
            button.addEventListener('click', openFullscreen);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
