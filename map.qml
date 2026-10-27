import QtQuick
import QtLocation
import QtPositioning

Item {
    width: 800
    height: 600

    Plugin {
        id: mapPlugin
        name: "osm"
        
        // Provide standard openstreetmap tiles directly to avoid watermarks
        PluginParameter { name: "osm.mapping.providersrepository.disabled"; value: true }
        PluginParameter { name: "osm.useragent"; value: "MyPySide6MapApp/1.0" }
        PluginParameter { name: "osm.mapping.custom.host"; value: "https://tile.openstreetmap.org/" }
    }

    Map {
        objectName: "Map"
        id: map
        anchors.fill: parent
        plugin: mapPlugin
        center: QtPositioning.coordinate(40.7128, -74.0060) // New York City
        zoomLevel: 14
    }
}
