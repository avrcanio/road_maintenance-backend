(function (window) {
    function notifyOpenerOfUpdate(config, value) {
        if (!window.opener) {
            return;
        }
        const targetField = window.opener.document.getElementById(config.fieldId);
        if (targetField) {
            targetField.value = value;
            if (window.opener.django && window.opener.django.jQuery) {
                window.opener.django.jQuery(targetField).trigger('change');
            }
        }
        if (!config.moduleName || !window.opener[config.moduleName]) {
            return;
        }
        const widget = window.opener[config.moduleName];
        if (typeof widget.clearFeatures === 'function') {
            widget.clearFeatures();
        }
        if (value) {
            try {
                const format = new window.opener.ol.format.GeoJSON();
                const featureCollection = widget.featureOverlay.getSource();
                const features = format.readFeatures('{"type": "Feature", "geometry": ' + value + '}');
                const extent = window.opener.ol.extent.createEmpty();
                features.forEach(function (feature) {
                    featureCollection.addFeature(feature);
                    window.opener.ol.extent.extend(extent, feature.getGeometry().getExtent());
                });
                if (!window.opener.ol.extent.isEmpty(extent)) {
                    widget.map.getView().fit(extent, {minResolution: 1});
                }
                if (!widget.options.is_collection && typeof widget.disableDrawing === 'function') {
                    widget.disableDrawing();
                }
            } catch (error) {
                console.error('Greška pri sinkronizaciji geometrije u prozoru administratora.', error);
            }
        }
    }

    function initRoadSectionFullscreenMap(config) {
        if (!window.opener) {
            alert('Nije moguće pronaći izvorni prozor administracije.');
            return;
        }
        const storageField = document.getElementById(config.storageFieldId);
        if (!storageField) {
            return;
        }
        const sourceField = window.opener.document.getElementById(config.fieldId);
        if (sourceField) {
            storageField.value = sourceField.value || '';
        }

        const options = {
            geom_name: config.geomName,
            id: config.storageFieldId,
            map_id: config.mapId,
            map_srid: config.mapSrid,
            name: config.storageFieldName,
            default_lon: config.defaultLon,
            default_lat: config.defaultLat,
            default_zoom: config.defaultZoom
        };
        window.fullscreenRoadWidget = new MapWidget(options);

        const saveButton = document.getElementById('fullscreen-save');
        const cancelButton = document.getElementById('fullscreen-cancel');
        const enableDrawButton = document.getElementById('fullscreen-enable-draw');
        const clearButton = document.getElementById('fullscreen-clear');

        if (saveButton) {
            saveButton.addEventListener('click', function () {
                notifyOpenerOfUpdate(config, storageField.value);
                window.close();
            });
        }
        if (cancelButton) {
            cancelButton.addEventListener('click', function () {
                window.close();
            });
        }
        if (enableDrawButton) {
            enableDrawButton.addEventListener('click', function () {
                if (window.fullscreenRoadWidget && typeof window.fullscreenRoadWidget.enableDrawing === 'function') {
                    window.fullscreenRoadWidget.enableDrawing();
                }
            });
        }
        if (clearButton) {
            clearButton.addEventListener('click', function () {
                if (window.fullscreenRoadWidget && typeof window.fullscreenRoadWidget.clearFeatures === 'function') {
                    window.fullscreenRoadWidget.clearFeatures();
                    storageField.value = '';
                }
            });
        }
    }

    window.initRoadSectionFullscreenMap = initRoadSectionFullscreenMap;
})(window);
