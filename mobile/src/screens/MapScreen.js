import React from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';
import { WebView } from 'react-native-webview';

export function MapScreen() {
  // Free OpenStreetMap Webview centered on Pondicherry
  const mapHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
          body, html, #map { margin: 0; padding: 0; height: 100%; width: 100%; }
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          var map = L.map('map').setView([11.9338, 79.8358], 13);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
          }).addTo(map);

          var points = [
            { name: "Promenade Beach", lat: 11.9338, lng: 79.8358 },
            { name: "Auroville Matrimandir", lat: 12.0068, lng: 79.8105 },
            { name: "Sri Aurobindo Ashram", lat: 11.9366, lng: 79.8347 },
            { name: "Cafe des Arts", lat: 11.9332, lng: 79.8339 },
            { name: "Surguru Pure Veg", lat: 11.9351, lng: 79.8310 },
            { name: "Paradise Beach", lat: 11.8727, lng: 79.8187 }
          ];

          points.forEach(function(p) {
            L.marker([p.lat, p.lng]).addTo(map).bindPopup("<b>" + p.name + "</b>");
          });
        </script>
      </body>
    </html>
  `;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Pondicherry Map</Text>
        <Text style={styles.subtitle}>OpenStreetMap Leaflet Pins</Text>
      </View>
      <WebView
        originWhitelist={['*']}
        source={{ html: mapHtml }}
        style={styles.map}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0f172a',
  },
  subtitle: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  map: {
    flex: 1,
  },
});
