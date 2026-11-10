# Geometry Operations

Geometry bugs rarely raise an exception. They produce empty intersections,
absurd areas, or features in the wrong place. Check geometry type, validity, and
CRS before doing the operation that matters.

## Purpose

Use this reference for QGIS 3 geometry construction, type checks, validity,
coordinate transforms, distance and area measurement, spatial indexes, and the
overlay operations plugins use most often.

## Construction

```python
from qgis.core import QgsGeometry, QgsPointXY

point = QgsGeometry.fromPointXY(QgsPointXY(2.35, 48.85))
line = QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(1, 1)])
ring = [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(1, 1)]
polygon = QgsGeometry.fromPolygonXY([ring])
```

QGIS 3 uses `fromPointXY()`, `fromPolylineXY()`, and `fromPolygonXY()`.
`fromPoint(QgsPoint)` is available since QGIS 3.34 for `QgsPoint` input,
including Z and M values; `fromPointXY(QgsPointXY)` remains the portable 2D
choice for plugins targeting older 3.x releases. QGIS closes polygon rings
automatically, so do not duplicate the first point as the last.

## Type checks

```python
from qgis.core import QgsWkbTypes

if geom.isNull() or geom.isEmpty():
    raise ValueError("Geometry is missing or empty")
is_polygon = geom.type() == QgsWkbTypes.PolygonGeometry
wkb_type = geom.wkbType()
is_multi = QgsWkbTypes.isMultiType(wkb_type)
label = QgsWkbTypes.displayString(wkb_type)
```

`isNull()` means no geometry object or coordinates; `isEmpty()` means the
geometry exists but contains nothing. Check both. Multi and single types are
different WKB types even when they represent the same shape.

## Validity

```python
from qgis.core import Qgis, QgsMessageLog

if not geom.isGeosValid():
    for problem in geom.validateGeometry():
        QgsMessageLog.logMessage(
            problem.what(), "Contour Helper", Qgis.Warning
        )
```

`isGeosValid()` is a fast gate; `validateGeometry()` explains the failure.
Invalid rings can make `intersection()`, `difference()`, and `buffer()` return
empty or partial results. Verify the `ValidationResult` members against the
target 3.x patch if you format the details in user-facing output.

## CRS transforms

```python
from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsGeometry, QgsProject,
)

source_crs = layer.crs()
target_crs = QgsCoordinateReferenceSystem("EPSG:3857")
if not source_crs.isValid() or not target_crs.isValid():
    raise ValueError("Invalid CRS")
transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
transformed = QgsGeometry(feature.geometry())
transformed.transform(transform)
```

`transform()` mutates the geometry in place. Copy first when the original is
still needed. Pass the project to `QgsCoordinateTransform` so datum shifts use
the project's transform context. Create the transform once per layer, not once
per feature.

## Distance and area units

```python
from qgis.core import QgsDistanceArea, QgsProject, QgsUnitTypes

measure = QgsDistanceArea()
measure.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
measure.setEllipsoid("WGS84")
length_km = measure.convertLengthMeasurement(
    measure.measureLength(line), QgsUnitTypes.DistanceKilometers
)
area_km2 = measure.convertAreaMeasurement(
    measure.measureArea(polygon), QgsUnitTypes.AreaSquareKilometers
)
```

`QgsGeometry.length()` and `QgsGeometry.area()` are planar and return values in
the layer CRS units. In EPSG:4326 those units are degrees, which are not usable
lengths or areas. Use `QgsDistanceArea` with an ellipsoid for metric output, or
transform to a suitable projected CRS first.

## Spatial index

```python
from qgis.core import QgsPointXY, QgsSpatialIndex

index = QgsSpatialIndex(layer.getFeatures())
candidate_ids = index.intersects(area.boundingBox())
for feature_id in candidate_ids:
    feature = layer.getFeature(feature_id)
    if not feature.isValid():
        continue
    if feature.geometry().intersects(area):
        pass
nearest_ids = index.nearestNeighbor(QgsPointXY(0, 0), 3)
```

A spatial index narrows the candidate set; it does not replace the exact
predicate. Rebuild the index after bulk edits, or call `addFeature()` and
`deleteFeature()` for each change. An index over stale feature IDs returns
features that no longer match or are already deleted.

## Overlay and buffers

```python
from qgis.core import QgsGeometry

buffered = area.buffer(100.0, 8)
if buffered.isNull() or buffered.isEmpty():
    raise ValueError("Buffer produced no geometry")
if area.intersects(other):
    clipped = area.intersection(other)
    if clipped.isNull() or clipped.isEmpty():
        clipped = QgsGeometry()
```

Buffer distance is in the layer CRS units. For a layer in EPSG:4326, `100.0`
means 100 degrees, not 100 meters. Overlay operations return a new geometry;
check the result rather than assuming a non-null input guarantees a non-empty
output.

## Version notes

- `QgsDistanceArea.setSourceCrs(crs, transformContext)` is the QGIS 3 signature;
  the QGIS 2 single-argument form is not valid here.
- `QgsDistanceArea.setEllipsoid()` is the QGIS 3 way to enable ellipsoidal
  measurement. The QGIS 2 `setEllipsoidalMode()` method is not available.
- Newer 3.x releases add geometry repair helpers. Do not use them when the
  plugin claims `qgisMinimumVersion=3.16`.
- If a binding rejects an iterator in `QgsSpatialIndex`, build an empty index
  and call `addFeature()` in a loop.

## Pitfalls

- Treating `None`, null geometry, and empty geometry as the same condition.
- Running overlay operations on invalid polygons and accepting an empty result.
- Forgetting that `transform()` mutates the geometry.
- Mixing layers with different CRSs without transforming one of them.
- Buffering or measuring in degrees.
- Using a stale spatial index after editing features.
- Comparing a multi type to a single type and concluding the geometry is wrong.
- Using planar `area()` or `length()` for a geographic CRS.
- Duplicating the first point as the last; QGIS closes polygon rings automatically.
- Assuming `fromPoint(QgsPoint)` exists before QGIS 3.34; use `fromPointXY()` for
  older 3.x targets.

## Sources

- QGIS 3.40 PyQGIS cookbook, geometry handling:
  https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/geometry.html
- QGIS 3.44 API, `QgsGeometry`:
  https://qgis.org/pyqgis/3.44/core/QgsGeometry.html

Related: `pyqgis-core.md`, `processing-algorithms.md`.
